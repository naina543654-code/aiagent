#!/usr/bin/env python3
"""PostToolUse hook: append one redacted journal line per MCP tool call.

Claude Code runs this after every tool call matching ``mcp__aipentester__*``
and passes the hook payload as JSON on stdin. The script extracts the tool
name and a short, redacted summary of its input and appends one line to
``state/journal.jsonl`` under the project directory.

Best-effort by design: it never fails the session (always exits 0), never
prints secrets (it prints nothing on success), never makes network calls,
and uses only the standard library. The redaction here is intentionally
small and local — the full redaction system lives in
``aipentester.safety.SecretsManager``; this script must work even when the
package is not importable, so it duplicates only the few regexes it needs.
"""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

# Field-name fragments whose values are never written to the journal.
_SENSITIVE_SUBSTRINGS = (
    "password", "passwd", "pwd", "secret", "token", "api_key", "apikey",
    "auth", "session", "cookie", "otp", "ssn", "credit_card", "card_number",
)

_VALUE_PATTERNS = (
    re.compile(r"(?i)(password|api[_-]?key|token|secret)\s*[:=]\s*\S+"),
    re.compile(r"(?i)authorization:\s*bearer\s+\S+"),
    re.compile(r"(?i)cookie:\s*[^\r\n]+"),
)


def _redact_text(text: str) -> str:
    for pattern in _VALUE_PATTERNS:
        text = pattern.sub("[REDACTED]", text)
    return text


def _redact_value(value: object) -> object:
    if isinstance(value, dict):
        return {
            key: ("[REDACTED]" if any(s in key.lower() for s in _SENSITIVE_SUBSTRINGS)
                  else _redact_value(val))
            for key, val in value.items()
        }
    if isinstance(value, list):
        return [_redact_value(item) for item in value]
    if isinstance(value, str):
        return _redact_text(value)
    return value


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except Exception:
        return 0  # No usable payload: nothing to log, never fail the session.
    try:
        project_dir = Path(
            os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()
        )
        tool_name = str(payload.get("tool_name", "unknown"))
        tool_input = payload.get("tool_input") or {}
        summary = json.dumps(_redact_value(tool_input), ensure_ascii=False)
        if len(summary) > 500:
            summary = summary[:500] + "…[truncated]"
        record = {
            "agent": "hook",
            "kind": "tool_use",
            "event": tool_name,
            "detail": {"tool_input_summary": summary},
        }
        # Timestamp is added by the journal; the hook keeps its own line
        # minimal and never re-implements the journal's schema.
        from datetime import UTC, datetime

        record["ts"] = datetime.now(UTC).isoformat()
        state_dir = project_dir / "state"
        state_dir.mkdir(parents=True, exist_ok=True)
        journal = state_dir / "journal.jsonl"
        with open(journal, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
            f.flush()
            os.fsync(f.fileno())
    except Exception:
        return 0  # Best-effort: a logging failure must never break the session.
    return 0


if __name__ == "__main__":
    sys.exit(main())
