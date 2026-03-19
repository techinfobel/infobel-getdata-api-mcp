"""Tests for InfobelSettings configuration."""
import pytest


class TestInfobelSettingsDefaults:
    def test_default_base_url(self):
        from infobel_api.config import InfobelSettings
        s = InfobelSettings()
        assert s.base_url == "https://getdata.infobelpro.com"

    def test_default_credentials_empty(self, monkeypatch):
        monkeypatch.delenv("INFOBEL_USERNAME", raising=False)
        monkeypatch.delenv("INFOBEL_PASSWORD", raising=False)
        from infobel_api.config import InfobelSettings
        s = InfobelSettings()
        assert s.username == ""
        assert s.password == ""

    def test_default_timeouts(self):
        from infobel_api.config import InfobelSettings
        s = InfobelSettings()
        assert s.connect_timeout == 30
        assert s.read_timeout == 60

    def test_default_rate_limiting(self):
        from infobel_api.config import InfobelSettings
        s = InfobelSettings()
        assert s.call_delay == 0.5
        assert s.max_call_delay == 10.0
        assert s.adaptive_rate_limit is True
        assert s.rate_limit_threshold == 3
        assert s.rate_limit_retry_delay == 5.0
        assert s.backoff_factor == 2.0
        assert s.respect_retry_after is True

    def test_default_retry(self):
        from infobel_api.config import InfobelSettings
        s = InfobelSettings()
        assert s.max_retries == 3

    def test_default_token_refresh_threshold(self):
        from infobel_api.config import InfobelSettings
        s = InfobelSettings()
        assert s.token_refresh_threshold == 300

    def test_default_pagination(self):
        from infobel_api.config import InfobelSettings
        s = InfobelSettings()
        assert s.page_size == 20
        assert s.name_search_page_size == 20

    def test_default_max_workers(self):
        from infobel_api.config import InfobelSettings
        s = InfobelSettings()
        assert s.max_workers == 10


class TestInfobelSettingsProperties:
    def test_token_url(self):
        from infobel_api.config import InfobelSettings
        s = InfobelSettings(base_url="https://example.com")
        assert s.token_url == "https://example.com/api/token"

    def test_api_url(self):
        from infobel_api.config import InfobelSettings
        s = InfobelSettings(base_url="https://example.com")
        assert s.api_url == "https://example.com/api"

    def test_token_url_default(self):
        from infobel_api.config import InfobelSettings
        s = InfobelSettings()
        assert s.token_url == "https://getdata.infobelpro.com/api/token"

    def test_api_url_default(self):
        from infobel_api.config import InfobelSettings
        s = InfobelSettings()
        assert s.api_url == "https://getdata.infobelpro.com/api"


class TestInfobelSettingsOverrides:
    def test_custom_credentials(self):
        from infobel_api.config import InfobelSettings
        s = InfobelSettings(username="user", password="pass")
        assert s.username == "user"
        assert s.password == "pass"

    def test_custom_base_url(self):
        from infobel_api.config import InfobelSettings
        s = InfobelSettings(base_url="https://staging.example.com")
        assert s.base_url == "https://staging.example.com"

    def test_custom_timeouts(self):
        from infobel_api.config import InfobelSettings
        s = InfobelSettings(connect_timeout=10, read_timeout=120)
        assert s.connect_timeout == 10
        assert s.read_timeout == 120

    def test_custom_retries(self):
        from infobel_api.config import InfobelSettings
        s = InfobelSettings(max_retries=5)
        assert s.max_retries == 5

    def test_disable_adaptive_rate_limit(self):
        from infobel_api.config import InfobelSettings
        s = InfobelSettings(adaptive_rate_limit=False)
        assert s.adaptive_rate_limit is False

    def test_env_prefix(self, monkeypatch):
        monkeypatch.setenv("INFOBEL_USERNAME", "envuser")
        monkeypatch.setenv("INFOBEL_PASSWORD", "envpass")
        from infobel_api.config import InfobelSettings
        s = InfobelSettings()
        assert s.username == "envuser"
        assert s.password == "envpass"

    def test_env_base_url(self, monkeypatch):
        monkeypatch.setenv("INFOBEL_BASE_URL", "https://env-server.com")
        from infobel_api.config import InfobelSettings
        s = InfobelSettings()
        assert s.base_url == "https://env-server.com"
