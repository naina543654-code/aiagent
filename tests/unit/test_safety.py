"""Tests for safety controls."""

import pytest

from aipentester.models.engagement import EngagementManifest
from aipentester.safety import ScopeValidator, ScopeViolationError


class TestScopeValidator:
    """Tests for ScopeValidator."""

    def test_in_scope_exact_match(self, sample_manifest: EngagementManifest) -> None:
        """Test exact host match."""
        validator = ScopeValidator(sample_manifest)
        # Should not raise
        validator.validate_url("https://example.com/test")

    def test_in_scope_wildcard(self, sample_manifest: EngagementManifest) -> None:
        """Test wildcard host match."""
        validator = ScopeValidator(sample_manifest)
        # Should not raise
        validator.validate_url("https://app.example.com/test")
        validator.validate_url("https://api.example.com/test")

    def test_out_of_scope_host(self, sample_manifest: EngagementManifest) -> None:
        """Test out-of-scope host is rejected."""
        validator = ScopeValidator(sample_manifest)
        with pytest.raises(ScopeViolationError, match="not in scope"):
            validator.validate_url("https://attacker.com/test")

    def test_excluded_path(self, sample_manifest: EngagementManifest) -> None:
        """Test excluded path is rejected."""
        validator = ScopeValidator(sample_manifest)
        with pytest.raises(ScopeViolationError, match="excluded"):
            validator.validate_url("https://example.com/admin/critical/action")

    def test_validate_host_with_port(self, sample_manifest: EngagementManifest) -> None:
        """Test host validation strips port."""
        validator = ScopeValidator(sample_manifest)
        # Should not raise
        validator.validate_host("example.com:8080")

    def test_case_insensitive_matching(self, sample_manifest: EngagementManifest) -> None:
        """Test host matching is case-insensitive."""
        validator = ScopeValidator(sample_manifest)
        # Should not raise
        validator.validate_url("https://EXAMPLE.COM/test")
        validator.validate_url("https://App.Example.Com/test")

    def test_invalid_url(self, sample_manifest: EngagementManifest) -> None:
        """Test invalid URL is rejected."""
        validator = ScopeValidator(sample_manifest)
        with pytest.raises(ScopeViolationError):
            validator.validate_url("not-a-url")

    def test_pre_flight_check(self, sample_manifest: EngagementManifest) -> None:
        """Test pre-flight check returns expected results."""
        validator = ScopeValidator(sample_manifest)
        results = validator.pre_flight_check()

        assert "engagement_active" in results
        assert "authorization_confirmed" in results
        assert "scope_hosts_defined" in results
        assert results["scope_hosts_defined"] is True

    def test_get_max_rate(self, sample_manifest: EngagementManifest) -> None:
        """Test max rate retrieval."""
        validator = ScopeValidator(sample_manifest)
        assert validator.get_max_rate() == 5

    def test_get_courtesy_delay(self, sample_manifest: EngagementManifest) -> None:
        """Test courtesy delay retrieval."""
        validator = ScopeValidator(sample_manifest)
        assert validator.get_courtesy_delay_ms() == 200


class TestSecretsManager:
    """Tests for SecretsManager."""

    def test_mask_password(self) -> None:
        """Test password masking."""
        from aipentester.safety import SecretsManager

        sm = SecretsManager()
        text = "username=admin&password=secret123&email=test@example.com"
        masked = sm.mask_string(text)

        assert "secret123" not in masked
        assert "***REDACTED***" in masked
        assert "admin" in masked  # username should remain

    def test_mask_api_key(self) -> None:
        """Test API key masking."""
        from aipentester.safety import SecretsManager

        sm = SecretsManager()
        text = "api_key=sk-1234567890abcdef"
        masked = sm.mask_string(text)

        assert "sk-1234567890abcdef" not in masked
        assert "***REDACTED***" in masked

    def test_mask_authorization_header(self) -> None:
        """Test authorization header masking."""
        from aipentester.safety import SecretsManager

        sm = SecretsManager()
        text = "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9"
        masked = sm.mask_string(text)

        assert "eyJhbGci" not in masked
        assert "***REDACTED***" in masked

    def test_mask_dict(self) -> None:
        """Test dictionary masking."""
        from aipentester.safety import SecretsManager

        sm = SecretsManager()
        data = {
            "username": "admin",
            "password": "secret",
            "api_key": "key123",
            "safe_field": "visible",
        }
        masked = sm.mask_dict(data)

        assert masked["username"] == "admin"  # username is not in default sensitive list
        assert masked["password"] == "***REDACTED***"
        assert masked["api_key"] == "***REDACTED***"
        assert masked["safe_field"] == "visible"

    def test_mask_nested_dict(self) -> None:
        """Test nested dictionary masking."""
        from aipentester.safety import SecretsManager

        sm = SecretsManager()
        data = {
            "user": {
                "name": "admin",
                "password": "secret",
            },
            "config": {
                "token": "abc123",
            },
        }
        masked = sm.mask_dict(data)

        assert masked["user"]["password"] == "***REDACTED***"
        assert masked["config"]["token"] == "***REDACTED***"
        assert masked["user"]["name"] == "admin"


class TestRateLimiter:
    """Tests for RateLimiter."""

    @pytest.mark.asyncio
    async def test_rate_limiting_delay(self) -> None:
        """Test that rate limiter adds appropriate delay."""
        import time

        from aipentester.safety import RateLimiter

        limiter = RateLimiter(max_rate=10, courtesy_delay_ms=0)

        start = time.time()
        await limiter.acquire()
        await limiter.acquire()
        elapsed = time.time() - start

        # Should take at least 0.1 seconds (1/10 rate)
        assert elapsed >= 0.09  # Allow small margin

    @pytest.mark.asyncio
    async def test_courtesy_delay(self) -> None:
        """Test courtesy delay is applied."""
        import time

        from aipentester.safety import RateLimiter

        limiter = RateLimiter(max_rate=100, courtesy_delay_ms=100)

        start = time.time()
        await limiter.acquire()
        elapsed = time.time() - start

        # Should take at least 0.1 seconds (courtesy delay)
        assert elapsed >= 0.09

    @pytest.mark.asyncio
    async def test_per_host_limiting(self) -> None:
        """Test per-host rate limiting."""
        from aipentester.safety import RateLimiter

        limiter = RateLimiter(max_rate=10, courtesy_delay_ms=0)

        # Different hosts should not interfere
        await limiter.acquire("host1")
        await limiter.acquire("host2")
        # Should complete quickly since different hosts
