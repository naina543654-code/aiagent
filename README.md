# AIPentester

> **Attribution / fixed copy:** This copy originates from
> [nayangoel/AIPentester](https://github.com/nayangoel/AIPentester) (main,
> commit `c08e65e`). The upstream snapshot did not work as shipped — the MCP
> server crashed on import, `validate-scope` and `plan` were missing, and a
> test failed. This copy fixes those issues; see [FIXES.md](FIXES.md) for the
> full list of bugs, fixes, and verification evidence.
>
> **Multi-agent framework:** this copy additionally wires three pieces into
> one framework — this repo's CLI + MCP server (tool layer), the specialist
> subagents from the pentest-framework Claude Code scaffold, and the
> SQLite/scoping/redaction engine from the ai-pentest-framework Python
> Phase 1 code. Orchestrator + specialists (Sonnet) with a Haiku scripter
> and scribe, a validator that alone confirms findings, and shared state
> that survives a crashed session (append-only journal, findings store,
> scribe-owned `STATE.md`). See [MULTI_AGENT_DESIGN.md](MULTI_AGENT_DESIGN.md),
> [CLAUDE.md](CLAUDE.md), and `.claude/agents/`.

**AI-powered pentesting assistant for Claude Desktop and Claude Code**

Give Claude superpowers to perform authorized security testing using Browser Use and Burp Suite!

## What This Is

AIPentester is an **MCP server** that lets you chat with Claude (in Claude Desktop or Claude Code) to perform penetration testing. Claude can:

- 🌐 Navigate applications through Burp proxy
- 🔐 Login with credentials (+ TOTP MFA) with automatic CAPTCHA detection
- 🔍 Use Burp Repeater for manual testing
- ⚡ Run Burp Intruder attacks with custom payloads
- 📡 Use Burp Collaborator for out-of-band testing
- 📸 Capture screenshots as evidence
- 🗺️ Autonomously crawl and map entire applications
- 🧠 Generate AI-driven threat models and attack scenarios
- 🔎 Run nmap and nikto reconnaissance scans
- 💥 Generate proof-of-concept exploits for findings
- 🎯 All while enforcing scope and logging everything

**No Anthropic API key needed for MCP mode** - uses your Claude subscription!

## Quick Start

### 1. Install

```bash
cd AIPentester
pip install -e .
playwright install chromium
```

### 2. Install Recon Tools (optional but recommended)

```bash
# macOS
brew install nmap nikto

# Linux
apt-get install nmap nikto
```

### 3. Initialize

```bash
python -m aipentester.cli.main init
```

### 4. Configure

Edit `engagement_manifest.yaml`:

```yaml
scope:
  hosts:
    - "yourapp.example.com"  # ← CHANGE THIS!
```

### 5. Choose Your Interface

**Option A: Claude Desktop (Mac App)**
→ See [CLAUDE_DESKTOP_SETUP.md](CLAUDE_DESKTOP_SETUP.md)

**Option B: Claude Code (Terminal)**
→ See [CLAUDE_CODE_SETUP.md](CLAUDE_CODE_SETUP.md)

### 6. Start Burp

```bash
# Terminal 1: Burp MCP server
npx -y @burp-suite-mcp/server

# Make sure Burp Suite Pro is running with proxy on 127.0.0.1:8080
```

### 7. Start Testing!

**Claude Desktop:** Open the app and chat

**Claude Code:** Run `claude-code` in terminal

Then just talk to Claude:

```
You: Pentest app.example.com

Claude: Running full pentest...
[recon_nmap_quick_scan → pentest_crawl_application → pentest_analyze_threats]

Discovered 3 endpoints. Generated threat model with 5 attack scenarios.
Testing XSS in /search... FOUND! Reflected XSS in q parameter.
Testing SQLi in /user/profile... testing...
```

## How It Works

```
┌────────────────┐
│ You            │  "Pentest this app"
│ (Chat)         │
└───────┬────────┘
        │
┌───────▼────────┐
│ Claude         │  Uses MCP tools
│ (Desktop/Code) │
└───────┬────────┘
        │
┌───────▼────────┐
│ AIPentester    │  MCP Server
│ (This Tool)    │
└───┬────────┬───┘
    │        │
    │    ┌───▼────────┐
    │    │ Burp MCP   │  Repeater, Intruder, Collaborator
    │    └────────────┘
    │
┌───▼────────┐
│ Browser    │  Playwright + Burp Proxy
│ (Headful)  │
└────────────┘
```

## Available Tools for Claude

Claude can use these tools when chatting with you:

### Browser Tools

| Tool | Purpose |
|------|---------|
| `browser_navigate` | Navigate to URLs through Burp proxy |
| `browser_login` | Authenticate with username/password/TOTP (detects CAPTCHAs) |
| `browser_screenshot` | Take screenshots for evidence |
| `browser_get_page_text` | Get visible text content of current page |
| `browser_find_elements` | Find interactive elements by text or attributes |
| `browser_click_element` | Click buttons, links, and other elements |
| `browser_extract_links` | Get all links on the current page |
| `browser_find_forms` | Find all forms and their input fields |

