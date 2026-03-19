"""Tests for HttpClient."""
from __future__ import annotations

from unittest.mock import MagicMock, patch, call

import pytest
import responses as resp


BASE_URL = "https://api.test.com"
API_URL = f"{BASE_URL}/api"


def _make_settings(**overrides):
    from infobel_api.config import InfobelSettings
    defaults = dict(
        username="user",
        password="pass",
        base_url=BASE_URL,
        max_retries=3,
        rate_limit_retry_delay=0.01,
        backoff_factor=1.0,
        respect_retry_after=True,
        adaptive_rate_limit=True,
        rate_limit_threshold=3,
        call_delay=0.0,
        max_call_delay=10.0,
    )
    defaults.update(overrides)
    return InfobelSettings(**defaults)


def _make_http(settings=None):
    from infobel_api._http import HttpClient
    s = settings or _make_settings()
    auth = MagicMock()
    auth.get_token.return_value = "test-token"
    auth.invalidate_token.return_value = None
    return HttpClient(s, auth)


# ---------------------------------------------------------------------------
# get / post delegation
# ---------------------------------------------------------------------------

class TestGetPost:
    @resp.activate
    def test_get_calls_request_with_get_method(self):
        resp.add(resp.GET, f"{API_URL}/test", json={"ok": True})
        http = _make_http()
        result = http.get("/test")
        assert result == {"ok": True}
        assert resp.calls[0].request.method == "GET"

    @resp.activate
    def test_post_calls_request_with_post_method(self):
        resp.add(resp.POST, f"{API_URL}/items", json={"created": True})
        http = _make_http()
        result = http.post("/items", json={"name": "x"})
        assert result == {"created": True}
        assert resp.calls[0].request.method == "POST"

    @resp.activate
    def test_get_with_params(self):
        resp.add(resp.GET, f"{API_URL}/search", json=[], match_querystring=False)
        http = _make_http()
        http.get("/search", params={"q": "test"})
        assert "q=test" in resp.calls[0].request.url

    @resp.activate
    def test_request_builds_full_url(self):
        resp.add(resp.GET, f"{API_URL}/categories/infobel/en", json=[])
        http = _make_http()
        http.get("/categories/infobel/en")
        assert resp.calls[0].request.url == f"{API_URL}/categories/infobel/en"

    @resp.activate
    def test_bearer_token_in_headers(self):
        resp.add(resp.GET, f"{API_URL}/test", json={})
        http = _make_http()
        http.get("/test")
        auth_header = resp.calls[0].request.headers.get("Authorization")
        assert auth_header == "Bearer test-token"


# ---------------------------------------------------------------------------
# 429 Rate Limiting
# ---------------------------------------------------------------------------

class TestRateLimiting:
    @resp.activate
    def test_429_retries_and_succeeds(self):
        resp.add(resp.GET, f"{API_URL}/test", status=429)
        resp.add(resp.GET, f"{API_URL}/test", json={"ok": True})
        http = _make_http()
        with patch("time.sleep"):
            result = http.get("/test")
        assert result == {"ok": True}
        assert len(resp.calls) == 2

    @resp.activate
    def test_429_exhausts_retries_raises_rate_limit_error(self):
        from infobel_api.exceptions import RateLimitError
        s = _make_settings(max_retries=2)
        for _ in range(3):  # initial + 2 retries
            resp.add(resp.GET, f"{API_URL}/test", status=429)
        http = _make_http(s)
        with patch("time.sleep"):
            with pytest.raises(RateLimitError) as exc_info:
                http.get("/test")
        assert exc_info.value.status_code == 429
        assert len(resp.calls) == 3

    @resp.activate
    def test_retry_after_header_causes_sleep(self):
        # Verify that a 429 triggers sleep before the retry succeeds.
        # The delay value is tested in isolation via TestCalculateRetryDelay.
        resp.add(resp.GET, f"{API_URL}/test", status=429, headers={"Retry-After": "1"})
        resp.add(resp.GET, f"{API_URL}/test", json={"ok": True})
        http = _make_http()
        with patch("time.sleep") as mock_sleep:
            result = http.get("/test")
        mock_sleep.assert_called_once()
        assert result == {"ok": True}


# ---------------------------------------------------------------------------
# 401 Token Refresh
# ---------------------------------------------------------------------------

