"""Tests for the multi-agent shared state package (journal, store, claims, STATE.md)."""

from pathlib import Path

import pytest

from aipentester.models.engagement import EngagementManifest
from aipentester.safety import ScopeValidator, ScopeViolationError
from aipentester.state import (
    ClaimConflict,
    Claims,
    FindingsStore,
    Journal,
    StateLayout,
    StoreError,
    parse,
    rebuild,
    render,
    resume_text,
    task_id_for,
    write_starter,
)

# -- journal ----------------------------------------------------------------


def test_journal_append_and_tail(tmp_path: Path) -> None:
    """Journal appends events in order; tail returns the last n."""
    journal = Journal(tmp_path / "journal.jsonl")
    journal.append("xss-agent", "task_started", {"endpoint": "/search"})
    journal.append("xss-agent", "candidate_found", {"title": "Reflected XSS"})
    assert journal.count() == 2
    tail = journal.tail(1)
    assert len(tail) == 1
    assert tail[0]["event"] == "candidate_found"
    assert tail[0]["agent"] == "xss-agent"
    assert "ts" in tail[0]


def test_journal_redacts_secrets_on_write(tmp_path: Path) -> None:
    """Passwords, tokens, and cookies never land in the journal file."""
    journal = Journal(tmp_path / "journal.jsonl")
    journal.append(
        "auth-agent",
        "login_attempt",
        {
            "username": "testuser",
            "password": "hunter2",
            "headers": {"Authorization": "Bearer abc123", "Cookie": "sid=xyz"},
            "token": "tok-123",
        },
    )
    raw = (tmp_path / "journal.jsonl").read_text()
    assert "hunter2" not in raw
    assert "abc123" not in raw
    assert "sid=xyz" not in raw
    assert "tok-123" not in raw
    assert "testuser" in raw  # non-sensitive values survive


def test_journal_skips_corrupt_lines(tmp_path: Path) -> None:
    """A half-written line (crash mid-write) is skipped, never fatal."""
    path = tmp_path / "journal.jsonl"
    path.write_text('{"agent": "a", "event": "ok"}\n{"agent": "b", "event": "hal\n')
    journal = Journal(path)
    events = journal.read_all()
    assert len(events) == 1
    assert events[0]["event"] == "ok"


# -- findings store -----------------------------------------------------------


def _store(tmp_path: Path) -> FindingsStore:
    return FindingsStore(tmp_path / "engagement.db")


def test_finding_starts_as_candidate(tmp_path: Path) -> None:
    """New findings are candidates, never confirmed on arrival."""
    store = _store(tmp_path)
    finding_id = store.add_finding("Reflected XSS", severity="High", category="xss")
    row = store.get_finding(finding_id)
    assert row is not None
    assert row["status"] == "candidate"
    assert store.counts_by_status()["candidate"] == 1


def test_finding_state_machine(tmp_path: Path) -> None:
    """candidate -> needs_validation -> confirmed; confirmed is terminal."""
    store = _store(tmp_path)
    finding_id = store.add_finding("Stored XSS", category="xss")
    with pytest.raises(StoreError):
        # Cannot jump straight to confirmed.
        store.transition_finding(finding_id, "confirmed")
    store.transition_finding(finding_id, "needs_validation")
    with pytest.raises(StoreError):
        # Confirmation requires attached evidence.
        store.transition_finding(finding_id, "confirmed")
    store.attach_evidence(finding_id, {"ref": "evidence/shot-0001.png"})
    store.transition_finding(finding_id, "confirmed")
    assert store.get_finding(finding_id)["status"] == "confirmed"
    with pytest.raises(StoreError):
        store.transition_finding(finding_id, "rejected")


def test_finding_illegal_transition_rejected(tmp_path: Path) -> None:
    """Unknown statuses and unknown findings raise StoreError."""
    store = _store(tmp_path)
    finding_id = store.add_finding("Something?", category="xss")
    with pytest.raises(StoreError):
        store.transition_finding(finding_id, "bogus-status")
    with pytest.raises(StoreError):
        store.transition_finding(9999, "rejected")
    with pytest.raises(StoreError):
        store.add_finding("Bad severity", severity="Critical-ish")


def test_finding_scope_refused_at_write_time(
    sample_manifest: EngagementManifest, tmp_path: Path
) -> None:
    """An out-of-scope URL is refused when recording the finding."""
    validator = ScopeValidator(sample_manifest)
    store = _store(tmp_path)
    ok_id = store.add_finding(
        "In-scope XSS",
        category="xss",
        endpoint_url="https://example.com/search?q=x",
        scope_validator=validator,
    )
    assert store.get_finding(ok_id) is not None
    with pytest.raises(ScopeViolationError):
        store.add_finding(
            "Out-of-scope XSS",
            category="xss",
            endpoint_url="https://evil.example/search?q=x",
            scope_validator=validator,
        )
    # Without a validator there is nothing to check (URL-less finding).
    store.add_finding("Process note", category="xss")


