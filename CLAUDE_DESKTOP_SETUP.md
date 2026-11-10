# Using AIPentester with Claude Desktop (Mac)

## What This Is

AIPentester is an **MCP server** that gives Claude Desktop pentesting superpowers.
You chat with Claude in the Claude Desktop app, and it can use the browser,
recon tools, and Burp proxy traffic to perform security testing.

**No Anthropic API key needed for MCP mode** — it uses your Claude Desktop
subscription. (The `aipentester chat` / `pentest` CLI commands are the ones that
need an Anthropic API key; MCP mode does not.)

This guide was corrected 2026-11-11: the upstream version hardcoded the
original author's paths (`/Users/nayan/...`), shipped an engagement manifest
example with expired 2024 dates, and listed Burp tools that are not actually
exposed over MCP. All three are fixed below.

## Prerequisites (Mac)

```bash
git clone https://github.com/naina543654-code/AIPentester.git
cd AIPentester
python3 -m venv .venv
.venv/bin/pip install -e ".[dev]"
.venv/bin/playwright install chromium   # only needed for the browser_* tools
```

Replace `/path/to/AIPentester` everywhere below with your real clone path.

## 1. Initialize a project (required)

The MCP server refuses to run tools until it can load an engagement manifest,
so do this first, in the directory you will pentest from:

```bash
.venv/bin/aipentester init
```

This creates `engagement_manifest.yaml`, a `.env` file, and the working
directories (`evidence/`, `audit_trail/`, `reports/`, ...).

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
before continuing — Claude Desktop will hit the same error on every tool call.

## 2. Configure `.env` (optional)

Edit `.env` only if you need non-default settings:

```bash
# Burp Proxy (defaults are usually fine)
BURP_PROXY_HOST=127.0.0.1
BURP_PROXY_PORT=8080

# Burp MCP Server (defaults are usually fine)
BURP_MCP_HOST=localhost
BURP_MCP_PORT=3000

# App credentials (if you want to use browser_login)
TEST_APP_USERNAME=testuser
TEST_APP_PASSWORD=<redacted>
# TEST_APP_TOTP_SECRET=<redacted>  # Optional
```

## 3. Configure Claude Desktop

Claude Desktop reads its MCP servers from:

**macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows:** `%APPDATA%\Claude\claude_desktop_config.json`

Easiest way to open it: **Claude Desktop → Settings → Developer → Edit Config**.
(Desktop does not pick up config changes while running — quit and reopen it
after editing.)

Add the server under `mcpServers` (use absolute paths):

```json
{
  "mcpServers": {
    "aipentester": {
      "command": "/path/to/AIPentester/.venv/bin/python",
      "args": [
        "/path/to/AIPentester/run_mcp_server.py"
      ],
      "env": {
        "AIPENTESTER_MANIFEST": "/path/to/AIPentester/engagement_manifest.yaml",
        "BURP_PROXY_HOST": "127.0.0.1",
        "BURP_PROXY_PORT": "8080"
      }
    }
  }
}
```

Setting `AIPENTESTER_MANIFEST` to an absolute path matters: Claude Desktop
starts the server with its own working directory, so a relative manifest path
will not be found.

## 4. Start Burp Suite (optional but recommended)

Browser traffic is routed through the Burp proxy, so start Burp first:

1. Open **Burp Suite Professional**
2. Enable the proxy listener on **127.0.0.1:8080**

If you also want Burp's own MCP server running alongside (a separate server,
not this one):

```bash
npx -y @burp-suite-mcp/server
```

## 5. Restart Claude Desktop and start pentesting

Fully quit and reopen Claude Desktop to load the MCP server, then start a new
conversation:

```
You: I need to test app.example.com for XSS. Can you help?

Claude: Let me check the scope first...
[reads aipentester://scope]

app.example.com is in scope. Navigating there now...
[uses browser_navigate tool]
```

## Tools Claude Desktop actually gets

Verified against the fixed server (real MCP client handshake: 17 tools,
2 resources). These are the tools Claude can call:

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
`aipentester chat`. Claude Desktop cannot call them directly.

What Claude Desktop *does* get from Burp is indirect: browser traffic is routed
through the Burp proxy (default `127.0.0.1:8080`), so requests are captured
there for you to inspect manually. Also note this project's `BurpMCPClient`
targets an undocumented Burp HTTP API and has **not** been verified against
the real Burp MCP server, so treat any Burp-backed behaviour as untested until
you confirm it yourself.

## Example conversations

### XSS testing
```
You: Test https://app.example.com for XSS vulnerabilities

Claude: I'll check the scope, then navigate to the site and look for forms...
[navigates, finds forms, analyses the traffic for injection points]
```

### SQL injection
```
You: Check if the /user/profile?id=123 endpoint is vulnerable to SQL injection

Claude: I'll navigate to that endpoint and analyse the parameter...
```

### Context-based retesting
```
You: We found XSS in /search?q= in version 1.2 which was supposedly fixed. Can you retest it?

Claude: I'll retest that XSS vulnerability...
[navigates to /search, tests the q parameter]
```

## Checking if it works

After restarting Claude Desktop:

1. Open a new conversation.
2. Look for the 🔧 tool icon — you should see AIPentester tools available.
3. Ask Claude: "What pentesting tools do you have access to?"
4. Claude should list the browser, pentest, and recon tools above.

## Troubleshooting

### "No tools available"

Check `~/Library/Application Support/Claude/claude_desktop_config.json`:
- Paths are absolute and correct.
- `command` points to your venv Python (`.venv/bin/python`).
- `args` points to `run_mcp_server.py`.
- Fully quit and reopen Claude Desktop (config is only read at startup).

You can also test the server manually — it should wait on stdin (that is
correct behaviour for a stdio server; Ctrl-C to stop it):

```bash
/path/to/AIPentester/.venv/bin/python /path/to/AIPentester/run_mcp_server.py
```

It prints `AIPentester MCP server starting...` to stderr, then waits. If it
exits with an import error instead, reinstall with
`.venv/bin/pip install -e ".[dev]"`.

### "Manifest not found" / "Scope validation failed"

- Set `AIPENTESTER_MANIFEST` in the config to the full (absolute) path.
- Edit `engagement_manifest.yaml`: add the target to `scope.hosts` and make
  sure the dates cover today. Verify with `aipentester validate-scope`.
- Restart Claude Desktop to reload the manifest.

### "Burp connection failed"

- Make sure Burp Suite Pro is running with the proxy on 127.0.0.1:8080:
  `curl -x http://127.0.0.1:8080 http://example.com`
- Browser tools proxy through Burp; if Burp isn't up they will fail. Recon
  tools need `nmap` / `nikto` installed on your machine.

## Logs and debugging

- **Audit trail**: `audit_trail/mcp-<pid>_<timestamp>.jsonl`
- **Screenshots**: `evidence/screenshots/`
- **Claude Desktop logs**: Check Console.app for the "Claude" process.

## Safety

- All URLs are validated against the engagement manifest; out-of-scope
  targets are refused.
- All actions are logged to the audit trail.
- Only test targets you are authorized to test.

## Advantages of this approach

1. **No API costs** — uses your Claude Desktop subscription.
2. **Natural conversation** — chat with Claude like a colleague.
3. **Full context** — Claude remembers the whole conversation.
4. **Integrated** — all tools in one interface.

## What to ask Claude

```
"Can you help me test this app for XSS?"
"I found a suspicious endpoint, can you investigate?"
"Test all form inputs for SQL injection"
"Here's a previous report, retest these findings"
"What should I test next?"
"Explain this finding to me"
```

---

**You're all set! Open Claude Desktop and start pentesting! 🔒**
