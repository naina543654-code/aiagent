"""Tests for the audit criticals + quick wins (FIXES.md §14).

C1: pentest_run_autonomous must scope-check before any recon runs.
C2: the `pentest` MCP tool must initialise the browser (it matches neither
    the "browser_" nor the "pentest_" prefix).
C3: credentials must never reach the audit log in cleartext.
C4: bare print() must not remain in MCP-reachable modules (stdout is the
    MCP transport); formerly-printing code must keep stdout empty.
C5: nikto scans must receive the computed port (not the port-80 default).
C6: the Burp proxy port must be 8080 everywhere (no 8081 stragglers).
"""

import ast
import inspect
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import yaml

from aipentester import mcp_server
from aipentester.models.engagement import EngagementManifest
from aipentester.pentest import PentestOrchestrator, PentestState
from aipentester.safety import AuditLogger, ScopeValidator
from aipentester.safety.secrets_manager import SecretsManager
from aipentester.simple_pentest import SimplePentest

REPO_ROOT = Path(__file__).resolve().parents[2]
SECRET_PASSWORD = "s3cr3t-p4ssw0rd!"
SECRET_TOTP = "JBSWY3DPEHPK3PXP"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _set_mcp_globals(monkeypatch, manifest: EngagementManifest) -> None:
    """Point the MCP server module at a test manifest (no file loading)."""
    monkeypatch.setattr(mcp_server, "manifest", manifest)
    monkeypatch.setattr(mcp_server, "scope_validator", ScopeValidator(manifest))
    monkeypatch.setattr(mcp_server, "audit_logger", None)


def _mock_scanners(monkeypatch) -> tuple[AsyncMock, AsyncMock]:
    """Stub the module-level nmap/nikto scanners with canned results."""
    nmap = AsyncMock()
    nmap.quick_scan.return_value = {"hosts": []}
    nmap.format_results.return_value = "nmap: no open ports"
    nikto = AsyncMock()
    nikto.quick_scan.return_value = {"vulnerabilities": []}
    nikto.format_results.return_value = "nikto: no issues"
    monkeypatch.setattr(mcp_server, "nmap_scanner", nmap)
    monkeypatch.setattr(mcp_server, "nikto_scanner", nikto)
    return nmap, nikto


def _mock_browser_spider_threat(monkeypatch) -> None:
    """Stub browser/spider/threat-analyzer so no real browser launches."""
    monkeypatch.setattr(mcp_server, "browser", MagicMock())
    spider = AsyncMock()
    spider.map_application.return_value = {
        "total_pages": 2,
        "form_count": 1,
        "api_endpoints": [],
    }
    monkeypatch.setattr(mcp_server, "spider", spider)
    threat = MagicMock()
    threat.generate_test_plan.return_value = {
        "total_threats": 0,
        "all_threats": [],
        "by_risk": {"critical": [], "high": [], "medium": []},
    }
    monkeypatch.setattr(mcp_server, "threat_analyzer", threat)


# ---------------------------------------------------------------------------
# C1 — autonomous-tool scope bypass
# ---------------------------------------------------------------------------


async def test_autonomous_out_of_scope_refused_before_recon(
    sample_manifest: EngagementManifest, monkeypatch
) -> None:
    """Out-of-scope start_url is refused and nmap/nikto never run (C1)."""
    _set_mcp_globals(monkeypatch, sample_manifest)
    nmap, nikto = _mock_scanners(monkeypatch)
    _mock_browser_spider_threat(monkeypatch)

    result = await mcp_server.call_tool(
        "pentest_run_autonomous", {"start_url": "https://evil.example/"}
    )
    text = result[0]["text"]
    assert "not in scope" in text
    assert "evil.example" in text
    nmap.quick_scan.assert_not_called()
    nikto.quick_scan.assert_not_called()
    mcp_server.spider.map_application.assert_not_called()


async def test_autonomous_in_scope_runs_recon_with_port(
    sample_manifest: EngagementManifest, monkeypatch
) -> None:
    """In-scope https start_url reaches recon, nikto on port 443 (C1+C5)."""
    _set_mcp_globals(monkeypatch, sample_manifest)
    nmap, nikto = _mock_scanners(monkeypatch)
    _mock_browser_spider_threat(monkeypatch)

    result = await mcp_server.call_tool(
        "pentest_run_autonomous", {"start_url": "https://example.com/app"}
    )
    text = result[0]["text"]
    assert "Autonomous scan complete" in text
    nmap.quick_scan.assert_awaited_once()
    nikto.quick_scan.assert_awaited_once()
    args, kwargs = nikto.quick_scan.call_args
    assert args[0] == "example.com"
    assert kwargs["port"] == 443
    assert kwargs["ssl"] is True


