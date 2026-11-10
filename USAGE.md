# AIPentester Usage Guide

## Installation Complete ✅

Your tool is now ready to use!

## Available Commands

```bash
aipentester init      # Initialize a new project
aipentester chat      # Start interactive pentesting session
aipentester version   # Show version
```

## Complete Setup Checklist

### 1. ✅ Install (Already Done)
```bash
pip install -e .
playwright install chromium
```

### 2. ✅ Initialize Project (Already Done)
```bash
aipentester init
```

This created:
- `engagement_manifest.yaml` - Configure your scope
- `.env` - Set your API keys
- `evidence/` - Screenshots will be saved here
- `audit_trail/` - All actions logged here

### 3. Configure Engagement Manifest

Edit `engagement_manifest.yaml`:

**REQUIRED CHANGES:**
- `engagement.name` - Your engagement name
- `engagement.authorized_by` - Who authorized this test
- `engagement.analyst_name` - Your name
- `engagement.analyst_email` - Your email
- `scope.hosts` - **IN-SCOPE HOSTS ONLY**

**Example:**
```yaml
engagement:
  name: "ACME Corp Web App Pentest"
  id: "ACME-2024-001"
  authorized_by: "Jane Doe, CISO of ACME Corp"
  analyst_name: "Your Name"
  analyst_email: "you@security.com"
  start_date: "2024-01-01"
  end_date: "2024-12-31"
  authorization_acknowledgement: |
    I confirm I have written authorization to test these systems.

scope:
  hosts:
    - "app.acmecorp.com"
    - "*.staging.acmecorp.com"
  excluded_paths:
    - "/admin/delete-all-data"
  max_request_rate: 5
```

### 4. Configure Environment Variables

Edit `.env`:

**REQUIRED:**
```bash
ANTHROPIC_API_KEY=sk-ant-your-actual-key-here
```

**OPTIONAL (for login):**
```bash
TEST_APP_USERNAME=testuser
TEST_APP_PASSWORD=testpass
TEST_APP_TOTP_SECRET=JBSWY3DPEHPK3PXP  # Base32 TOTP secret if MFA enabled
```

**OPTIONAL (Burp settings):**
```bash
BURP_PROXY_HOST=127.0.0.1
BURP_PROXY_PORT=8080
BURP_MCP_HOST=localhost
BURP_MCP_PORT=3000
```

### 5. Start Burp Suite

**Terminal 1:**
```bash
# Open Burp Suite Professional
# Enable proxy listener on 127.0.0.1:8080
# Start Burp MCP server:
npx -y @burp-suite-mcp/server
```

Leave this running.

### 6. Start Pentesting!

**Terminal 2:**
```bash
aipentester chat
```

## Example Conversation

```
$ aipentester chat

🔒 Ready to Test
Engagement: ACME Corp Web App Pentest
Scope: app.acmecorp.com, *.staging.acmecorp.com

Type 'quit' to exit

You: Login to https://app.acmecorp.com with credentials from .env and test for XSS

Agent: thinking...
Agent: I'll help you test for XSS. Let me start by logging in...

[Tool: browser_navigate]
Navigated to https://app.acmecorp.com/login. Screenshot saved: evidence/screenshots/screenshot_0001.png

[Tool: browser_login]
Login successful

Now let me check the recent proxy history to find interesting endpoints...

[Tool: burp_get_proxy_history]
Retrieved 15 requests from proxy history:
1. POST https://app.acmecorp.com/login - 302
2. GET https://app.acmecorp.com/dashboard - 200
3. GET https://app.acmecorp.com/search?q=test - 200
4. POST https://app.acmecorp.com/api/products - 200

The search endpoint looks promising for XSS testing. Let me send it to Burp Intruder with XSS payloads...

[Tool: burp_send_to_intruder]
Configured Intruder attack on request #3 with 50 XSS payloads targeting the 'q' parameter.

Running attack...

Results: 1 payload triggered reflection without encoding!

🎯 FINDING: Reflected XSS
- URL: https://app.acmecorp.com/search
- Parameter: q
- Payload: <img src=x onerror=alert(1)>
- Evidence: Payload reflected in <div class="results"> without encoding

I've sent this request to Burp Repeater (tab #3) for you to verify manually.

Would you like me to:
1. Test other parameters for XSS
2. Check for stored XSS in form submissions
3. Move on to SQL injection testing

You: Yes, test the product search for SQL injection

Agent: ...
```

