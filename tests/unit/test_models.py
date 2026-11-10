"""Tests for data models."""

from datetime import date

import pytest
from pydantic import ValidationError

from aipentester.models.engagement import (
    CredentialSource,
    Credentials,
    EngagementInfo,
    MFAMode,
    Scope,
)


class TestEngagementInfo:
    """Tests for EngagementInfo model."""

    def test_valid_engagement_info(self) -> None:
        """Test valid engagement info."""
        info = EngagementInfo(
            name="Test",
            id="TEST-001",
            authorized_by="CISO",
            analyst_name="Analyst",
            analyst_email="analyst@test.com",
            start_date=date(2024, 1, 1),
            end_date=date(2024, 12, 31),
            authorization_acknowledgement="Confirmed",
        )
        assert info.name == "Test"
        assert info.is_active()

    def test_invalid_date_range(self) -> None:
        """Test end_date before start_date is rejected."""
        with pytest.raises(ValidationError, match="end_date must be after start_date"):
            EngagementInfo(
                name="Test",
                id="TEST-001",
                authorized_by="CISO",
                analyst_name="Analyst",
                analyst_email="analyst@test.com",
                start_date=date(2024, 12, 31),
                end_date=date(2024, 1, 1),
                authorization_acknowledgement="Confirmed",
            )

    def test_is_expired(self) -> None:
        """Test is_expired check."""
        info = EngagementInfo(
            name="Test",
            id="TEST-001",
            authorized_by="CISO",
            analyst_name="Analyst",
            analyst_email="analyst@test.com",
            start_date=date(2020, 1, 1),
            end_date=date(2020, 12, 31),
            authorization_acknowledgement="Confirmed",
        )
        assert info.is_expired()


class TestScope:
    """Tests for Scope model."""

    def test_valid_scope(self) -> None:
        """Test valid scope."""
        scope = Scope(
            hosts=["example.com"],
            max_request_rate=10,
        )
        assert len(scope.hosts) == 1

    def test_empty_hosts_rejected(self) -> None:
        """Test empty hosts list is rejected."""
        with pytest.raises(ValidationError):
            Scope(hosts=[])

    def test_is_host_in_scope(self) -> None:
        """Test host scope checking."""
        scope = Scope(
            hosts=["example.com", "*.test.com"],
        )
        assert scope.is_host_in_scope("example.com")
        assert scope.is_host_in_scope("app.test.com")
        assert not scope.is_host_in_scope("attacker.com")

    def test_is_path_excluded(self) -> None:
        """Test path exclusion checking."""
        scope = Scope(
            hosts=["example.com"],
            excluded_paths=["/admin", "/api/internal"],
        )
        assert scope.is_path_excluded("/admin/users")
        assert scope.is_path_excluded("/api/internal/metrics")
        assert not scope.is_path_excluded("/api/public/data")


class TestCredentials:
    """Tests for Credentials model."""

    def test_valid_env_credentials(self) -> None:
        """Test valid env credentials."""
        creds = Credentials(
            source=CredentialSource.ENV,
            env_vars={"username": "USER", "password": "PASS"},
        )
        assert creds.source == CredentialSource.ENV

    def test_env_credentials_require_username_and_password(self) -> None:
        """Test env credentials require both username and password."""
        with pytest.raises(
            ValidationError, match="username and password env_vars required"
        ):
            Credentials(
                source=CredentialSource.ENV,
                env_vars={"username": "USER"},
            )

    def test_keyring_credentials(self) -> None:
        """Test keyring credentials."""
        creds = Credentials(
            source=CredentialSource.KEYRING,
            mfa_mode=MFAMode.TOTP,
        )
        assert creds.source == CredentialSource.KEYRING
        assert creds.mfa_mode == MFAMode.TOTP