async def test_autonomous_http_uses_port_80(
    sample_manifest: EngagementManifest, monkeypatch
) -> None:
    """In-scope http start_url reaches nikto on port 80 (C5)."""
    _set_mcp_globals(monkeypatch, sample_manifest)
    _, nikto = _mock_scanners(monkeypatch)
    _mock_browser_spider_threat(monkeypatch)

    await mcp_server.call_tool(
        "pentest_run_autonomous", {"start_url": "http://example.com/app"}
    )
    _, kwargs = nikto.quick_scan.call_args
    assert kwargs["port"] == 80
    assert kwargs["ssl"] is False


# ---------------------------------------------------------------------------
# C2 — `pentest` tool browser initialisation
# ---------------------------------------------------------------------------


def test_browser_tool_set_covers_exact_pentest_tool() -> None:
    """The browser-needing set lists `pentest` explicitly (C2)."""
    assert "pentest" in mcp_server._BROWSER_TOOLS
    assert {
        "pentest",
        "pentest_crawl_application",
        "pentest_run_autonomous",
        "pentest_interactive_explore_and_test",
    } == mcp_server._BROWSER_TOOLS


async def test_pentest_tool_initializes_browser(
    sample_manifest: EngagementManifest, monkeypatch
) -> None:
    """call_tool("pentest") constructs the browser before SimplePentest (C2)."""
    _set_mcp_globals(monkeypatch, sample_manifest)
    monkeypatch.setattr(mcp_server, "browser", None)

    adapter_instance = AsyncMock()
    adapter_cls = MagicMock(return_value=adapter_instance)
    monkeypatch.setattr(mcp_server, "BrowserUseAdapter", adapter_cls)

    pentest_instance = AsyncMock()
    pentest_instance.run.return_value = {
        "target": "https://example.com/",
        "authenticated": False,
        "phases_completed": ["recon"],
        "exploration": {"urls": [], "interaction_count": 0},
        "attack_scenarios": [],
        "vulnerabilities": [],
        "errors": [],
    }
    pentest_cls = MagicMock(return_value=pentest_instance)
    monkeypatch.setattr(mcp_server, "SimplePentest", pentest_cls)

    result = await mcp_server.call_tool(
        "pentest",
        {
            "target": "https://example.com/",
            "username": "tester",
            "password": SECRET_PASSWORD,
        },
    )
    assert "PENETRATION TEST RESULTS" in result[0]["text"]
    adapter_cls.assert_called_once()
    adapter_instance.initialize.assert_awaited_once()
    # SimplePentest received the freshly created browser, not None.
    pentest_cls.assert_called_once()
    (browser_arg,) = pentest_cls.call_args.args[:1]
    assert browser_arg is adapter_instance


# ---------------------------------------------------------------------------
# C3 — credentials in cleartext in logs
# ---------------------------------------------------------------------------


def test_redact_tool_arguments_masks_credentials() -> None:
    """_redact_tool_arguments keeps names/URLs but masks secrets (C3)."""
    redacted = mcp_server._redact_tool_arguments(
        {
            "username": "tester",
            "password": SECRET_PASSWORD,
            "totp_secret": SECRET_TOTP,
            "url": "https://example.com/login",
        }
    )
    assert redacted["username"] == "tester"
    assert redacted["url"] == "https://example.com/login"
    assert redacted["password"] == "***REDACTED***"
    assert redacted["totp_secret"] == "***REDACTED***"
    assert SECRET_PASSWORD not in str(redacted)
    assert SECRET_TOTP not in str(redacted)


def test_audit_logger_masks_credentials_in_file(tmp_path: Path) -> None:
    """AuditLogger's own file never contains a logged password (C3)."""
    logger = AuditLogger(str(tmp_path), "test-c3")
    logger.log_error(
        "tool_error",
        "boom",
        {
            "tool": "browser_login",
            "arguments": {"username": "tester", "password": SECRET_PASSWORD},
        },
    )
    logger.log_action(
        "browser_navigate",
        f"https://example.com/?token={SECRET_TOTP}",
        details={"password": SECRET_PASSWORD},
    )
    content = logger.get_log_file_path().read_text()
    assert SECRET_PASSWORD not in content
    assert SECRET_TOTP not in content
    assert "***REDACTED***" in content