class TestTokenRefreshOn401:
    @resp.activate
    def test_401_invalidates_token_and_retries(self):
        # First request returns 401, second succeeds with new token
        resp.add(resp.GET, f"{API_URL}/test", status=401)
        resp.add(resp.GET, f"{API_URL}/test", json={"data": "ok"})

        from infobel_api._http import HttpClient
        s = _make_settings()
        auth = MagicMock()
        auth.get_token.return_value = "old-token"
        http = HttpClient(s, auth)

        result = http.get("/test")
        assert result == {"data": "ok"}
        auth.invalidate_token.assert_called_once()
        assert len(resp.calls) == 2

    @resp.activate
    def test_401_on_retry_does_not_loop_forever(self):
        from infobel_api.exceptions import InfobelAPIError
        # Both calls return 401 — second attempt (retry_count=1) raises directly
        resp.add(resp.GET, f"{API_URL}/test", status=401)
        resp.add(resp.GET, f"{API_URL}/test", status=401)

        from infobel_api._http import HttpClient
        s = _make_settings()
        auth = MagicMock()
        auth.get_token.return_value = "tok"
        http = HttpClient(s, auth)

        with pytest.raises(InfobelAPIError):
            http.get("/test")
        # Only 2 calls: initial + one retry
        assert len(resp.calls) == 2


# ---------------------------------------------------------------------------
# 5xx Server Errors
# ---------------------------------------------------------------------------

class TestServerErrors:
    @resp.activate
    def test_500_retries_and_succeeds(self):
        resp.add(resp.GET, f"{API_URL}/test", status=500)
        resp.add(resp.GET, f"{API_URL}/test", json={"ok": True})
        http = _make_http()
        with patch("time.sleep"):
            result = http.get("/test")
        assert result == {"ok": True}

    @resp.activate
    def test_500_exhausts_retries_raises(self):
        from infobel_api.exceptions import InfobelAPIError
        s = _make_settings(max_retries=1)
        resp.add(resp.GET, f"{API_URL}/test", status=500)
        resp.add(resp.GET, f"{API_URL}/test", status=500)
        http = _make_http(s)
        with patch("time.sleep"):
            with pytest.raises(InfobelAPIError) as exc_info:
                http.get("/test")
        assert exc_info.value.status_code == 500

    @resp.activate
    def test_503_retries(self):
        resp.add(resp.GET, f"{API_URL}/test", status=503)
        resp.add(resp.GET, f"{API_URL}/test", json={"ok": True})
        http = _make_http()
        with patch("time.sleep"):
            result = http.get("/test")
        assert result == {"ok": True}


# ---------------------------------------------------------------------------
# Other HTTP errors
# ---------------------------------------------------------------------------

class TestOtherHttpErrors:
    @resp.activate
    def test_400_raises_immediately(self):
        from infobel_api.exceptions import InfobelAPIError
        resp.add(resp.GET, f"{API_URL}/test", status=400, json={"error": "bad request"})
        http = _make_http()
        with pytest.raises(InfobelAPIError) as exc_info:
            http.get("/test")
        assert exc_info.value.status_code == 400

    @resp.activate
    def test_404_raises_immediately(self):
        from infobel_api.exceptions import InfobelAPIError
        resp.add(resp.GET, f"{API_URL}/test", status=404)
        http = _make_http()
        with pytest.raises(InfobelAPIError) as exc_info:
            http.get("/test")
        assert exc_info.value.status_code == 404


# ---------------------------------------------------------------------------
# Network errors
# ---------------------------------------------------------------------------

