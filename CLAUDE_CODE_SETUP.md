# Using AIPentester with Claude Code (Terminal)

## What This Is

Use AIPentester as an MCP server with **Claude Code** in your Mac terminal! Chat with Claude right in your terminal and it can perform pentests using Browser Use + Burp Suite.

**No Anthropic API key needed** - uses your Claude subscription!

## Setup for Claude Code

### 1. Install Prerequisites (Already Done ✅)

```bash
cd /Users/nayan/Documents/Code/AIPentester
pip install -e .
playwright install chromium
```

### 2. Initialize Project

```bash
python -m aipentester.cli.main init
```

Edit `engagement_manifest.yaml` with your authorized scope.

### 3. Configure Claude Code MCP

Claude Code uses MCP servers configured in `~/.config/claude-code/config.json`

**Create/Edit:** `~/.config/claude-code/config.json`

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

**Adjust paths if needed!**

### 4. Start Burp Suite

Terminal 1:
```bash
# Make sure Burp Suite Professional is running
# Proxy on 127.0.0.1:8080

# Start Burp MCP server
npx -y @burp-suite-mcp/server
```

### 5. Start Claude Code

Terminal 2:
```bash
claude-code
```

Or if you have a project directory:
```bash
cd /path/to/your/project
claude-code
```

### 6. Start Pentesting!

In Claude Code terminal:

```
You: I need to test app.example.com for XSS vulnerabilities

Claude: I can help with that! Let me start by navigating to the application...
[uses browser_navigate tool]

I can see we're at the login page. Would you like me to login using the credentials?

You: Yes, login with credentials from the environment

Claude: Logging in now...
[uses browser_login tool]

Success! Now let me check the proxy history to find interesting endpoints...
[uses burp_get_proxy_history]

I found several endpoints. The /search endpoint looks promising for XSS testing.
Let me send it to Burp Intruder with XSS payloads...
```

## Available Tools

Claude Code can use:

1. **browser_navigate** - Navigate with Burp proxy
2. **browser_login** - Authenticate
3. **browser_screenshot** - Capture evidence
4. **burp_get_proxy_history** - View requests
5. **burp_send_to_repeater** - Manual testing
6. **burp_send_to_intruder** - Automated fuzzing
7. **burp_collaborator_generate** - OOB testing
8. **burp_collaborator_check** - Check callbacks

## Example Commands

### Basic Testing
```
You: Test https://app.example.com for common vulnerabilities

You: Check the search parameter for XSS and SQL injection

You: Use Collaborator to test for SSRF vulnerabilities
```

### Workflow-Based
```
You:
1. Navigate to app.example.com
2. Login as testuser
3. Find all form inputs
4. Test each one for XSS

You: Help me test the checkout flow for business logic flaws
```

### Context Provision
```
You: Here's a previous pentest report. Retest all findings:
[paste report or describe findings]

You: The app was vulnerable to XSS in /search?q= in v1.2.
Version 1.3 supposedly fixed it. Can you verify?
```

## Checking if MCP Server is Loaded

In Claude Code:

```
You: What tools do you have access to?

Claude: I have access to these AIPentester tools:
- browser_navigate: Navigate to URLs through Burp proxy
- browser_login: Authenticate to applications
[... lists all tools ...]
```

## Workflow Example

```bash
# Terminal 1: Burp MCP Server
npx -y @burp-suite-mcp/server

# Terminal 2: Claude Code
claude-code
```

Then in Claude Code:
```
You: Let's pentest app.example.com

Claude: I can help! First, I need to check if this is in our authorized scope.
[reads engagement manifest resource]

Yes, app.example.com is in scope. Let me navigate there...
[uses browser_navigate]

I see a login page. Should I attempt to login?

You: Yes, use the creds from environment

Claude: [uses browser_login]
Success! I'm now logged in. Let me check what requests were captured...
[uses burp_get_proxy_history]

I see several interesting endpoints:
1. /api/search?q=
2. /api/user/profile?id=
3. /admin/settings

Which would you like me to test first, or should I start with the most common vulnerabilities?

You: Test the search for XSS

Claude: [uses burp_send_to_intruder with XSS payloads]

FINDING: Reflected XSS detected!
- Parameter: q
- Payload: <img src=x onerror=alert(1)>
- Evidence: Payload reflected in HTML without encoding

I've sent this to Burp Repeater for you to verify manually.
Would you like me to continue testing other parameters?
```

