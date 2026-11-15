"""Tests for all-traffic-through-Burp: proxy helper + proxied curl."""

import os

import pytest

from aipentester.pentest.poc_generator import POCGenerator, Threat
from aipentester.safety.burp_proxy import (
    check_burp_reachable,
    curl_proxy_args,
    ensure_burp_proxy_env,
    proxies_dict,
    proxied_curl_command,
    proxy_url,
    require_burp,
)


def test_proxy_url_default(monkeypatch):
    monkeypatch.delenv("BURP_PROXY_HOST", raising=False)
    monkeypatch.delenv("BURP_PROXY_PORT", raising=False)
    assert proxy_url() == "http://127.0.0.1:8080"


def test_proxy_url_env_override(monkeypatch):
    monkeypatch.setenv("BURP_PROXY_HOST", "10.0.0.5")
    monkeypatch.setenv("BURP_PROXY_PORT", "9090")
    assert proxy_url() == "http://10.0.0.5:9090"


def test_proxies_dict_and_curl_args():
    assert proxies_dict() == {
        "http": "http://127.0.0.1:8080",
        "https": "http://127.0.0.1:8080",
    }
    assert curl_proxy_args() == ["-x", "http://127.0.0.1:8080"]
    cmd = proxied_curl_command("http://127.0.0.1:10015/search?q=test")
    assert '-x http://127.0.0.1:8080' in cmd
    assert "127.0.0.1:10015/search" in cmd


def test_ensure_burp_proxy_env_sets_proxy_and_clears_no_proxy(monkeypatch):
    monkeypatch.setenv("NO_PROXY", "127.0.0.1,localhost")
    monkeypatch.setenv("no_proxy", "localhost")
    monkeypatch.delenv("HTTP_PROXY", raising=False)
    ensure_burp_proxy_env()
    assert os.environ["HTTP_PROXY"] == "http://127.0.0.1:8080"
    assert os.environ["HTTPS_PROXY"] == "http://127.0.0.1:8080"
    assert os.environ["http_proxy"] == "http://127.0.0.1:8080"
    assert "NO_PROXY" not in os.environ
    assert "no_proxy" not in os.environ


def test_poc_generator_xss_curl_goes_through_burp():
    gen = POCGenerator()
    threat = Threat(
        category="xss",
        endpoint="http://127.0.0.1:10015/search",
        parameter="q",
        risk_level="high",
        description="Reflected XSS",
        attack_vector="GET",
        test_payloads=["<script>alert(1)</script>"],
    )
    curl = gen._generate_xss_curl(threat)
    assert "-x http://127.0.0.1:8080" in curl


def test_require_burp_fails_when_burp_down(monkeypatch):
    # Point at a port nothing listens on — must fail fast, not silently pass.
    monkeypatch.setenv("BURP_PROXY_HOST", "127.0.0.1")
    monkeypatch.setenv("BURP_PROXY_PORT", "1")
    assert check_burp_reachable(timeout=0.5) is False
    with pytest.raises(ConnectionError, match="Burp proxy not reachable"):
        require_burp()


def test_all_agents_mandate_mcp_only_traffic():
    from pathlib import Path

    agents = list(Path("src/aipentester").parent.glob(".claude/agents/*.md"))
    # Fall back to repo-root relative path when run from elsewhere.
    if not agents:
        agents = list(Path(".claude/agents").glob("*.md"))
    assert len(agents) == 13
    for p in agents:
        text = p.read_text()
        assert "Use ONLY the MCP tools" in text, p.name
        assert "NEVER use Bash `curl`" in text, p.name
