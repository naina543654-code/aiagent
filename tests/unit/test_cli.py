"""Tests for CLI commands (validate-scope, plan)."""

from pathlib import Path

import yaml
from typer.testing import CliRunner

from aipentester.cli.main import app
from aipentester.models.engagement import EngagementManifest

runner = CliRunner()


def _write_manifest(tmp_path: Path, manifest: EngagementManifest) -> Path:
    path = tmp_path / "engagement_manifest.yaml"
    path.write_text(yaml.safe_dump(manifest.model_dump(mode="json")))
    return path


def test_validate_scope_passes(sample_manifest: EngagementManifest, tmp_path: Path) -> None:
    """validate-scope exits 0 for an active, authorized manifest."""
    manifest_path = _write_manifest(tmp_path, sample_manifest)
    result = runner.invoke(app, ["validate-scope", "--manifest", str(manifest_path)])
    assert result.exit_code == 0, result.output
    assert "Scope validation passed" in result.output
    assert "example.com" in result.output


def test_validate_scope_missing_manifest(tmp_path: Path) -> None:
    """validate-scope exits 1 when the manifest file does not exist."""
    result = runner.invoke(
        app, ["validate-scope", "--manifest", str(tmp_path / "nope.yaml")]
    )
    assert result.exit_code == 1
    assert "not found" in result.output


def test_plan_writes_assessment_plan(
    sample_manifest: EngagementManifest, tmp_path: Path, monkeypatch
) -> None:
    """plan writes a markdown assessment plan under reports/."""
    manifest_path = _write_manifest(tmp_path, sample_manifest)
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["plan", "--manifest", str(manifest_path)])
    assert result.exit_code == 0, result.output

    plan_path = tmp_path / "reports" / "assessment_plan.md"
    assert plan_path.exists()
    content = plan_path.read_text()
    assert "Test Engagement" in content
    assert "example.com" in content
    assert "Reconnaissance" in content
    assert "xss" in content


def test_plan_invalid_mode(
    sample_manifest: EngagementManifest, tmp_path: Path
) -> None:
    """plan rejects an unknown --mode."""
    manifest_path = _write_manifest(tmp_path, sample_manifest)
    result = runner.invoke(
        app, ["plan", "--mode", "bogus", "--manifest", str(manifest_path)]
    )
    assert result.exit_code == 1
    assert "invalid mode" in result.output


def test_help_lists_new_commands() -> None:
    """--help shows validate-scope and plan."""
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "validate-scope" in result.output
    assert "plan" in result.output