## Advantages of Claude Code Terminal

1. **Integrated with your workflow** - Stay in terminal
2. **File access** - Claude can read/write files in your project
3. **Git integration** - Can commit findings
4. **Natural language** - Just describe what you want
5. **Full context** - Remembers the whole conversation

## Tips for Effective Use

### Be Specific
```
❌ "Test for vulnerabilities"
✅ "Test the search parameter for XSS using Burp Intruder"
```

### Provide Context
```
✅ "I'm testing an e-commerce app. Focus on the checkout flow and payment processing"
```

### Ask for Help
```
✅ "What should I test next given what we've found so far?"
✅ "Explain this SQL injection finding"
✅ "How can I verify this XSS is exploitable?"
```

### Use Multi-Step Requests
```
You:
1. Navigate to the app
2. Login
3. Find the admin panel
4. Test for authorization bypass
5. Document any findings
```

## Combining with Other MCP Servers

You can use AIPentester alongside other MCP servers:

```json
{
  "mcpServers": {
    "aipentester": { ... },
    "filesystem": { ... },
    "github": { ... }
  }
}
```

This lets Claude:
- Pentest with AIPentester
- Write reports to files
- Create GitHub issues for findings
- All in one conversation!

## Troubleshooting

### MCP Server Not Loading

Check `~/.config/claude-code/config.json`:
```bash
cat ~/.config/claude-code/config.json
```

Verify:
- Paths are absolute
- Python path is correct (use `which python` in your venv)
- manifest path exists

### Test MCP Server Manually

```bash
cd /Users/nayan/Documents/Code/AIPentester
venv/bin/python run_mcp_server.py
```

Should wait for stdin (that's correct behavior).

### Burp Not Connecting

```bash
# Check if Burp proxy is running
curl -x http://127.0.0.1:8080 http://example.com

# Check if Burp MCP is running
npx -y @burp-suite-mcp/server
```

### Scope Validation Errors

Edit `engagement_manifest.yaml` and add your target to `scope.hosts`.

Then restart Claude Code to reload the manifest.

## Security Notes

- All URLs validated against engagement manifest
- All actions logged to `audit_trail/`
- Only authorized Burp tools used (no automatic exploitation)
- Screenshots saved to `evidence/screenshots/`

## Example Session

```bash
$ claude-code

Claude Code v0.1.0

You: I want to test app.example.com for XSS

Claude: I'll help you test for XSS. Let me first verify this is in our authorized scope...
✓ app.example.com is in scope

Navigating to https://app.example.com...
✓ Navigation complete. Screenshot saved to evidence/screenshots/screenshot_0001.png

I see a login form. Would you like me to login?

You: yes

Claude: Logging in with credentials from environment...
✓ Login successful

Now checking proxy history for interesting endpoints...

Found these requests:
1. POST /login - 302
2. GET /dashboard - 200
3. GET /search?q=test - 200  ← This looks promising for XSS
4. GET /api/products - 200

Let me test the search endpoint for XSS...

Sending to Burp Intruder with 50 XSS payloads...
✓ Attack complete

FINDING: Reflected XSS Vulnerability
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
URL: https://app.example.com/search
Parameter: q
Payload: <img src=x onerror=alert(1)>
Response: Payload reflected without encoding

Evidence:
- Request sent to Burp Repeater (tab #1)
- Screenshot: evidence/screenshots/screenshot_0002.png

Would you like me to:
1. Test other parameters for XSS
2. Test for other vulnerability types
3. Document this finding

You: document it and continue testing

Claude: Creating finding report...
✓ Report saved to findings/xss_search_parameter.md

Continuing with security testing...
[continues testing]
```

---

**You're ready! Just run `claude-code` and start pentesting! 🚀**
