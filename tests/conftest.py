"""Pytest configuration and fixtures."""

from datetime import date, datetime
from pathlib import Path

import pytest

from aipentester.models.engagement import (
    Credentials,
    CredentialSource,
    EngagementInfo,
    EngagementManifest,
    Evidence,
    MFAMode,
    Safety,
    Scope,
)


@pytest.fixture
def sample_engagement_info() -> EngagementInfo:
    """Sample engagement info for testing."""
    return EngagementInfo(
        name="Test Engagement",
        id="TEST-2024-001",
        authorized_by="Test CISO",
        analyst_name="Test Analyst",
        analyst_email="analyst@test.com",
        start_date=date(2024, 1, 1),
        end_date=date(2024, 12, 31),
        authorization_acknowledgement="I confirm authorization",
    )


@pytest.fixture
def sample_scope() -> Scope:
    """Sample scope for testing."""
    return Scope(
        hosts=["example.com", "*.example.com"],
        excluded_paths=["/admin/critical"],
        max_request_rate=5,
        courtesy_delay_ms=200,
    )


@pytest.fixture
def sample_credentials() -> Credentials:
    """Sample credentials config for testing."""
    return Credentials(
        source=CredentialSource.ENV,
        env_vars={"username": "TEST_USER", "password": "TEST_PASS"},
        mfa_mode=MFAMode.NONE,
    )


@pytest.fixture
def sample_manifest(
    sample_engagement_info: EngagementInfo,
    sample_scope: Scope,
    sample_credentials: Credentials,
) -> EngagementManifest:
    """Sample engagement manifest for testing."""
    return EngagementManifest(
        engagement=sample_engagement_info,
        scope=sample_scope,
        credentials=sample_credentials,
        approved_categories=["xss", "sqli", "authz"],
        safety=Safety(),
        evidence=Evidence(),
    )


@pytest.fixture
def temp_project_dir(tmp_path: Path) -> Path:
    """Temporary project directory for testing."""
    project_dir = tmp_path / "test_project"
    project_dir.mkdir()
    return project_dir