### Reconnaissance Tools

| Tool | Purpose |
|------|---------|
| `recon_nmap_quick_scan` | Quick port scan (top 1000 ports) |
| `recon_nmap_service_scan` | Detailed service/version detection |
| `recon_nmap_vuln_scan` | Nmap vulnerability scripts |
| `recon_nikto_scan` | Nikto web server vulnerability scanner |

### Pentest Workflow Tools

| Tool | Purpose |
|------|---------|
| `pentest_crawl_application` | Auto-crawl app to discover all pages, forms, endpoints |
| `pentest_analyze_threats` | Generate threat model with attack scenarios from app map |
| `pentest_run_autonomous` | Full autonomous test: recon → crawl → threat model |
| `pentest_skill_execute` | Structured pentest: recon → auth → crawl → threat model → POC |
| `pentest` | One-liner full pentest: just say "Pentest example.com" |

### Burp Suite Tools (via Burp MCP)

| Tool | Purpose |
|------|---------|
| `burp_get_proxy_history` | View captured HTTP requests |
| `burp_send_to_repeater` | Send requests for manual testing |
| `burp_send_to_intruder` | Run automated fuzzing attacks |
| `burp_collaborator_generate` | Get out-of-band payload |
| `burp_collaborator_check` | Check for OOB interactions |

## Autonomous Pentest Workflow

The `pentest_skill_execute` and `pentest` tools run a structured multi-phase workflow:

```
RECON → AUTH → CRAWL → THREAT_MODEL → POC_GENERATION → REPORTING
  │       │       │           │               │
nmap    login   spider    analyze         generate
nikto   TOTP    vision    scenarios       exploits
```

Each phase feeds the next — recon finds services, crawling maps endpoints, threat modeling generates targeted attack scenarios, and POC generation creates working exploit code for verified findings.

## CLI Commands

AIPentester also ships a standalone CLI (requires `ANTHROPIC_API_KEY`):

```bash
# Run full autonomous pentest
aipentester pentest http://target.example.com

# With login
aipentester pentest http://target.example.com --login

# Skip recon
aipentester pentest http://target.example.com --no-recon

# Reconnaissance only
aipentester recon nmap-quick target.example.com
aipentester recon nmap-service target.example.com --ports 80,443,8080
aipentester recon nmap-vuln target.example.com
aipentester recon nikto target.example.com --ssl --scan-type full

# Interactive chat session
aipentester chat

# Initialize new engagement
aipentester init
```

## Example Conversations

### One-Liner Full Pentest
```
You: Pentest app.example.com with authentication

Claude: Starting full pentest...
[nmap scan → nikto scan → login → crawl → threat model → POC generation]

FINDINGS:
- Critical: Reflected XSS in /search (q parameter)
- High: SQL Injection in /user/profile (id parameter)  
- Medium: CSRF on /account/settings
```

### XSS Testing
```
You: Test the search functionality for XSS

Claude: I'll test the search for XSS...
[navigates, finds search, uses Intruder with XSS payloads]
Found reflected XSS!
```

### SQL Injection
```
You: Check if /user/profile?id=123 has SQL injection

Claude: Testing the id parameter for SQLi...
[gets request from proxy, sends to Intruder with SQLi payloads]
```

### SSRF with Collaborator
```
You: Use Burp Collaborator to test for SSRF in the webhook_url parameter

Claude: Generating Collaborator payload...
[generates payload, injects, checks for callbacks]
Detected DNS and HTTP callbacks! SSRF confirmed.
```

### Autonomous Reconnaissance
```
You: Run a full recon scan on target.example.com

Claude: Running nmap and nikto...
[recon_nmap_service_scan → recon_nikto_scan]

Open ports: 22 (SSH), 80 (HTTP/nginx 1.18), 443 (HTTPS), 8080 (Tomcat 9.0)
Nikto findings: 3 outdated headers, directory listing on /backup/
```

## Attack Types Supported

Claude can test for:

- ✅ **XSS** (Reflected, Stored, DOM-based)
- ✅ **SQL Injection** (Error-based, Blind, Time-based)
- ✅ **Command Injection** (OS command injection)
- ✅ **SSRF** (Server-Side Request Forgery)
- ✅ **IDOR** (Insecure Direct Object References)
- ✅ **Authentication Bypass**
- ✅ **Authorization Flaws**
- ✅ **CSRF** (Cross-Site Request Forgery)
- ✅ **Path Traversal**
- ✅ **XXE** (XML External Entity)
- ✅ **File Upload** vulnerabilities
- ✅ **Business Logic** flaws

All testing done via **Burp tools only** - no direct exploitation.

## Safety Controls

- ✅ **Scope Validation**: Every URL checked against engagement manifest
- ✅ **Audit Logging**: All actions logged to `audit_trail/`
- ✅ **Secrets Masking**: Credentials never in logs
- ✅ **Authorization Required**: Engagement manifest mandatory
- ✅ **Burp-Only Attacks**: No automatic exploitation
- ✅ **Evidence Capture**: Screenshots and requests saved
- ✅ **CAPTCHA Detection**: Automatically pauses when CAPTCHA detected, prompts for human intervention

