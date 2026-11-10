# AIPentester Quick Setup Guide

## What You Need

✅ **Already installed:**
- AIPentester (this tool)
- Python virtual environment with dependencies
- Claude Code configured

🔲 **Still need:**
- Burp Suite Professional
- Burp MCP Server extension

---

## Step 1: Install Burp MCP Extension

### Option A: Via BApp Store (Easiest)

1. **Open Burp Suite Professional**
2. **Go to:** Extensions → BApp Store
3. **Search for:** "MCP Server"
4. **Click:** Install

### Option B: Build from Source (if needed)

```bash
# Install Java 21
brew install openjdk@21

# Build the extension
cd /Users/nayan/Documents/Code/burp-mcp-server
./gradlew embedProxyJar

# Load build/libs/burp-mcp-all.jar into Burp Suite:
# Extensions → Add → Java → Select JAR file
```

---

## Step 2: Configure Burp MCP Extension

1. **In Burp Suite, go to:** MCP tab
2. **Enable the server:** Check "Enabled"
3. **Note the URL:** Default is `http://127.0.0.1:9876`
4. **Make sure Burp Proxy is running:** 127.0.0.1:8080

---

## Step 3: Update Engagement Manifest

Edit `engagement_manifest.yaml`:

```yaml
scope:
  hosts:
    - "credify.tech"      # ← Your target
    - "*.credify.tech"
```

Update credentials if needed:

```yaml
credentials:
  env_vars:
    username: is.test@credify.tech
    password: Welcome@123
```

---

## Step 4: Test the Setup

### Test Burp MCP Connection

```bash
curl http://127.0.0.1:9876/health
# Should return: OK or 200 status
```

### Test AIPentester MCP Server

```bash
cd /Users/nayan/Documents/Code/AIPentester
venv/bin/python run_mcp_server.py
```

Should wait for input (that's correct - it's listening for MCP protocol messages).
Press Ctrl+C to exit.

---

## Step 5: Restart Claude Code

```bash
# Exit Claude Code if running (Ctrl+D)
# Start it again
claude
```

---

## Step 6: Verify Tools Are Available

In Claude Code, ask:

```
> What pentesting tools do you have access to?
```

You should see:
- `browser_navigate`
- `browser_login`
- `browser_screenshot`
- `burp_get_proxy_history`
- `burp_send_to_repeater`
- `burp_send_to_intruder`
- `burp_collaborator_generate`
- `burp_collaborator_check`

---

## Step 7: Start Pentesting!

Example commands:

```
> Navigate to https://credify.tech

> Login using the credentials from the manifest

> Check the proxy history

> Test the search parameter for XSS

> Send the login request to Burp Repeater
```

---

## Troubleshooting

### Claude doesn't see the tools

**Check:** `~/.config/claude-code/config.json` has:

```json
{
  "mcpServers": {
    "aipentester": {
      "command": "/Users/nayan/Documents/Code/AIPentester/venv/bin/python",
      "args": ["/Users/nayan/Documents/Code/AIPentester/run_mcp_server.py"],
      "env": {
        "AIPENTESTER_MANIFEST": "/Users/nayan/Documents/Code/AIPentester/engagement_manifest.yaml",
        "BURP_PROXY_HOST": "127.0.0.1",
        "BURP_PROXY_PORT": "8080",
        "BURP_MCP_HOST": "127.0.0.1",
        "BURP_MCP_PORT": "9876"
      }
    }
  }
}
```

**Then restart Claude Code.**

### "Burp connection failed"

1. Is Burp Suite running?
2. Is the MCP extension enabled in Burp? (Check MCP tab)
3. Is it listening on 127.0.0.1:9876? (Check MCP tab settings)
4. Test: `curl http://127.0.0.1:9876/health`

### "Scope validation failed"

1. Edit `engagement_manifest.yaml`
2. Add your target to `scope.hosts`
3. Restart Claude Code

### Browser won't start

```bash
playwright install chromium
```

---

## Architecture Overview

```
┌──────────────┐
│ You          │  "Test for XSS"
│ (Terminal)   │
└──────┬───────┘
       │
┌──────▼───────┐
│ Claude Code  │  Uses MCP tools
└──────┬───────┘
       │
┌──────▼───────┐
│ AIPentester  │  MCP Server (run_mcp_server.py)
│              │  Exposes 8 tools to Claude
└──┬────────┬──┘
   │        │
   │    ┌───▼──────┐
   │    │ Burp MCP │  http://127.0.0.1:9876
   │    │ Extension│  Repeater, Intruder, Collaborator
   │    └──────────┘
   │
┌──▼────────┐
│ Browser   │  Playwright + Burp Proxy (8080)
│ (Chromium)│
└───────────┘
```

---

**You're ready to pentest with Claude! 🚀**
