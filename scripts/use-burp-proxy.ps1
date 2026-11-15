# Run this in PowerShell BEFORE starting Claude Code, in the same window:
#   . .\scripts\use-burp-proxy.ps1
# It makes every HTTP request from that session (curl, Python, Claude Code
# subagents) go through Burp on 127.0.0.1:8080 — including loopback targets,
# which Windows/Python skip the proxy for by default.
$env:HTTP_PROXY = "http://127.0.0.1:8080"
$env:HTTPS_PROXY = "http://127.0.0.1:8080"
$env:http_proxy = "http://127.0.0.1:8080"
$env:https_proxy = "http://127.0.0.1:8080"
Remove-Item Env:NO_PROXY -ErrorAction SilentlyContinue
Remove-Item Env:no_proxy -ErrorAction SilentlyContinue
Write-Host "Burp proxy on for this session: HTTP_PROXY=$env:HTTP_PROXY (NO_PROXY cleared)"