async def test_agent_execute_tool_redacts_credentials(
    sample_manifest: EngagementManifest, monkeypatch
) -> None:
    """PentestAgent's tool-call log carries no password (C3)."""
    from aipentester.agent import PentestAgent  # local import: heavy deps

    agent = PentestAgent.__new__(PentestAgent)
    agent.secrets_manager = SecretsManager()
    audit_logger = MagicMock()
    agent.audit_logger = audit_logger
    agent.browser = MagicMock()
    agent._tool_browser_login = AsyncMock(return_value="Login successful")

    result = await agent._execute_tool(
        "browser_login", {"username": "tester", "password": SECRET_PASSWORD}
    )
    assert result == "Login successful"
    audit_logger.log_action.assert_called_once()
    _, kwargs = audit_logger.log_action.call_args
    assert SECRET_PASSWORD not in kwargs["target"]
    assert "***REDACTED***" in kwargs["target"]
    assert "tester" in kwargs["target"]


async def test_mcp_tool_error_path_redacts_arguments(
    sample_manifest: EngagementManifest, monkeypatch, tmp_path: Path
) -> None:
    """A tool error still writes an audit line, minus the password (C3)."""
    _set_mcp_globals(monkeypatch, sample_manifest)
    logger = AuditLogger(str(tmp_path), "test-c3-mcp")
    monkeypatch.setattr(mcp_server, "audit_logger", logger)
    monkeypatch.setattr(mcp_server, "browser", MagicMock())

    # browser_navigate with no "url" key raises KeyError inside call_tool.
    result = await mcp_server.call_tool(
        "browser_navigate",
        {"username": "tester", "password": SECRET_PASSWORD},
    )
    assert "Error:" in result[0]["text"]
    content = logger.get_log_file_path().read_text()
    assert SECRET_PASSWORD not in content
    assert "browser_navigate" in content


# ---------------------------------------------------------------------------
# C4 — stdout must stay clean under MCP
# ---------------------------------------------------------------------------


def test_no_bare_print_in_mcp_reachable_modules() -> None:
    """No bare print() remains in the five converted modules (C4)."""
    modules = [
        "src/aipentester/simple_pentest.py",
        "src/aipentester/browser/browser_use_adapter.py",
        "src/aipentester/crawler/vision_crawler.py",
        "src/aipentester/pentest/test_executor.py",
        "src/aipentester/burp/burp_mcp_client.py",
    ]
    for rel in modules:
        tree = ast.parse((REPO_ROOT / rel).read_text())
        prints = [
            node
            for node in ast.walk(tree)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "print"
        ]
        assert prints == [], f"bare print() still present in {rel}"


async def test_simple_pentest_keeps_stdout_empty(capsys) -> None:
    """A formerly-printing SimplePentest path writes nothing to stdout (C4)."""
    pentest = SimplePentest(MagicMock(), MagicMock(), MagicMock())
    scenarios = await pentest._generate_attacks_from_burp({"urls": []})
    assert scenarios == []
    captured = capsys.readouterr()
    assert captured.out == ""


# ---------------------------------------------------------------------------
# C5 — nikto port (orchestrator + CLI)
# ---------------------------------------------------------------------------


async def test_orchestrator_recon_passes_port(
    sample_manifest: EngagementManifest,
) -> None:
    """Orchestrator recon passes the URL's port to nikto (C5)."""
    from aipentester.safety import ScopeValidator as _SV

    orchestrator = PentestOrchestrator(
        scope_validator=_SV(sample_manifest),
        audit_logger=MagicMock(),
        approved_categories=["xss"],
    )
    orchestrator.nmap_scanner = AsyncMock()
    orchestrator.nmap_scanner.quick_scan.return_value = {"hosts": []}
    orchestrator.nikto_scanner = AsyncMock()
    orchestrator.nikto_scanner.quick_scan.return_value = {"vulnerabilities": []}
    state = PentestState(target_url="https://example.com:8443/app")

    await orchestrator._run_reconnaissance("https://example.com:8443/app", state)
    _, kwargs = orchestrator.nikto_scanner.quick_scan.call_args
    assert kwargs["port"] == 8443
    assert kwargs["ssl"] is True


