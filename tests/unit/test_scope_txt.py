"""Tests for scope-only mode: a plain scope.txt instead of a full manifest."""

from datetime import date

import pytest

from aipentester.models.engagement import EngagementManifest, _parse_scope_txt


def test_parse_scope_txt_basic(tmp_path):
    p = tmp_path / "scope.txt"
    p.write_text("127.0.0.1\nexample.com\n", encoding="utf-8")
    assert _parse_scope_txt(p.read_text()) == ["127.0.0.1", "example.com"]


def test_parse_scope_txt_ignores_blanks_comments_and_urls():
    text = "# comment\n\n127.0.0.1\nhttp://example.com:8080/path\n*.example.com # trailing\n"
    assert _parse_scope_txt(text) == [
        "127.0.0.1",
        "example.com:8080",
        "*.example.com",
    ]


def test_parse_scope_txt_empty_raises():
    with pytest.raises(ValueError, match="no hosts"):
        _parse_scope_txt("# only a comment\n\n")


def test_from_scope_file_fills_defaults_and_is_active(tmp_path):
    p = tmp_path / "scope.txt"
    p.write_text("127.0.0.1\n", encoding="utf-8")
    m = EngagementManifest.from_scope_file(str(p))
    assert m.scope.hosts == ["127.0.0.1"]
    assert m.engagement.is_active()
    assert m.engagement.start_date == date.today()
    assert m.engagement.authorization_acknowledgement.strip()
    assert m.credentials.source.value == "interactive"
    m.validate_active()
    m.validate_authorization()


def test_from_file_accepts_txt_path(tmp_path):
    p = tmp_path / "scope.txt"
    p.write_text("127.0.0.1\n", encoding="utf-8")
    m = EngagementManifest.from_file(str(p))
    assert m.scope.hosts == ["127.0.0.1"]


def test_from_file_falls_back_to_scope_txt_when_manifest_missing(tmp_path):
    (tmp_path / "scope.txt").write_text("127.0.0.1\n", encoding="utf-8")
    m = EngagementManifest.from_file(str(tmp_path / "engagement_manifest.yaml"))
    assert m.scope.hosts == ["127.0.0.1"]


def test_from_file_missing_everything_raises(tmp_path):
    with pytest.raises(FileNotFoundError, match="scope.txt"):
        EngagementManifest.from_file(str(tmp_path / "engagement_manifest.yaml"))


def test_from_file_scope_only_yaml(tmp_path):
    p = tmp_path / "engagement_manifest.yaml"
    p.write_text("scope:\n  hosts:\n  - 127.0.0.1\n", encoding="utf-8")
    m = EngagementManifest.from_file(str(p))
    assert m.scope.hosts == ["127.0.0.1"]
    assert m.engagement.is_active()


def test_from_yaml_file_still_loads_full_manifest(tmp_path):
    # Backwards compat: the old full-manifest path must keep working.
    p = tmp_path / "engagement_manifest.yaml"
    p.write_text(
        "engagement:\n"
        "  name: Test\n"
        "  id: TEST-001\n"
        "  authorized_by: CISO\n"
        "  analyst_name: Analyst\n"
        "  analyst_email: a@test.com\n"
        "  start_date: '2026-01-01'\n"
        "  end_date: '2027-01-01'\n"
        "  authorization_acknowledgement: Confirmed\n"
        "scope:\n"
        "  hosts:\n"
        "  - example.com\n"
        "credentials:\n"
        "  source: interactive\n",
        encoding="utf-8",
    )
    m = EngagementManifest.from_yaml_file(str(p))
    assert m.scope.hosts == ["example.com"]
    assert m.engagement.name == "Test"
