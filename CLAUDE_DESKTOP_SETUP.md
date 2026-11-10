# Using AIPentester with Claude Desktop (Mac)

## What This Is

AIPentester is an **MCP server** that gives Claude Desktop pentesting superpowers! You chat with Claude in the Claude Desktop app, and it can use Browser Use + Burp Suite to perform security testing.

**No Anthropic API key needed** - you're using your Claude Desktop subscription!

## Setup Steps

### 1. Install AIPentester (Already Done ✅)

```bash
cd /Users/nayan/Documents/Code/AIPentester
pip install -e .
playwright install chromium
```

### 2. Initialize Project

```bash
python -m aipentester.cli.main init
```

This creates:
- `engagement_manifest.yaml` - Configure your authorized scope
- `.env` - Configure Burp proxy settings (no API key needed!)

### 3. Configure Engagement Manifest

Edit `engagement_manifest.yaml`:

```yaml
engagement:
  name: "My Security Assessment"
  id: "ACME-2024-001"
  authorized_by: "CISO Name"
  analyst_name: "Your Name"
  analyst_email: "your@email.com"
  start_date: "2024-01-01"
  end_date: "2024-12-31"
  authorization_acknowledgement: |
    I confirm I have written authorization to test these systems.

scope:
  hosts:
    - "app.example.com"        # CHANGE THIS to your authorized target!
    - "*.example.com"
  excluded_paths:
    - "/admin/dangerous-action"
  max_request_rate: 5
```

### 4. Configure .env (Optional)

Edit `.env` if you need non-default settings:

```bash
# Burp Proxy (defaults are usually fine)
BURP_PROXY_HOST=127.0.0.1
BURP_PROXY_PORT=8080

# Burp MCP Server (defaults are usually fine)
BURP_MCP_HOST=localhost
BURP_MCP_PORT=3000

# App credentials (if you want to use browser_login)
TEST_APP_USERNAME=testuser
TEST_APP_PASSWORD=testpass
# TEST_APP_TOTP_SECRET=JBSWY3DPEHPK3PXP  # Optional
```

### 5. Configure Claude Desktop

Add AIPentester to your Claude Desktop MCP servers.

**Edit:** `~/Library/Application Support/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "aipentester": {
      "command": "/Users/nayan/Documents/Code/AIPentester/venv/bin/python",
      "args": [
        "/Users/nayan/Documents/Code/AIPentester/run_mcp_server.py"
      ],
      "env": {
        "AIPENTESTER_MANIFEST": "/Users/nayan/Documents/Code/AIPentester/engagement_manifest.yaml",
        "BURP_PROXY_HOST": "127.0.0.1",
        "BURP_PROXY_PORT": "8080"
      }
    }
  }
}
```

**Important:** Adjust paths if you installed AIPentester elsewhere!

### 6. Start Burp Suite

1. Open **Burp Suite Professional**
2. Enable proxy listener on **127.0.0.1:8080**
3. In a terminal, start **Burp MCP server**:

```bash
npx -y @burp-suite-mcp/server
```

Leave this running.

### 7. Restart Claude Desktop

Quit and reopen Claude Desktop app to load the MCP server.

### 8. Start Pentesting! 🎉

Open Claude Desktop and start a new conversation:

```
You: I need to test app.example.com for XSS. Can you help?

Claude: I can help you test for XSS! Let me start by navigating to the application...
[uses browser_navigate tool]

You: Login with the credentials from the environment

Claude: I'll login now...
[uses browser_login tool]

You: Check the proxy history and test any search parameters for XSS

Claude: Let me check the proxy history...
[uses burp_get_proxy_history tool]
I found a search endpoint. Let me send it to Burp Intruder with XSS payloads...
[uses burp_send_to_intruder tool]

Found reflected XSS! The payload <script>alert(1)</script> was reflected without encoding...
```

## Available Tools for Claude

Claude can use these tools:

1. **browser_navigate** - Navigate to URLs (through Burp proxy)
2. **browser_login** - Login with credentials
3. **browser_screenshot** - Take screenshots
4. **burp_get_proxy_history** - See recent requests
5. **burp_send_to_repeater** - Send requests to Repeater
6. **burp_send_to_intruder** - Run fuzzing attacks
7. **burp_collaborator_generate** - Get Collaborator payload
8. **burp_collaborator_check** - Check for interactions

## Example Conversations

### XSS Testing
```
You: Test https://app.example.com for XSS vulnerabilities

Claude: I'll help test for XSS. First, let me navigate to the site...
[navigates, finds forms, tests with Burp Intruder]
```

### SQL Injection
```
You: Check if the /user/profile?id=123 endpoint is vulnerable to SQL injection

Claude: I'll test the id parameter for SQL injection...
[gets request from proxy history, sends to Intruder with SQLi payloads]
```

### SSRF Testing
```
You: Use Burp Collaborator to test for SSRF in the url parameter

Claude: I'll generate a Collaborator payload and test for SSRF...
[generates payload, tests, checks for interactions]
```

### Context-Based Retesting
```
You: We found XSS in /search?q= in version 1.2 which was supposedly fixed. Can you retest it?

Claude: I'll retest that XSS vulnerability...
[navigates to /search, tests the q parameter]
```

## Checking if It Works

After restarting Claude Desktop:

1. Open a new conversation
2. Look for the 🔧 tool icon - you should see AIPentester tools available
3. Ask Claude: "What pentesting tools do you have access to?"
4. Claude should list the browser and Burp tools

## Troubleshooting

### "No tools available"

Check `~/Library/Application Support/Claude/claude_desktop_config.json`:
- Paths are correct
- `command` points to your venv Python
- `args` points to `run_mcp_server.py`
- Restart Claude Desktop

### "Manifest not found"

- Set `AIPENTESTER_MANIFEST` in the config to the full path
- Or run `aipentester init` in your project directory

### "Burp connection failed"

- Make sure Burp Suite Pro is running
- Check proxy is on 127.0.0.1:8080
- Start Burp MCP server: `npx -y @burp-suite-mcp/server`

### "Scope validation failed"

- Edit `engagement_manifest.yaml`
- Add the target to `scope.hosts`
- Restart Claude Desktop to reload manifest

## Logs and Debugging

- **Audit trail**: `audit_trail/mcp-<pid>_<timestamp>.jsonl`
- **Screenshots**: `evidence/screenshots/`
- **Claude Desktop logs**: Check Console.app for "Claude" process

## Safety

- ✅ All URLs validated against scope before access
- ✅ All actions logged to audit trail
- ✅ Only uses Burp tools for attacks (no direct exploitation)
- ✅ Engagement manifest required

## Advantages of This Approach

1. **No API costs** - Uses your Claude Desktop subscription
2. **Natural conversation** - Chat with Claude like a colleague
3. **Full context** - Claude remembers the whole conversation
4. **Better reasoning** - Claude Desktop has full context window
5. **Integrated** - All tools in one interface

## What to Ask Claude

Be conversational! Claude is your pentesting partner:

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