class TestNetworkErrors:
    def test_timeout_retries_then_raises(self):
        from infobel_api.exceptions import NetworkError
        import requests
        s = _make_settings(max_retries=1)
        http = _make_http(s)

        call_count = 0
        def raise_timeout(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            raise requests.exceptions.Timeout("timeout")

        http._session.request = raise_timeout
        with patch("time.sleep"):
            with pytest.raises(NetworkError, match="timed out"):
                http.get("/test")
        assert call_count == 2

    def test_connection_error_retries_then_raises(self):
        from infobel_api.exceptions import NetworkError
        import requests
        s = _make_settings(max_retries=1)
        http = _make_http(s)

        call_count = 0
        def raise_conn(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            raise requests.exceptions.ConnectionError("refused")

        http._session.request = raise_conn
        with patch("time.sleep"):
            with pytest.raises(NetworkError, match="Connection error"):
                http.get("/test")
        assert call_count == 2

    def test_generic_request_exception_retries_then_raises(self):
        from infobel_api.exceptions import NetworkError
        import requests
        s = _make_settings(max_retries=1)
        http = _make_http(s)

        call_count = 0
        def raise_generic(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            raise requests.exceptions.RequestException("oops")

        http._session.request = raise_generic
        with patch("time.sleep"):
            with pytest.raises(NetworkError, match="Network error"):
                http.get("/test")
        assert call_count == 2


# ---------------------------------------------------------------------------
# raw_response mode
# ---------------------------------------------------------------------------

class TestRawResponseMode:
    @resp.activate
    def test_raw_response_returns_response_object(self):
        import requests
        resp.add(resp.GET, f"{API_URL}/test", json={"data": 1})
        http = _make_http()
        result = http.request("GET", "/test", raw_response=True)
        assert isinstance(result, requests.Response)
        assert result.status_code == 200


# ---------------------------------------------------------------------------
# _safe_json
# ---------------------------------------------------------------------------

class TestSafeJson:
    def test_returns_parsed_json(self):
        from infobel_api._http import HttpClient
        mock_resp = MagicMock()
        mock_resp.content = b'{"key": "value"}'
        mock_resp.json.return_value = {"key": "value"}
        result = HttpClient._safe_json(mock_resp)
        assert result == {"key": "value"}

    def test_returns_none_when_no_content(self):
        from infobel_api._http import HttpClient
        mock_resp = MagicMock()
        mock_resp.content = b""
        result = HttpClient._safe_json(mock_resp)
        assert result is None

    def test_returns_none_on_invalid_json(self):
        from infobel_api._http import HttpClient
        mock_resp = MagicMock()
        mock_resp.content = b"not-json"
        mock_resp.json.side_effect = ValueError("invalid json")
        result = HttpClient._safe_json(mock_resp)
        assert result is None


# ---------------------------------------------------------------------------
# Adaptive rate limiting
# ---------------------------------------------------------------------------

class TestAdaptiveRateLimiting:
    def test_initial_delay_is_call_delay(self):
        s = _make_settings(call_delay=0.5, adaptive_rate_limit=True)
        http = _make_http(s)
        assert http.get_current_delay() == 0.5

    def test_disabled_returns_call_delay(self):
        s = _make_settings(call_delay=0.5, adaptive_rate_limit=False)
        http = _make_http(s)
        assert http.get_current_delay() == 0.5

    def test_rate_limit_increases_delay_after_threshold(self):
        s = _make_settings(
            call_delay=0.5,
            max_call_delay=10.0,
            adaptive_rate_limit=True,
            rate_limit_threshold=3,
        )
        http = _make_http(s)
        initial = http.get_current_delay()
        for _ in range(3):  # Hit threshold
            http._update_rate_limit_state(is_rate_limited=True)
        assert http.get_current_delay() > initial

    def test_delay_capped_at_max_call_delay(self):
        s = _make_settings(
            call_delay=8.0,
            max_call_delay=10.0,
            adaptive_rate_limit=True,
            rate_limit_threshold=1,
        )
        http = _make_http(s)
        for _ in range(10):
            http._update_rate_limit_state(is_rate_limited=True)
        assert http.get_current_delay() <= 10.0

    def test_no_rate_limit_update_when_disabled(self):
        s = _make_settings(call_delay=0.5, adaptive_rate_limit=False)
        http = _make_http(s)
        for _ in range(10):
            http._update_rate_limit_state(is_rate_limited=True)
        assert http.get_current_delay() == 0.5


# ---------------------------------------------------------------------------
# _calculate_retry_delay
# ---------------------------------------------------------------------------

class TestCalculateRetryDelay:
    def test_base_delay_at_retry_0(self):
        s = _make_settings(rate_limit_retry_delay=5.0, backoff_factor=2.0)
        http = _make_http(s)
        assert http._calculate_retry_delay(0) == 5.0

    def test_exponential_backoff(self):
        s = _make_settings(rate_limit_retry_delay=5.0, backoff_factor=2.0)
        http = _make_http(s)
        assert http._calculate_retry_delay(1) == 10.0
        assert http._calculate_retry_delay(2) == 20.0

    def test_capped_at_600(self):
        s = _make_settings(rate_limit_retry_delay=5.0, backoff_factor=2.0)
        http = _make_http(s)
        assert http._calculate_retry_delay(100) == 600

    def test_retry_after_header_used_when_larger(self):
        s = _make_settings(rate_limit_retry_delay=1.0, backoff_factor=1.0, respect_retry_after=True)
        http = _make_http(s)
        mock_response = MagicMock()
        mock_response.headers = {"Retry-After": "30"}
        d = http._calculate_retry_delay(0, mock_response)
        assert d == 30


# ---------------------------------------------------------------------------
# Lifecycle
# ---------------------------------------------------------------------------

class TestHttpClientLifecycle:
    def test_close_does_not_raise(self):
        http = _make_http()
        http.close()

    def test_context_manager(self):
        with _make_http() as http:
            assert http is not None

    def test_refresh_connections_recreates_session(self):
        http = _make_http()
        old = http._session
        http.refresh_connections()
        assert http._session is not old