async def test_cli_nikto_scan_passes_port(
    sample_manifest: EngagementManifest, tmp_path: Path, monkeypatch
) -> None:
    """CLI _nikto_scan passes its port to quick_scan and full_scan (C5)."""
    from aipentester.cli.commands import recon as recon_cmd

    monkeypatch.chdir(tmp_path)
    manifest_path = tmp_path / "engagement_manifest.yaml"
    manifest_path.write_text(
        yaml.safe_dump(sample_manifest.model_dump(mode="json"))
    )

    scanner = AsyncMock()
    scanner.quick_scan.return_value = {}
    scanner.full_scan.return_value = {}
    # format_results is called synchronously by _nikto_scan, so it must be
    # a plain MagicMock — an AsyncMock child would create an un-awaited
    # coroutine (and the "done" string would be a coroutine object).
    scanner.format_results = MagicMock(return_value="done")
    monkeypatch.setattr(recon_cmd, "NiktoScanner", lambda: scanner)

    await recon_cmd._nikto_scan("example.com", 8443, True, "quick", str(manifest_path))
    _, kwargs = scanner.quick_scan.call_args
    assert kwargs == {"port": 8443, "ssl": True}
    scanner.quick_scan.reset_mock()

    await recon_cmd._nikto_scan("example.com", 8080, False, "full", str(manifest_path))
    _, kwargs = scanner.full_scan.call_args
    assert kwargs == {"port": 8080, "ssl": False}


def test_cli_pentest_passes_port_to_nikto() -> None:
    """CLI pentest's nikto call includes port= (C5, source-level check)."""
    tree = ast.parse(
        (REPO_ROOT / "src/aipentester/cli/commands/pentest.py").read_text()
    )
    nikto_calls = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "quick_scan"
        and any(isinstance(t, ast.Name) and t.id == "nikto_scanner" for t in [node.func.value])
    ]
    assert nikto_calls, "no nikto quick_scan call found in cli pentest"
    for call in nikto_calls:
        assert any(kw.arg == "port" for kw in call.keywords), (
            "nikto quick_scan without port= in cli/commands/pentest.py"
        )


# ---------------------------------------------------------------------------
# C6 — proxy port 8080 everywhere
# ---------------------------------------------------------------------------


def test_orchestrator_default_proxy_port_is_8080() -> None:
    """PentestOrchestrator.initialize defaults to Burp's 8080 (C6)."""
    params = inspect.signature(PentestOrchestrator.initialize).parameters
    assert params["proxy_port"].default == 8080


async def test_orchestrator_initialize_uses_port_8080(
    sample_manifest: EngagementManifest, monkeypatch
) -> None:
    """initialize() with no args hands 8080 to the browser adapter (C6)."""
    import aipentester.pentest.orchestrator as orch_mod

    orchestrator = PentestOrchestrator(
        scope_validator=ScopeValidator(sample_manifest),
        audit_logger=MagicMock(),
        approved_categories=["xss"],
    )
    browser_cls = MagicMock()
    browser_cls.return_value.initialize = AsyncMock()
    monkeypatch.setattr(orch_mod, "BrowserUseAdapter", browser_cls)
    monkeypatch.setattr(orch_mod, "IntelligentSpider", MagicMock())
    monkeypatch.setattr(orch_mod, "NmapScanner", MagicMock())
    monkeypatch.setattr(orch_mod, "NiktoScanner", MagicMock())
    monkeypatch.setattr(orch_mod, "ThreatAnalyzer", MagicMock())

    await orchestrator.initialize()
    browser_cls.assert_called_once()
    _, kwargs = browser_cls.call_args
    assert kwargs["proxy_port"] == 8080


def test_no_8081_anywhere_in_source() -> None:
    """No 8081 stragglers remain in the Python source (C6)."""
    offenders = [
        str(p)
        for p in (REPO_ROOT / "src").rglob("*.py")
        if "8081" in p.read_text()
    ]
    assert offenders == [], f"8081 still present in: {offenders}"


# ---------------------------------------------------------------------------
# Regression: recon handlers still scope-check (pattern FIX 1 follows)
# ---------------------------------------------------------------------------


async def test_recon_handlers_still_scope_check(
    sample_manifest: EngagementManifest, monkeypatch
) -> None:
    """Recon tools still refuse out-of-scope targets (unchanged behaviour)."""
    _set_mcp_globals(monkeypatch, sample_manifest)
    nmap, _ = _mock_scanners(monkeypatch)
    result = await mcp_server.call_tool(
        "recon_nmap_quick_scan", {"target": "evil.example"}
    )
    assert "not in scope" in result[0]["text"]
    nmap.quick_scan.assert_not_called()
