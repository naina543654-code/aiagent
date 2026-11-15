# One command to start Claude Code for an aiagent run — no manual setup.
# Usage, from the project folder (where scope.txt lives):
#   .\scripts\start-claude.ps1
# It sets the Burp proxy for this session (so ALL requests, including
# curl/Python from subagents, go through Burp on 127.0.0.1:8080, loopback
# included) and then starts Claude Code in the current folder.
# Any arguments are passed through to `claude`, e.g.:
#   .\scripts\start-claude.ps1 --model sonnet

$env:HTTP_PROXY = "http://127.0.0.1:8080"
$env:HTTPS_PROXY = "http://127.0.0.1:8080"
$env:http_proxy = "http://127.0.0.1:8080"
$env:https_proxy = "http://127.0.0.1:8080"
Remove-Item Env:NO_PROXY -ErrorAction SilentlyContinue
Remove-Item Env:no_proxy -ErrorAction SilentlyContinue
Write-Host "Burp proxy on for this session. Starting Claude Code..."
& claude @args
