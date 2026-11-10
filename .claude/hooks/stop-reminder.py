#!/usr/bin/env python3
"""Stop hook: remind the session to leave resumable state behind.

Claude Code runs this when a session stops. Its stdout is shown to the
agent, so a short reminder is enough: consolidate the journal and findings
into STATE.md (via the scribe) before ending, so a fresh session can
resume from `state/STATE.md` plus the journal tail.

Best-effort: always exits 0, prints only this reminder, no I/O besides
stdout, no secrets.
"""

from __future__ import annotations

import sys

REMINDER = (
    "Checkpoint reminder: before ending, make sure the work is resumable: "
    "journal events are appended, candidate findings are recorded with "
    "`aipentester findings add`, and the scribe has refreshed "
    "state/STATE.md. A fresh session resumes from STATE.md + the journal tail."
)


def main() -> int:
    try:
        print(REMINDER, flush=True)
    except Exception:
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
