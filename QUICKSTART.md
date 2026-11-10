# Quick Start Guide

## 5-Minute Setup

### 1. Install

```bash
cd AIPentester
pip install -e .
playwright install chromium
```

### 2. Initialize

```bash
aipentester init
```

### 3. Configure

Edit `engagement_manifest.yaml`:

```yaml
engagement:
  name: "My Test"
  id: "TEST-001"
  authorized_by: "Your CISO"
  analyst_name: "Your Name"
  analyst_email: "you@example.com"
  start_date: "2024-01-01"
  end_date: "2024-12-31"
  authorization_acknowledgement: "I have authorization"

scope:
  hosts:
    - "yourapp.example.com"
```

Edit `.env`:

```bash
ANTHROPIC_API_KEY=sk-ant-your-key-here
TEST_APP_USERNAME=testuser
TEST_APP_PASSWORD=testpass
```

### 4. Start Burp

```bash
# Terminal 1: Start Burp MCP server
npx -y @burp-suite-mcp/server

# Make sure Burp Suite Pro is running with proxy on 127.0.0.1:8080
```

### 5. Chat!

```bash
#Terminal 2: Start chat
aipentester chat
```

## Example Commands

```
You: Login to https://yourapp.example.com and test for XSS

You: Check the search parameter for SQL injection

You: Use Burp Collaborator to test for SSRF in the URL parameter

You: Test all form inputs for command injection
```

## What Claude Can Do

✅ Navigate and login to apps
✅ Send requests to Burp Repeater
✅ Run Burp Intruder attacks
✅ Use Burp Collaborator
✅ Analyze proxy history
✅ Test for: XSS, SQLi, Command Injection, SSRF, IDOR, etc.

## What Claude Cannot Do

❌ Test targets not in scope
❌ Perform attacks without Burp
❌ Use Browser Use to inject payloads (only for browsing)
❌ Disable safety controls

---

**Remember**: You're chatting with Claude. Be specific about what you want tested!
