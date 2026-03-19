"""Tests for AuthenticationHandler."""
from __future__ import annotations

from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch, PropertyMock

import pytest
import responses as resp


def _make_settings(**overrides):
    from infobel_api.config import InfobelSettings
    defaults = dict(
        username="user",
        password="pass",
        base_url="https://api.test.com",
        max_retries=3,
        rate_limit_retry_delay=0.01,  # fast retries in tests
        backoff_factor=1.0,
        respect_retry_after=True,
        token_refresh_threshold=300,
    )
    defaults.update(overrides)
    return InfobelSettings(**defaults)


def _make_handler(settings=None):
    from infobel_api.auth import AuthenticationHandler
    return AuthenticationHandler(settings or _make_settings())


TOKEN_URL = "https://api.test.com/api/token"
GOOD_TOKEN_BODY = {
    "access_token": "test-token-abc",
    "token_type": "Bearer",
    "expires_in": 3600,
}


# ---------------------------------------------------------------------------
# get_token
# ---------------------------------------------------------------------------

class TestGetToken:
    @resp.activate
    def test_fetches_token_on_first_call(self):
        resp.add(resp.POST, TOKEN_URL, json=GOOD_TOKEN_BODY, status=200)
        handler = _make_handler()
        token = handler.get_token()
        assert token == "test-token-abc"
        assert len(resp.calls) == 1

    @resp.activate
    def test_caches_token_on_subsequent_calls(self):
        resp.add(resp.POST, TOKEN_URL, json=GOOD_TOKEN_BODY, status=200)
        handler = _make_handler()
        t1 = handler.get_token()
        t2 = handler.get_token()
        assert t1 == t2
        # Only one HTTP call
        assert len(resp.calls) == 1

    @resp.activate
    def test_force_refresh_fetches_new_token(self):
        resp.add(resp.POST, TOKEN_URL, json=GOOD_TOKEN_BODY, status=200)
        resp.add(resp.POST, TOKEN_URL, json={**GOOD_TOKEN_BODY, "access_token": "new-token"}, status=200)
        handler = _make_handler()
        handler.get_token()
        new = handler.get_token(force_refresh=True)
        assert new == "new-token"
        assert len(resp.calls) == 2

    @resp.activate
    def test_refreshes_expired_token_automatically(self):
        # First call succeeds with an already-expired token
        expired_body = {**GOOD_TOKEN_BODY, "expires_in": 1}
        resp.add(resp.POST, TOKEN_URL, json=expired_body, status=200)
        resp.add(resp.POST, TOKEN_URL, json={**GOOD_TOKEN_BODY, "access_token": "refreshed"}, status=200)

        handler = _make_handler()
        handler.get_token()

        # Manually expire the stored token
        from infobel_api.models.auth import TokenResponse
        handler._token = TokenResponse(
            access_token="old",
            issued_at=datetime.now() - timedelta(hours=2),
            expires_at=datetime.now() - timedelta(hours=1),
        )

        new_token = handler.get_token()
        assert new_token == "refreshed"


# ---------------------------------------------------------------------------
# _fetch_token — HTTP error handling
# ---------------------------------------------------------------------------