# -- task claiming -----------------------------------------------------------


def test_claim_id_is_stable(tmp_path: Path) -> None:
    """Same endpoint/method/parameter/class always maps to the same claim id."""
    assert task_id_for("/search", "GET", "q", "xss") == task_id_for(
        "/search", "GET", "q", "xss"
    )
    assert task_id_for("/search", "GET", "q", "xss") != task_id_for(
        "/search", "GET", "q", "sqli"
    )


def test_claim_conflict_release_and_reclaim(tmp_path: Path) -> None:
    """A live claim blocks others; release frees it for reclaim."""
    claims = Claims(tmp_path / "tasks")
    task_id = task_id_for("/search", "GET", "q", "xss")
    claims.claim(task_id, "xss-agent")
    with pytest.raises(ClaimConflict):
        claims.claim(task_id, "injection-agent")
    with pytest.raises(ClaimConflict):
        claims.release(task_id, "injection-agent")
    assert claims.release(task_id, "xss-agent") is True
    assert claims.release(task_id, "xss-agent") is False  # already gone
    claims.claim(task_id, "injection-agent")  # reclaim works
    assert [c.agent for c in claims.list_claims()] == ["injection-agent"]


def test_stale_claim_can_be_taken_over(tmp_path: Path) -> None:
    """A claim whose holder went silent past its TTL is takeable."""
    claims = Claims(tmp_path / "tasks")
    task_id = task_id_for("/login", "POST", "username", "auth")
    claims.claim(task_id, "auth-agent", ttl_seconds=0)
    # ttl 0: the claim is stale the moment it exists.
    taken = claims.claim(task_id, "validation-agent")
    assert taken.agent == "validation-agent"


# -- STATE.md ------------------------------------------------------------------


def test_state_md_round_trip(tmp_path: Path) -> None:
    """render -> parse preserves the scribe's sections."""
    data = {
        "engagement": {"name": "Test Engagement", "id": "TEST-1"},
        "updated": "2026-11-11T00:00:00+00:00",
        "summary": {
            "findings": {"candidate": 2, "confirmed": 1},
            "open_claims": 1,
            "journal_events": 5,
        },
        "done": ["recon finished on example.com"],
        "in_flight": ["xss-agent: task-abc123"],
        "blocked": ["Burp proxy down"],
        "next": ["validate finding #1"],
        "findings": ["candidate: 2", "confirmed: 1"],
    }
    text = render(data)
    parsed = parse(text)
    assert parsed["Done"] == ["recon finished on example.com"]
    assert parsed["Blocked"] == ["Burp proxy down"]
    assert parsed["Next"] == ["validate finding #1"]
    assert "candidate: 2" in parsed["Findings"]


def test_rebuild_keeps_scribe_notes(tmp_path: Path) -> None:
    """Rebuild refreshes counts but does not discard scribe notes."""
    layout = StateLayout(tmp_path)
    layout.ensure()
    write_starter(layout, name="Test Engagement", engagement_id="TEST-1")
    # Add a finding and a journal event, then hand-edit a Blocked note.
    store = FindingsStore(layout.db_path)
    try:
        store.add_finding("Reflected XSS", category="xss")
    finally:
        store.close()
    Journal(layout.journal_path).append("xss-agent", "candidate_found")
    # The starter has "(nothing yet)" under Blocked; put a scribe note there.
    state_md = layout.state_md_path.read_text()
    state_md = state_md.replace(
        "## Blocked\n\n- (nothing yet)", "## Blocked\n\n- Burp is down"
    )
    layout.state_md_path.write_text(state_md)

    draft = rebuild(layout, "Test Engagement", "TEST-1")
    parsed = parse(draft)
    assert "Burp is down" in parsed["Blocked"]
    assert "candidate: 1" in parsed["Findings"]
    assert "- Journal events: 1" in draft


def test_resume_text_includes_live_state(tmp_path: Path) -> None:
    """resume_text gives a fresh session STATE.md + live counters."""
    layout = StateLayout(tmp_path)
    layout.ensure()
    write_starter(layout, name="Test Engagement", engagement_id="TEST-1")
    store = FindingsStore(layout.db_path)
    try:
        store.add_finding("Reflected XSS", category="xss")
    finally:
        store.close()
    Journal(layout.journal_path).append("xss-agent", "candidate_found")
    text = resume_text(layout)
    assert "Test Engagement" in text
    assert "candidate" in text
    assert "Journal events: 1" in text


def test_layout_ensure_and_starter(tmp_path: Path) -> None:
    """ensure() creates the dirs; write_starter is idempotent."""
    layout = StateLayout(tmp_path)
    assert not layout.state_dir.exists()
    layout.ensure()
    assert layout.tasks_dir.exists()
    assert layout.inbox_dir.exists()
    path = write_starter(layout, name="Test Engagement", engagement_id="TEST-1")
    assert path.exists()
    first = path.read_text()
    write_starter(layout, name="Other", engagement_id="OTHER")
    assert path.read_text() == first  # never overwrites an existing file
