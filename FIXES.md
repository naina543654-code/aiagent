# FIXES.md — What was broken and what was fixed

This is a fixed copy of upstream [nayangoel/AIPentester](https://github.com/nayangoel/AIPentester)
(main, commit `c08e65e`, snapshot 2026-04-28). The upstream snapshot did **not** work
as shipped: `pip install` succeeded but the MCP server crashed on import, two
documented CLI commands did not exist, and the test suite failed. Every item
below was reproduced verbatim first, then fixed, then re-verified (see
"Verification evidence" at the end).

## Bugs found and fixed

### 1. MCP server crashed on import — mcp 2.x removed the decorator API (CRITICAL)
- **Symptom:** `python run_mcp_server.py` exited immediately:
  ```
  Import failed: 'Server' object has no attribute 'list_resources'
  AttributeError: 'Server' object has no attribute 'list_resources'
  ```
  Any import of `aipentester.mcp_server` failed, so the whole MCP mode (the
  project's main feature) was dead.
- **Cause:** `src/aipentester/mcp_server.py` used the old mcp SDK decorator API
  (`@app.list_tools()`, `@app.call_tool()`, `@app.list_resources()`,
  `@app.read_resource()`) and `Tool(..., inputSchema=...)` /
  `Resource(..., mimeType=...)` kwargs. `pip install` resolves `mcp>=0.9.0` to
  mcp **2.3.0**, whose low-level `Server` has no decorator methods at all —
  handlers are constructor callbacks (`on_list_tools=`, `on_call_tool=`,
  `on_list_resources=`, `on_read_resource=`) returning typed results
  (`ListToolsResult`, `CallToolResult`, `ListResourcesResult`,
  `ReadResourceResult`), and type fields are snake_case
  (`input_schema`, `mime_type`).
- **Fix:** Rewrote the handler registration layer of `mcp_server.py` to the
  mcp 2.x API. The tool definitions and all tool *implementation* logic are
  unchanged; they are now a module-level `TOOLS` list served by
  `handle_list_tools`, and `handle_call_tool` wraps the existing `call_tool`
  (which returns `[{type, text}]` dicts) into a `CallToolResult` of
  `TextContent`. Resources are served by `handle_list_resources` /
  `handle_read_resource` returning typed results. Pinned the dependency in
  `pyproject.toml`: `mcp>=2.0,<3` (was `mcp>=0.9.0`).

### 2. `VisionCrawler` used but never imported in `mcp_server.py` (latent runtime crash)
- **Symptom:** The `pentest_interactive_explore_and_test` tool handler
  referenced `VisionCrawler` (line ~947), which was not imported → `NameError`
  if that tool was ever called.
- **Fix:** Added `VisionCrawler` to the `from .crawler import ...` line.
  (The tool is still not advertised in `list_tools()`, matching the README —
  only its crash was fixed.)

### 3. Browser re-created on every `pentest_*` tool call (precedence bug)
- **Symptom in code:** `if browser is None and name.startswith("browser_") or name.startswith("pentest_"):` 
  evaluates as `(A and B) or C`, so *every* `pentest_*` call constructed a new
  `BrowserUseAdapter` and re-initialized the browser, discarding session state.
- **Fix:** `if browser is None and (name.startswith("browser_") or name.startswith("pentest_")):` — initialize once, lazily.

### 4. `SimplePentest` imported a module that does not exist
- **Symptom (reproduced):**
  ```
  ModuleNotFoundError: No module named 'aipentester.mcp_burp'
  ```
  raised from `SimplePentest._generate_attacks_from_burp` (phase 4 of the
  `pentest` MCP tool), because it did `from .mcp_burp import get_proxy_http_history`.
  No `mcp_burp` module exists anywhere in the repo; the function
  `get_proxy_http_history` is defined as a placeholder at the bottom of
  `simple_pentest.py` itself.
- **Fix:** Removed the bogus import; the method now calls the module-level
  placeholder directly (returns `[]` — no Burp history client exists yet, so
  0 attack scenarios are generated from Burp traffic; the rest of the
  workflow is unaffected). Noted as a known limitation, not silently papered
  over.

### 5. `aipentester validate-scope` did not exist (documented everywhere)
- **Symptom:** `aipentester validate-scope` → `No such command 'validate-scope'` (exit 2).
  The command is referenced by `aipentester init`'s success panel, the
  Makefile (`run-validate`), `ARCHITECTURE.md`, `GETTING_STARTED.md`,
  `QUICK_REFERENCE.md`, `INDEX.md`, `PROJECT_SUMMARY.md`, `THREAT_MODEL.md`.
  The docs even claim `cli/commands/validate_scope.py` is "✅ Complete (120 lines)" —
  the file was absent from the snapshot.
- **Fix:** Implemented `src/aipentester/cli/commands/validate_scope.py` per the
  architecture doc (load manifest → run `ScopeValidator.pre_flight_check()`).
  It prints the engagement/scope summary and the four pre-flight checks
  (engagement active, authorization confirmed, scope hosts defined, approval
  gate enabled), exits 0 on pass and 1 on failure, and is registered as
  `validate-scope` in `cli/main.py`.

### 6. `aipentester plan` did not exist (documented in `init` output and architecture docs)
- **Symptom:** `aipentester plan` → `No such command 'plan'`.
- **Fix:** Implemented `src/aipentester/cli/commands/plan.py` as a small,
  safe, offline stub matching the documented interface (`plan --mode generic`
  / `--mode context`). It loads and validates the manifest, then writes a
  markdown assessment plan (`reports/assessment_plan.md` by default) covering
  scope, approved categories, context files (context mode), the six phases,
  and safety controls. It performs no scanning, crawling, or network access.
  The other aspirational commands from the architecture docs (`login`,
  `crawl`, `ingest-context`, `review-queue`, `report`, `burp-check`) were
  **not** invented — they remain unimplemented; see "Known limitations".

### 7. Test suite failed: fixture dates from 2024 are expired
- **Symptom (reproduced):** `1 failed, 27 passed` —
  ```
  FAILED tests/unit/test_models.py::TestEngagementInfo::test_valid_engagement_info
  assert info.is_active()
  AssertionError: assert False
  ```
  The fixture engagement ran 2024-01-01 → 2024-12-31, so `is_active()` is
  `False` on any date after 2024.
- **Fix:** `tests/conftest.py` and `test_models.py` now use dates relative to
  today (`today − 1 day` → `today + 365 days`). `test_is_expired` still uses
  fixed 2020 dates (correctly expired).

### 8. `datetime.utcnow()` deprecation (Python 3.12)
- `src/aipentester/safety/audit_log.py` used `datetime.utcnow()` (3 calls),
  deprecated in 3.12. Replaced with `datetime.now(timezone.utc)` — same
  values, no warning.

### 9. Makefile required `uv` and `pytest-watch`, neither installed nor declared
- **Symptom:** `make install` / `make dev-install` / `make build` /
  `make publish*` all invoked `uv ...`; `uv` is not installed in a plain
  Python environment and is not a project dependency. `make watch-test`
  invoked `pytest-watch`, which is not in dev dependencies.
- **Fix:** `install`/`dev-install` now use `python -m pip install -e .` /
  `".[dev]"`; `build` uses `python -m build` (installing `build` first);
  `publish*` use `twine`; the `pytest-watch` target was removed. The
  `run-validate` target now works because `validate-scope` exists.

### 10. Stray `-.json` file at repo root
- The file was a nikto scan result for `unsaidtalks.com` dated 2026-04-26
  (scan failed: "Unable to connect to unsaidtalks.com:80"). It is not source
  code and its name is an artifact of a nikto `-o` typo.
- **Fix:** Moved to `reports/nikto-unsaidtalks-2026-04-26.json` (via `git mv`).
  It is a leftover scan artifact, kept for reference, not a test target —
  no live scan of that host was performed by this work.

### 11. `mcp-proxy.jar` (13 MB) — kept, identified
- Identified (not executed): `META-INF/MANIFEST.MF` gives
  `Main-Class: net.portswigger.MainKt`; contents are
  `net/portswigger/*` classes (`SseClient`, `OAuth21Client`, …). This is
  PortSwigger's official **Burp MCP proxy** — the stdio↔SSE bridge that lets
  an MCP client talk to Burp Suite Pro's MCP server, with OAuth 2.1 client
  support. 7,821 files, ~30 MB uncompressed.
- **Decision: kept as-is.** It is legitimate upstream tooling and the
  alternative to the README's `npx -y @burp-suite-mcp/server` route
  (requires Java + Burp Suite Pro). Notes: it is 13 MB, so pre-commit's
  `check-added-large-files` hook will flag it; it is not referenced by any
  Python code or docs in this repo — see "Known limitations".

## Packaging check (not a bug)
- `pyproject.toml` `[tool.hatch.build.targets.wheel] packages = ["src/aipentester"]`
  is correct for the src layout with hatchling: `pip install -e .` built and
  installed the `aipentester` console script successfully (verified in two
  fresh venvs). No change needed.

## What was NOT changed
- No live pentest behaviour was added; no network calls to external targets.
- No secrets/keys were added. `.env.example` still contains only placeholders.
- The aspirational CLI commands `login`, `crawl`, `ingest-context`,
  `review-queue`, `report`, `burp-check` (architecture docs) remain
  unimplemented rather than stubbed — the docs that claim them are listed in
  "Known limitations" instead of being silently "completed".
- `ruff` still reports 52 remaining findings (mostly style: `SIM102`,
  `ARG001`, `B904`, `E722` bare-except, `E402`, `F841`, etc.). The 62 safe
  auto-fixes were applied (`ruff check --fix`); the rest do not affect
  running and were left alone. No `F821` (undefined name) findings remain.

## Known limitations (still require external tools / work)
- **Burp Suite Pro + Burp MCP server** (`npx -y @burp-suite-mcp/server`, or
  `java -jar mcp-proxy.jar`) are required for any Burp tool; `BurpMCPClient`
  targets an undocumented `http://host:port/api/*` + `/health` API that does
  not match the official Burp MCP server, so the interactive agent's Burp
  calls are untested against a real Burp.
- **Anthropic API key** required for `aipentester chat` / `aipentester pentest`
  (and the `VisionCrawler`); MCP mode needs none (uses the Claude subscription).
- **nmap / nikto** binaries required for recon tools (not installed here).
- **Playwright Chromium** (`playwright install chromium`) required for the
  browser adapter; headful browser (`headless=False`) needs a display.
- `SimplePentest` Burp-history attack generation is a placeholder returning
  no scenarios (see bug 4).
- `mcp-proxy.jar` is undocumented in the repo's setup docs; the README's
  Burp section only mentions the `npx` route.
- Docs that over-claim implementation status (`INDEX.md`, `PROJECT_SUMMARY.md`,
  `QUICK_REFERENCE.md` claim `validate_scope.py`/`storage/duckdb_adapter.py`
  and other modules are "✅ Complete"; `GETTING_STARTED.md` lists a
  `storage/` package and commands that do not exist) were not rewritten —
  only the README top note was added. Treat those docs as aspirational.

## Verification evidence

Environment: Python 3.12.3, fresh venv `.venv`, `pip install -e ".[dev]"`.
Installed versions: `mcp 2.3.0`, `browser-use 1.0.1`, `anthropic 2.8.0`,
`playwright 1.65.0`, `pydantic 2.14.3`, `typer 0.29.0`, `pytest 9.2.0`,
`ruff 0.17.4`.

Before fixes (reproduced verbatim):
- `python -m compileall src tests` — exit 0 (no syntax errors).
- `pytest` — **27 passed, 1 failed** (`test_valid_engagement_info`,
  `assert info.is_active()` → `assert False`).
- `aipentester --help` — exit 0 (commands: version, chat, init, pentest, recon).
- `aipentester version` — `AIPentester v0.1.0`, exit 0.
- `aipentester validate-scope` — `No such command 'validate-scope'`, exit 2.
- `aipentester plan` — `No such command 'plan'`.
- `aipentester init` in a temp dir — exit 0, created `evidence/ audit_trail/
  context/ reports/ runs/ engagement_manifest.yaml .env .gitignore`.
- `python run_mcp_server.py` — exit 1, `Import failed: 'Server' object has
  no attribute 'list_resources'`.
- `SimplePentest._generate_attacks_from_burp` — `ModuleNotFoundError: No module
  named 'aipentester.mcp_burp'`.

After fixes:
- `python -m compileall src tests` — exit 0.
- `pytest` — **33 passed, 0 failed** (5 new CLI tests in
  `tests/unit/test_cli.py`; 6.1s). Coverage 19% (unchanged scope — tests only
  cover models/safety/CLI, not the browser/Burp paths).
- `ruff check src/ tests/` — 114 findings before auto-fix → 62 safe fixes
  applied → **52 remaining** (style-only, none affects running).
- `aipentester --help` — lists version, chat, init, pentest,
  **validate-scope**, **plan**, recon. `aipentester version` — v0.1.0.
- `aipentester init` (fresh temp dir) — exit 0.
- `aipentester validate-scope` — exit 1 on the sample manifest (2024 dates,
  correctly "Engagement is not active"); exit 0 after updating the manifest
  dates to 2026-11-01 → 2026-12-31 ("✓ Scope validation passed.").
- `aipentester plan` — exit 0, wrote `reports/assessment_plan.md`
  (engagement, hosts, phases, safety); `plan --mode context` — exit 0;
  `plan --mode bogus` — exit 1 ("invalid mode").
- `python -m aipentester --help` — works, lists validate-scope and plan.
- MCP stdio smoke test (real `mcp` 2.3.0 client against
  `run_mcp_server.py`): `initialize` OK, `list_tools` → **17 tools**,
  `list_resources` → **2 resources**, `read_resource aipentester://scope`
  and `aipentester://manifest` OK, unknown tool call returns
  "Unknown tool: nonexistent_tool_xyz" gracefully; server exits cleanly.
- `SimplePentest._generate_attacks_from_burp` — returns `[]`, no exception.
- Fresh-venv reinstall (`.venv-fresh`, `pip install -e ".[dev]"`, Python
  3.12.3) — exit 0, resolved `mcp 2.3.0` under the new `mcp>=2.0,<3` pin,
  pytest **33 passed**, `aipentester --help` lists `validate-scope`,
  `aipentester.mcp_server` imports cleanly. (An earlier attempt placed the
  venv under `/tmp`, a 512 MB tmpfs, and failed with "No space left on
  device" — an environment limit, not a code issue; the retry on the main
  disk succeeded.)

## 11. CLAUDE_CODE_SETUP.md was stale (doc fix, 2026-11-11)

- It pointed at the old `~/.config/claude-code/config.json` path and the old
  `claude-code` binary, and listed `burp_get_proxy_history` /
  `burp_send_to_repeater` / `burp_send_to_intruder` / `burp_collaborator_*`
  as MCP tools. Those burp_* tools exist only in `agent.py` (the
  Anthropic-API `chat` agent), not in `mcp_server.py` — the MCP server
  exposes 17 tools (8 `browser_*`, 3 `pentest_*`, 4 `recon_*`,
  `pentest_skill_execute`, `pentest`) and 2 resources.
- Rewrote the guide around `claude mcp add --transport stdio` / `.mcp.json`,
  with the correct 17-tool list, the manifest-first requirement
  (`AIPENTESTER_MANIFEST` absolute path, valid dates), and the Burp caveat
  above. No code changed; pytest still 33 passed.
