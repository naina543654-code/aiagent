"""Regression: nmap scan is removed — no MCP tool, no CLI command, no class."""

import pytest


def test_no_nmap_mcp_tools():
    from aipentester.mcp_server import TOOLS

    names = [t.name for t in TOOLS]
    assert len(names) == 14, names
    assert not any("nmap" in n for n in names)


def test_no_nmap_scanner_class():
    with pytest.raises(ImportError):
        from aipentester.recon import NmapScanner  # noqa: F401


def test_cli_recon_has_no_nmap_commands():
    from typer.testing import CliRunner

    from aipentester.cli.commands.recon import recon

    result = CliRunner().invoke(recon, ["--help"])
    assert "nmap" not in result.output.lower()
