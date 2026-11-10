# Multi-Agent Design

One framework, three merged pieces: AIPentester's CLI + MCP server (the
tool layer), the pentest-framework Claude Code scaffold (the specialist
agents), and the ai-pentest-framework Python Phase 1 store/scope/redaction
(the state engine). This document is the architecture. `CLAUDE.md` is the
operating rules agents must follow; this file explains why the rules are
what they are.

## Origins

- **Tool layer — AIPentester (this repo, fixed copy of
  [nayangoel/AIPentester](https://github.com/nayangoel/AIPentester)).**
  Python CLI (`aipentester`) + stdio MCP server (`run_mcp_server.py`).
  17 real MCP tools, 2 resources. See `FIXES.md` for what was broken and
  fixed.
- **Agents — pentest-framework scaffold.** 10 Claude Code subagents
  (orchestrator, recon, injection, authentication, access-control,
  business-logic, api-security, ssrf, validation, reporting) + 2 skills.
  Adapted here into `.claude/agents/` and `.claude/skills/`: the
  Windows/PowerShell-only bits removed, `config/scope.yaml` replaced by
  `engagement_manifest.yaml`, and every Burp MCP tool claim rewritten to
  match the real 17-tool inventory.
- **State engine — ai-pentest-framework Phase 1.** The SQLite finding
  state machine (confirmation requires evidence), the default-deny scope
  predicate idea, and field-name secret redaction — re-implemented
  compactly in `src/aipentester/state/` against this repo's own
  `ScopeValidator` and `SecretsManager`, not vendored wholesale.

## Roles and model tiers

| Role | Model | What it does |
| --- | --- | --- |
| Orchestrator (main conversation) | Sonnet | Plans, assigns, merges, decides. No testing. |
| `pentest-orchestrator` agent | Sonnet | Independent plan/scope review. No testing. |
| Specialists: recon, injection, xss, authentication, access-control, business-logic, api-security, ssrf | Sonnet (recon: Haiku) | One capability each, narrow brief, own context. |
| `xss-agent` | Sonnet | Dedicated XSS session — the capability the user asked to isolate. |
| `scripter` | Haiku | PoCs, parsers, helper scripts. Cheap, fast, boilerplate. |
| `validation-agent` | Sonnet | Re-tests every claimed finding with fresh evidence. Only agent that confirms. |
| `scribe` | Haiku | Owns `state/STATE.md`. Tests nothing, writes nothing else. |
| `reporting-agent` | Sonnet | Reports from *confirmed* findings only. |

Why the tiers: security reasoning (is this a real vulnerability, what is
the impact) needs the stronger model. Writing a PoC harness, normalizing
an endpoint list, or consolidating a status file does not — Haiku is
faster and cheaper there. The one rule that keeps the cheap tier safe: a
Haiku-written PoC is a *claim* until it runs and `validation-agent`
confirms it. Plausible-looking code is not evidence.

## The three state layers

Memory lives in files, not in any session. A session can die, be
compacted, or be replaced; the files remain.

1. **Append-only journal — `state/journal.jsonl`.** Every agent appends
   events as they happen (`Journal.append`, one line per event, fsync).
   Append-only means concurrent writers cannot corrupt each other, and a
   crashed session leaves a complete record up to its last event. All
   detail is redacted on write (`SecretsManager`). A PostToolUse hook
   (`.claude/hooks/journal-append.py`) appends one line per MCP tool call
   automatically, so logging does not depend on an agent remembering to log.
2. **Findings store — `state/engagement.db` (SQLite, WAL).**
   `FindingsStore` enforces the state machine in code:
   `candidate → needs_validation → confirmed` (confirmation requires
   attached evidence), plus `rejected` / `inconclusive`. Workers record
   candidates via `aipentester findings add`; only the validator moves a
   finding forward. Scope is enforced at write time: the store takes the
   engagement's `ScopeValidator` and refuses out-of-scope URLs.
3. **Resume file — `state/STATE.md`, scribe-owned.** Short (aim under 200
   lines): engagement, status summary, Done / In flight / Blocked / Next,
   findings by status. Details live in the inbox files, the journal, and
   the store; `STATE.md` is the index, not the archive. Only the scribe
   edits it, so two writers can never fight over it.

Supporting pieces: `state/tasks/` (one claim file per task) and
`state/inbox/` (one full result file per completed task).

## Task claiming

Before a specialist starts work it claims the task
(`aipentester.state.Claims`): the claim id is a hash of
endpoint + method + parameter + test class, so the same input can never be
assigned twice, even across separate Claude Code sessions that share only
the filesystem. Claims are files created atomically (`O_EXCL`); a stale
claim (holder silent longer than its TTL, default 1 hour — e.g. its
session crashed) may be taken over, and the takeover is recorded. Only
the owner may release a claim.

## Resume procedure

After a crash, a fresh session runs:

```bash
aipentester status        # findings, claims, journal count, STATE.md
```

then reads `state/STATE.md` plus the journal tail (last 20 events), and
continues from the `Next` section. The scribe rebuilds `STATE.md` from the
store + journal (`statefile.rebuild`) whenever they disagree with what a
session remembers. The Stop hook reminds every session to leave resumable
state behind before ending.

## Scope enforcement

One scope authority: `aipentester.safety.ScopeValidator`, built from
`engagement_manifest.yaml`. It is checked in three places:

1. Before work: `aipentester validate-scope` (orchestrator + every agent).
2. Before every active request: each agent validates the exact URL against
   the manifest (the MCP server does the same per tool call).
3. At write time: the findings store refuses out-of-scope URLs.

The ai-pentest-framework scope predicate (scheme/port/subdomain aware)
was *not* ported as a second system — AIPentester's `ScopeValidator`
already covers host patterns and excluded paths, and two competing scope
systems would disagree. If finer scope semantics are ever needed, they
belong inside `ScopeValidator`, not beside it.

## Cost and context notes

- Each subagent has its own context window: an XSS agent that has only
  ever thought about XSS is sharper than one agent juggling everything.
  That is the main win.
- The cost is re-reads: every agent reads the manifest, `STATE.md`, and
  the journal tail on start. Keep `STATE.md` short and the journal tail
  small (last 20 events) or the re-reads eat the saving.
- Parallel agents hitting one target look like an aggressive scan to a
  WAF. Stagger them, keep the manifest's rate limits, and never let two
  agents test the same input (task claiming).
- Start with subagents inside one Claude Code session (shared workspace,
  parent coordinates). Separate terminal sessions are the second option —
  true isolation, but coordination is files-only, so claiming is mandatory
  there, not optional.

## Burp, honestly

In MCP mode, Burp's role is that browser traffic routes through the Burp
proxy (127.0.0.1:8080) for capture. There are NO `burp_*` MCP tools:
Repeater, Intruder, and Collaborator calls do not exist over MCP, and no
agent prompt in this repo instructs Claude Code to call them. High-impact
Burp operations (Intruder/Scanner runs) need a human in the Burp UI, or
the separate official Burp MCP server alongside — they are not part of
this framework's tool layer, and the pentest-framework Phase 3.1 Burp
permission policy was deliberately NOT ported (it governs tools that do
not exist here). The `BurpMCPClient` in `src/aipentester/burp/` targets
an undocumented Burp HTTP API and is untested against the real Burp MCP
server.

## What was deliberately NOT ported

- **pentest-framework's Burp MCP hooks + Phase 3.1 policy** (PowerShell
  `burp-mcp-pretool.ps1` / `burp-mcp-posttool.ps1`, `BurpMcpPolicy.psm1`).
  Windows-only, and they enforce a tool inventory (Repeater/Intruder via
  MCP) that does not exist in this framework. Replaced by the scope
  validator, the findings-store write gate, and the journal hook.
- **pentest-framework's `database/schema.sql` as a whole.** Its endpoint /
  parameter / external-component / approval tables belong to the grey-box
  scaffold's tracker, not to this framework. Only the finding state
  machine idea was carried over, re-implemented in `state/store.py`.
  Endpoint inventory stays in the recon agent's inbox results, not in a
  second database.
- **ai-pentest-framework's traffic pipeline** (parse/redact/normalise/
  dedup, Burp adapter, local vuln-app fixture). It is a Phase 2+ ingestion
  path that needs a live Burp instance; wiring it now would add an
  untested integration. If traffic import is wanted later, it lands as a
  new `aipentester import-traffic` command against this store — not as a
  vendored copy.