class TestFetchToken:
    @resp.activate
    def test_401_raises_authentication_error(self):
        from infobel_api.exceptions import AuthenticationError
        resp.add(resp.POST, TOKEN_URL, json={"error": "invalid_client"}, status=401)
        handler = _make_handler()
        with pytest.raises(AuthenticationError) as exc_info:
            handler._fetch_token()
        assert exc_info.value.status_code == 401

    @resp.activate
    def test_429_retries_then_raises(self):
        from infobel_api.exceptions import AuthenticationError
        # max_retries=1 for speed; handler retries then raises
        s = _make_settings(max_retries=1)
        for _ in range(2):
            resp.add(resp.POST, TOKEN_URL, status=429)
        handler = _make_handler(s)
        with patch("time.sleep"):  # skip actual sleep
            with pytest.raises(AuthenticationError) as exc_info:
                handler._fetch_token()
        assert exc_info.value.status_code == 429
        assert len(resp.calls) == 2

    @resp.activate
    def test_500_retries_then_raises(self):
        from infobel_api.exceptions import AuthenticationError
        s = _make_settings(max_retries=1)
        for _ in range(2):
            resp.add(resp.POST, TOKEN_URL, status=500)
        handler = _make_handler(s)
        with patch("time.sleep"):
            with pytest.raises(AuthenticationError) as exc_info:
                handler._fetch_token()
        assert exc_info.value.status_code == 500
        assert len(resp.calls) == 2

    @resp.activate
    def test_403_raises_authentication_error(self):
        from infobel_api.exceptions import AuthenticationError
        resp.add(resp.POST, TOKEN_URL, json={"error": "forbidden"}, status=403)
        handler = _make_handler()
        with pytest.raises(AuthenticationError) as exc_info:
            handler._fetch_token()
        assert exc_info.value.status_code == 403

    @resp.activate
    def test_success_returns_token_response(self):
        from infobel_api.models.auth import TokenResponse
        resp.add(resp.POST, TOKEN_URL, json=GOOD_TOKEN_BODY, status=200)
        handler = _make_handler()
        result = handler._fetch_token()
        assert isinstance(result, TokenResponse)
        assert result.access_token == "test-token-abc"

    @resp.activate
    def test_missing_access_token_raises(self):
        from infobel_api.exceptions import AuthenticationError
        resp.add(resp.POST, TOKEN_URL, json={"token_type": "Bearer"}, status=200)
        handler = _make_handler()
        with pytest.raises(AuthenticationError, match="No access token"):
            handler._fetch_token()

    def test_timeout_retries_then_raises_network_error(self):
        from infobel_api.exceptions import NetworkError
        import requests
        s = _make_settings(max_retries=1)
        handler = _make_handler(s)

        call_count = 0
        def raise_timeout(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            raise requests.exceptions.Timeout("timeout")

        handler._session.post = raise_timeout
        with patch("time.sleep"):
            with pytest.raises(NetworkError, match="timed out"):
                handler._fetch_token()
        assert call_count == 2  # initial + 1 retry

    def test_connection_error_retries_then_raises_network_error(self):
        from infobel_api.exceptions import NetworkError
        import requests
        s = _make_settings(max_retries=1)
        handler = _make_handler(s)

        call_count = 0
        def raise_conn(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            raise requests.exceptions.ConnectionError("refused")

        handler._session.post = raise_conn
        with patch("time.sleep"):
            with pytest.raises(NetworkError, match="Connection error"):
                handler._fetch_token()
        assert call_count == 2

    @resp.activate
    def test_invalid_json_response_retries_then_raises_network_error(self):
        # requests.exceptions.JSONDecodeError is a RequestException subclass,
        # so it triggers retries (not the ValueError catch) and ultimately
        # raises NetworkError after max_retries exhausted.
        from infobel_api.exceptions import NetworkError
        s = _make_settings(max_retries=1)
        # initial call + 1 retry = 2 calls
        for _ in range(2):
            resp.add(resp.POST, TOKEN_URL, body=b"not json", status=200)
        handler = _make_handler(s)
        with patch("time.sleep"):
            with pytest.raises(NetworkError):
                handler._fetch_token()
        assert len(resp.calls) == 2


# ---------------------------------------------------------------------------
# _retry_delay
# ---------------------------------------------------------------------------

class TestRetryDelay:
    def test_base_delay_no_response(self):
        s = _make_settings(rate_limit_retry_delay=5.0, backoff_factor=2.0)
        handler = _make_handler(s)
        d = handler._retry_delay(0)
        assert d == 5.0

    def test_exponential_backoff(self):
        s = _make_settings(rate_limit_retry_delay=5.0, backoff_factor=2.0)
        handler = _make_handler(s)
        assert handler._retry_delay(0) == 5.0
        assert handler._retry_delay(1) == 10.0
        assert handler._retry_delay(2) == 20.0

    def test_retry_after_header_respected(self):
        s = _make_settings(rate_limit_retry_delay=1.0, backoff_factor=1.0, respect_retry_after=True)
        handler = _make_handler(s)
        mock_response = MagicMock()
        mock_response.headers = {"Retry-After": "30"}
        d = handler._retry_delay(0, mock_response)
        assert d == 30  # Retry-After > base delay

    def test_retry_after_header_ignored_when_disabled(self):
        s = _make_settings(rate_limit_retry_delay=1.0, backoff_factor=1.0, respect_retry_after=False)
        handler = _make_handler(s)
        mock_response = MagicMock()
        mock_response.headers = {"Retry-After": "30"}
        d = handler._retry_delay(0, mock_response)
        assert d == 1.0  # header ignored

    def test_invalid_retry_after_falls_back_to_base(self):
        s = _make_settings(rate_limit_retry_delay=5.0, backoff_factor=1.0, respect_retry_after=True)
        handler = _make_handler(s)
        mock_response = MagicMock()
        mock_response.headers = {"Retry-After": "not-a-number"}
        d = handler._retry_delay(0, mock_response)
        assert d == 5.0


# ---------------------------------------------------------------------------
# invalidate_token / is_token_valid
# ---------------------------------------------------------------------------

class TestTokenStateManagement:
    @resp.activate
    def test_is_token_valid_false_initially(self):
        handler = _make_handler()
        assert handler.is_token_valid() is False

    @resp.activate
    def test_is_token_valid_true_after_fetch(self):
        resp.add(resp.POST, TOKEN_URL, json=GOOD_TOKEN_BODY, status=200)
        handler = _make_handler()
        handler.get_token()
        assert handler.is_token_valid() is True

    @resp.activate
    def test_invalidate_clears_token(self):
        resp.add(resp.POST, TOKEN_URL, json=GOOD_TOKEN_BODY, status=200)
        handler = _make_handler()
        handler.get_token()
        handler.invalidate_token()
        assert handler.is_token_valid() is False

    @resp.activate
    def test_is_token_valid_false_for_expiring_soon(self):
        resp.add(resp.POST, TOKEN_URL, json=GOOD_TOKEN_BODY, status=200)
        handler = _make_handler()
        handler.get_token()
        # Set token to expire within threshold
        handler._token.expires_at = datetime.now() + timedelta(seconds=100)
        # With default threshold=300, token expiring in 100s → needs refresh → invalid
        assert handler.is_token_valid() is False


# ---------------------------------------------------------------------------
# Lifecycle
# ---------------------------------------------------------------------------

class TestAuthHandlerLifecycle:
    def test_close_does_not_raise(self):
        handler = _make_handler()
        handler.close()  # Should not raise

    def test_context_manager(self):
        with _make_handler() as handler:
            assert handler is not None

    def test_refresh_connections_recreates_session(self):
        handler = _make_handler()
        old_session = handler._session
        handler.refresh_connections()
        assert handler._session is not old_session