## Project Structure

```
AIPentester/
├── engagement_manifest.yaml   # Your authorized scope
├── .env                        # Burp proxy settings
├── run_mcp_server.py          # MCP server entry point
├── src/aipentester/
│   ├── mcp_server.py          # MCP server + all tools
│   ├── browser/               # Browser automation + CAPTCHA handling
│   ├── crawler/               # App crawler (spider + vision-based)
│   ├── pentest/               # Pentest orchestrator, test executor, POC generator
│   ├── recon/                 # Nmap and Nikto scanner wrappers
│   ├── cli/                   # CLI commands (pentest, recon, chat, init)
│   ├── threat_model/          # Threat analyzer
│   ├── models/                # Data models
│   └── safety/                # Scope validation, audit logging
├── evidence/
│   └── screenshots/           # Captured screenshots
└── audit_trail/               # Action logs
```

## Requirements

- **Python 3.11+**
- **Playwright** (for browser automation)
- **Burp Suite Professional** (for security testing)
- **Claude Desktop** or **Claude Code** (for MCP mode AI)
- **nmap** (optional, for recon tools)
- **nikto** (optional, for web recon)
- **Anthropic API key** (optional, for CLI `pentest` and `recon` commands)

## Comparison: Claude Desktop vs Claude Code

| Feature | Claude Desktop | Claude Code |
|---------|----------------|-------------|
| Interface | Mac GUI app | Terminal |
| Use Case | Interactive testing | Integrated workflow |
| File Access | Limited | Full access |
| Best For | Focused pentesting | DevSecOps workflows |

Both use the same MCP server!

## Configuration Files

### `engagement_manifest.yaml`
Defines authorized scope, test dates, analyst info.

### `~/.config/claude-code/config.json` (Claude Code)
Or `~/Library/Application Support/Claude/claude_desktop_config.json` (Desktop)

```json
{
  "mcpServers": {
    "aipentester": {
      "command": "/path/to/venv/bin/python",
      "args": ["/path/to/AIPentester/run_mcp_server.py"],
      "env": {
        "AIPENTESTER_MANIFEST": "/path/to/engagement_manifest.yaml"
      }
    }
  }
}
```

## Troubleshooting

### Tools Not Available in Claude

1. Check MCP config file has correct paths
2. Restart Claude Desktop/Code
3. Test MCP server: `python run_mcp_server.py`

### Scope Validation Errors

1. Edit `engagement_manifest.yaml`
2. Add target to `scope.hosts`
3. Restart Claude to reload

### Burp Not Connecting

1. Burp Suite Pro running?
2. Proxy on 127.0.0.1:8080?
3. Burp MCP server: `npx -y @burp-suite-mcp/server`

### Browser Won't Start

```bash
playwright install chromium
```

### Nmap/Nikto Not Found

```bash
# macOS
brew install nmap nikto

# Linux
apt-get install nmap nikto
```

### CAPTCHA Detected During Login

AIPentester automatically detects reCAPTCHA and hCaptcha and pauses with a `CaptchaDetectedException`. Solve the CAPTCHA manually in the browser window, then retry the login.

## Tips for Effective Testing

1. **Be Conversational**: "Pentest this app" works — Claude knows what to do
2. **Use Autonomous Mode**: `pentest` tool runs the full workflow without manual steps
3. **Provide Context**: Tell Claude what you're testing and why
4. **Ask Questions**: "What should I test next?" or "Explain this finding"
5. **Verify Findings**: Always manually verify in Burp Repeater
6. **Iterate**: Build on findings - "Now test the admin panel"

## Documentation

- **[CLAUDE_DESKTOP_SETUP.md](CLAUDE_DESKTOP_SETUP.md)** - Setup for Claude Desktop
- **[CLAUDE_CODE_SETUP.md](CLAUDE_CODE_SETUP.md)** - Setup for Claude Code terminal
- **[PENTEST_SKILL_GUIDE.md](PENTEST_SKILL_GUIDE.md)** - Guide to the structured pentest skill
- **[INTERACTIVE_PENTEST_GUIDE.md](INTERACTIVE_PENTEST_GUIDE.md)** - Interactive testing guide
- **[IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md)** - Technical details

## Limitations

- Requires Burp Suite **Professional** (for MCP server)
- Recon tools (`nmap`, `nikto`) must be installed separately
- Browser automation may need customization per app
- Login function uses common selectors (may need adjustment for non-standard forms)
- CAPTCHA solving requires manual intervention

## License

[Choose appropriate license]

## Disclaimer

**FOR AUTHORIZED SECURITY TESTING ONLY**

This tool is designed for:
- ✅ Authorized penetration testing with written permission
- ✅ Security research on your own systems
- ✅ Bug bounty programs (following their rules)

Users are responsible for:
- Obtaining proper authorization
- Complying with laws and regulations
- Respecting scope constraints
- Maintaining confidentiality

---

**⚠️ CRITICAL: Only test systems you have written authorization to test!**

Happy (authorized) hacking! 🔒