- **ai-pentest-framework's `config.py` / engagement YAML format.** This
  repo already has `EngagementManifest`; a second config format would
  split scope authority. One manifest, one validator.
- **The `pentest-orchestrator` agent's "main conversation stays
  orchestrator" shape was kept**, not the upstream AIPentester
  `PentestAgent` chat loop — the chat agent is a single-session tool, and
  the multi-agent design replaces it for engagements.

## Known limits

- The MCP server was verified with a real MCP client (17 tools, 2
  resources), not inside Claude Code itself, and the agents have not been
  run end-to-end against a live target — there is no live target in this
  environment. The first real engagement is the first real test.
- `SimplePentest` Burp-history attack generation is still a placeholder
  (returns no scenarios); `pentest_run_autonomous` therefore cannot mine
  Burp history yet.
- The journal hook only fires for `mcp__aipentester__*` tools and only
  when hooks are enabled in Claude Code; Bash/file edits by an agent are
  logged by the agent's own journal appends, not by the hook.
- `STATE.md` is per-engagement: cloning this repo does not carry any
  engagement's state. Each engagement runs `aipentester init` in its own
  project directory.
- Runtime state (`journal.jsonl`, `engagement.db`, `state/tasks/`,
  `state/inbox/`) is gitignored by design; `state/STATE.md` is the tracked
  resume file. If a repo is shared, the journal and DB do not travel with
  it — the resume file does.