## Command Examples

### General Testing
```
You: Test https://app.example.com for XSS and SQL injection

You: Login to app.example.com and crawl the application

You: Test all form inputs for command injection

You: Check the API endpoints for authentication bypass
```

### Specific Vulnerability Testing
```
You: Test the 'id' parameter in /user/profile for IDOR

You: Check if the /api/admin endpoint has proper authorization

You: Test the file upload for malicious file execution

You: Use Burp Collaborator to test for blind SSRF in the url parameter
```

### Context-Based Testing
```
You: I found XSS in /search?q= in version 1.2 which was supposedly fixed. Retest it.

You: Here's the previous pentest report. Check if these issues are still present:
[paste findings]
```

## What Claude Can Do

✅ Navigate to URLs (through Burp proxy)
✅ Login with username/password + optional TOTP
✅ Click elements and fill forms
✅ Send requests to Burp Repeater
✅ Run Burp Intruder attacks with custom payloads
✅ Generate Burp Collaborator payloads
✅ Check Burp Collaborator interactions
✅ Query proxy history
✅ Take screenshots
✅ Test for: XSS, SQLi, Command Injection, SSRF, IDOR, etc.

## What Claude Cannot Do

❌ Test URLs not in scope (will be blocked)
❌ Bypass safety controls
❌ Run attacks without using Burp tools
❌ Access files outside the project directory

## Tips for Effective Testing

1. **Be Specific**: "Test the search parameter for XSS" is better than "test for XSS"
2. **One Thing at a Time**: Focus on one vulnerability type or endpoint
3. **Review Findings**: Always verify findings manually in Burp
4. **Use Context**: Tell Claude about previously found vulnerabilities
5. **Ask Questions**: "What should I test next?" or "Explain this finding"

## Troubleshooting

### "Burp MCP connection failed"
- Make sure `npx -y @burp-suite-mcp/server` is running
- Check Burp Suite Professional is open

### "Scope validation failed"
- Verify the URL is in `scope.hosts` in engagement_manifest.yaml
- Check for typos in the host name

### "Login failed"
- Verify credentials in `.env`
- Check if the login form uses different selectors (you may need to customize the browser adapter)
- Try logging in manually first to see the flow

### "Browser not connecting through proxy"
- Verify Burp proxy is listening on 127.0.0.1:8080
- Check Burp's proxy history to see if requests are coming through

### "Module not found" errors
- Make sure you ran `pip install -e .`
- Check you're using the virtual environment: `source venv/bin/activate` (or `venv\Scripts\activate` on Windows)

## Audit Trail

Every action is logged to `audit_trail/interactive-<pid>_<timestamp>.jsonl`

Check it to see:
- Every URL navigated
- Every tool called
- Every finding
- Timestamps and risk levels

## Safety Features

- ✅ **Scope validation**: Every URL checked before navigation
- ✅ **Audit logging**: Every action logged
- ✅ **Secrets masking**: Passwords/tokens never in logs
- ✅ **Engagement manifest**: Authorization required
- ✅ **All attacks via Burp**: No direct exploitation

## Getting Help

1. Read the README.md
2. Check QUICKSTART.md
3. Look at examples in this file
4. Check audit logs for errors
5. Try asking Claude: "Help me test for SQL injection" or "What should I do next?"

---

**Remember**: This tool is for AUTHORIZED security testing only!
