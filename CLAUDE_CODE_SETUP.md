# Using AIPentester with Claude Code (Terminal)

## What This Is

Use AIPentester as an MCP server with **Claude Code** in your terminal. Chat with
Claude right in your terminal and it can perform pentests using the browser,
recon tools, and Burp proxy traffic.

**No Anthropic API key needed for MCP mode** — it uses your Claude subscription.
(The `aipentester chat` / `pentest` CLI commands are the ones that need an
Anthropic API key; MCP mode does not.)

This guide was corrected 2026-11-11: the upstream version pointed at the old
`~/.config/claude-code/config.json` path and the old `claude-code` binary, and
listed Burp tools that are not actually exposed over MCP. Both are fixed below.

## Prerequisites

```bash
git clone https://github.com/naina543654-code/AIPentester.git
cd AIPentester
python -m venv .venv
.venv/bin/pip install -e ".[dev]"
.venv/bin/playwright install chromium   # only needed for the browser_* tools
```

## 1. Initialize a project (required)

The MCP server refuses to run tools until it can load an engagement manifest,
so do this first, in the directory you will pentest from:

```bash
.venv/bin/aipentester init
```

Then edit the generated `engagement_manifest.yaml`:

- Put your **authorized** target in `scope.hosts` (nothing else will be tested —
  the server validates every URL against this list).
- Set `start_date` / `end_date` to dates that cover today — the sample manifest
  ships with expired dates and validation will fail until you fix them.
- Fill in `authorized_by` and the authorization acknowledgement truthfully.

Check it with:

```bash
.venv/bin/aipentester validate-scope
```

It should print `✓ Scope validation passed.` If it doesn't, fix the manifest
before continuing — Claude Code will hit the same error on every tool call.

## 2. Add the MCP server to Claude Code

Use absolute paths. Replace `/path/to/AIPentester` with your real clone path.

```bash
claude mcp add --transport stdio --scope project aipentester \
  --env AIPENTESTER_MANIFEST=/path/to/AIPentester/engagement_manifest.yaml \
  -- /path/to/AIPentester/.venv/bin/python /path/to/AIPentester/run_mcp_server.py
```

`--scope project` writes it to `.mcp.json` in the project so it is shared with
anyone who clones the repo. Use `--scope user` instead if you want it global
for just you, or `--scope local` for this project only.

Prefer a file instead of the CLI? Create `.mcp.json` in the project root:

```json
{
  "mcpServers": {
    "aipentester": {
      "type": "stdio",
      "command": "/path/to/AIPentester/.venv/bin/python",
      "args": ["/path/to/AIPentester/run_mcp_server.py"],
      "env": {
        "AIPENTESTER_MANIFEST": "/path/to/AIPentester/engagement_manifest.yaml",
        "BURP_PROXY_HOST": "127.0.0.1",
        "BURP_PROXY_PORT": "8080"
      }
    }
  }
}
```

### Verify it loaded

```bash
claude mcp list
```

Then start Claude Code (`claude`) and run `/mcp` inside the session — `aipentester`
should show as connected. Ask it:

```
What tools do you have access to?
```

It should list the AIPentester tools below.

## 3. Tools Claude Code actually gets

Verified against the fixed server (real MCP client handshake: 17 tools,
2 resources). These are the tools Claude Code can call:

**Browser (traffic goes through the Burp proxy):**
`browser_navigate`, `browser_login`, `browser_screenshot`,
`browser_get_page_text`, `browser_find_elements`, `browser_click_element`,
`browser_extract_links`, `browser_find_forms`

**Pentest:**
`pentest_crawl_application`, `pentest_analyze_threats`,
`pentest_run_autonomous`, `pentest`, `pentest_skill_execute`

**Recon (needs the binaries installed):**
`recon_nmap_quick_scan`, `recon_nmap_service_scan`, `recon_nmap_vuln_scan`,
`recon_nikto_scan`

**Resources:** `aipentester://manifest` (engagement manifest),
`aipentester://scope` (target scope).

### What you do NOT get over MCP

The upstream docs listed `burp_get_proxy_history`, `burp_send_to_repeater`,
`burp_send_to_intruder`, `burp_collaborator_generate`, and
`burp_collaborator_check` as MCP tools. **They are not MCP tools.** They exist
only in `src/aipentester/agent.py` — the Anthropic-API chat agent behind
`aipentester chat`. Claude Code cannot call them directly.

What Claude Code *does* get from Burp is indirect: browser traffic is routed
through the Burp proxy (default `127.0.0.1:8080`), so requests are captured
there for you to inspect manually. If you want Burp's own MCP server as well,
run it separately — it is a different server, not this one:

```bash
# Terminal 1: Burp Suite Professional running, proxy on 127.0.0.1:8080
npx -y @burp-suite-mcp/server
```

Note: this project's `BurpMCPClient` targets an undocumented Burp HTTP API and
has **not** been verified against the real Burp MCP server, so treat any
Burp-backed behaviour as untested until you confirm it yourself.

## 4. Start pentesting

```bash
claude
```

```
You: I need to test app.example.com for XSS vulnerabilities

Claude: Let me check the scope first...
[reads aipentester://scope]

app.example.com is in scope. Navigating there now...
[uses browser_navigate]
```

## Troubleshooting

### MCP server not loading

- Check `claude mcp list` and `/mcp` in the session for the error.
- Paths in the config must be **absolute**; use the `.venv/bin/python` from
  the install step, not the system python.
- Test the server manually — it should wait on stdin (that is correct
  behaviour for a stdio server; Ctrl-C to stop it):

```bash
/path/to/AIPentester/.venv/bin/python /path/to/AIPentester/run_mcp_server.py
```

It prints `AIPentester MCP server starting...` to stderr, then waits. If it
exits with an import error instead, your install is broken — reinstall with
`.venv/bin/pip install -e ".[dev]"`.

### "Engagement manifest not found" / scope validation errors

- The server reads `AIPENTESTER_MANIFEST` if set, otherwise
  `engagement_manifest.yaml` in the **current working directory** — and Claude
  Code starts the server with its own working directory, so always set
  `AIPENTESTER_MANIFEST` to an absolute path (as in the setup above).
- Fix the manifest dates and `scope.hosts`, then restart Claude Code (or run
  `/mcp reconnect all`) to reload it.

### Burp not connecting

```bash
# Check if the Burp proxy is running
curl -x http://127.0.0.1:8080 http://example.com
```

Browser tools proxy through Burp; if Burp isn't up they will fail. Recon
tools need `nmap` / `nikto` installed on your machine.

## Security notes

- All URLs are validated against the engagement manifest; out-of-scope
  targets are refused.
- All actions are logged to `audit_trail/`.
- Only test targets you are authorized to test.

## Tips for effective use

Be specific:

```
❌ "Test for vulnerabilities"
✅ "Test the search parameter for XSS"
```

Provide context:

```
✅ "I'm testing an e-commerce app. Focus on the checkout flow."
```

Use multi-step requests:

```
You:
1. Navigate to app.example.com
2. Login as testuser
3. Find all form inputs
4. Test each one for XSS
```
