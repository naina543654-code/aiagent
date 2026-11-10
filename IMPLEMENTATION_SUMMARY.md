# AIPentester - Implementation Summary

## What This Is

An **interactive AI pentesting assistant** that you chat with in your terminal. Claude controls Browser Use and Burp Suite to perform security testing while you watch and guide.

## Core Concept

```
You (Terminal) ←→ Claude (Agent) ←→ Browser Use ←→ Target App
                        ↓
                    Burp MCP
                        ↓
                  Burp Suite Tools
              (Repeater/Intruder/Collaborator)
```

## Key Files

### Main Agent
- **`src/aipentester/agent.py`** - Interactive chat agent (300 lines)
  - Handles conversation with Claude
  - Defines tools Claude can use
  - Executes tool calls
  - Manages safety controls

### Browser Automation
- **`src/aipentester/browser/browser_use_adapter.py`** - Browser Use integration (200 lines)
  - Configures browser with Burp proxy
  - Handles login (with optional TOTP)
  - Takes screenshots
  - Extracts forms and links

### Burp Integration
- **`src/aipentester/burp/burp_mcp_client.py`** - Burp MCP client (150 lines)
  - Connects to Burp MCP server
  - Send to Repeater/Intruder
  - Collaborator payload generation/checking
  - Proxy history retrieval

### Safety & Models
- **`src/aipentester/safety/scope_validator.py`** - Validates all URLs
- **`src/aipentester/safety/audit_log.py`** - Logs every action
- **`src/aipentester/models/engagement.py`** - Engagement manifest schema

### CLI
- **`src/aipentester/cli/main.py`** - Entry point
- **`src/aipentester/cli/commands/init.py`** - Project initialization

## How It Works

### 1. Initialization

```python
agent = PentestAgent(manifest)
await agent.initialize()  # Starts browser + connects to Burp
```

### 2. Interactive Loop

```python
await agent.run_interactive()  # Chat loop
```

User types → Claude processes → Claude uses tools → Claude responds

### 3. Tool Execution

Claude can call:
- `browser_navigate(url)` - Navigate browser
- `browser_login(username, password)` - Login
- `burp_send_to_repeater(request_id)` - Send to Repeater
- `burp_send_to_intruder(request_id, payloads)` - Run Intruder attack
- `burp_collaborator_generate()` - Get Collaborator payload
- `burp_collaborator_check(payload)` - Check interactions
- `burp_get_proxy_history()` - Get recent requests

### 4. Safety Enforcement

Before every browser navigation:
```python
self.scope_validator.validate_url(url)  # Raises if out of scope
```

Every action logged:
```python
self.audit_logger.log_action(action, target, risk_level)
```

## Installation

```bash
pip install -e .
playwright install chromium
```

## Usage

```bash
# Terminal 1: Burp MCP server
npx -y @burp-suite-mcp/server

# Terminal 2: AIPentester
aipentester init
# Edit engagement_manifest.yaml and .env
aipentester chat
```

## Example Session

```
$ aipentester chat

🔒 Ready to Test
Engagement: Example Corp Assessment
Scope: app.example.com, *.example.com

You: Login to app.example.com and test for XSS

Agent: thinking...
Agent: I'll help you test for XSS. Let me start by logging in...

[Tool: browser_navigate]
Navigated to https://app.example.com/login. Screenshot saved.

[Tool: browser_login]
Login successful

Now let me get the recent proxy history to find interesting requests...

[Tool: burp_get_proxy_history]
Retrieved 12 requests:
1. GET https://app.example.com/dashboard - 200
2. POST https://app.example.com/search?q=test - 200
3. GET https://app.example.com/profile?id=123 - 200

The search endpoint looks promising. Let me test it with XSS payloads using Burp Intruder...

[Tool: burp_send_to_intruder]
Configured Intruder attack with 50 XSS payloads on search parameter.
Results: 1 payload reflected without encoding!

FINDING: Reflected XSS
- URL: https://app.example.com/search
- Parameter: q
- Payload: <img src=x onerror=alert(1)>
- Evidence: Response contains unencoded payload in <h1> tag

I've sent this to Burp Repeater (tab #3) for you to verify.

Would you like me to:
1. Test other parameters for XSS
2. Move on to SQL injection testing
3. Check for CSRF protection

You: Test for SQL injection in the profile ID parameter

Agent: ...
```

## What's Implemented

✅ Interactive chat with Claude
✅ Browser Use integration with Burp proxy
✅ Burp MCP client (Repeater, Intruder, Collaborator)
✅ Scope validation
✅ Audit logging
✅ Engagement manifest system
✅ Safety controls
✅ Login with TOTP support
✅ Screenshot capture
✅ All attacks via Burp tools only

## What's NOT Needed (Removed from Original Design)

❌ Separate CLI commands (we have chat instead)
❌ DuckDB storage (logs to JSONL, findings in Burp)
❌ Report generation (Burp handles this)
❌ Context file ingestion (can paste into chat)
❌ Sub-agents (Claude is the agent)
❌ Review queue UI (approval happens in chat)
❌ Evidence encryption (keep in Burp)

## Dependencies

Minimal set:
- `typer` - CLI framework
- `rich` - Terminal UI
- `anthropic` - Claude API
- `browser-use` - Browser automation
- `playwright` - Browser driver
- `mcp` - Burp MCP client
- `pydantic` - Data validation
- `pyotp` - TOTP support
- `structlog` - Logging

## Architecture

```
┌─────────────┐
│   You       │  Types commands in terminal
└─────┬───────┘
      │
┌─────▼────────┐
│ PentestAgent │  Claude-powered conversational agent
│              │  - Scope validation
│              │  - Audit logging
│              │  - Tool execution
└─────┬────────┘
      │
      ├─────────────────────┐
      │                     │
┌─────▼──────────┐   ┌──────▼─────────┐
│ BrowserUse     │   │ BurpMCPClient  │
│ Adapter        │   │                │
│ - Navigate     │   │ - Repeater     │
│ - Login        │   │ - Intruder     │
│ - Screenshot   │   │ - Collaborator │
└────────────────┘   └────────────────┘
```

## Testing

The tool is ready to use! Test by:

1. Create test engagement manifest
2. Point to a test app (DVWA, WebGoat, or your authorized target)
3. Run `aipentester chat`
4. Ask Claude to test specific vulnerabilities

## Next Steps

1. Install dependencies
2. Configure Burp Suite with MCP
3. Create engagement manifest
4. Start chatting with Claude!

## Limitations

- Requires Burp Suite Professional (for MCP server)
- Requires Anthropic API key
- Claude's effectiveness depends on prompt quality
- May need to customize login selectors per app
- Burp MCP may have API limitations

## Safety

All requests validated against scope before execution.
All actions logged to `audit_trail/`.
Secrets masked in all output.
No automated exploitation without explicit instruction.

---

**Total Code**: ~800 lines (agent + adapters + safety + models)
**Status**: Ready to use!
**Requirements**: Burp Suite Pro, Anthropic API key, authorized target
