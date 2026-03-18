"""
Shared HTTP client with retry, rate limiting, and auth handling.
"""

import logging
import time
from typing import Any, Optional

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from .config import InfobelSettings
from .auth import AuthenticationHandler
from .exceptions import NetworkError, RateLimitError, InfobelAPIError

logger = logging.getLogger(__name__)


class HttpClient:
    """
    Centralized HTTP client that handles authentication, retries,
    rate limiting, and connection pooling for all API requests.
    """

    def __init__(self, settings: InfobelSettings, auth_handler: AuthenticationHandler):
        self.settings = settings
        self.auth_handler = auth_handler

        # Adaptive rate limiting state
        self._rate_limit_count = 0
        self._current_call_delay = settings.call_delay
        self._last_rate_limit_time = 0.0

        self._session = self._create_session()

    def _create_session(self) -> requests.Session:
        session = requests.Session()

        retry_strategy = Retry(
            total=0,
            connect=0,
            read=0,
            status_forcelist=[],
            raise_on_status=False,
            backoff_factor=0.5,
        )

        pool_connections = min(self.settings.max_workers, 50)
        pool_maxsize = min(self.settings.max_workers * 3, 150)

        adapter = HTTPAdapter(
            pool_connections=pool_connections,
            pool_maxsize=pool_maxsize,
            max_retries=retry_strategy,
            pool_block=False,
        )

        session.mount("http://", adapter)
        session.mount("https://", adapter)
        session.timeout = (self.settings.connect_timeout, self.settings.read_timeout)
        session.headers.update(
            {"Connection": "keep-alive", "User-Agent": "InfobelClient/2.0"}
        )
        return session

    # -- Public API --

    def get(self, path: str, params: dict | None = None, **kwargs: Any) -> Any:
        return self.request("GET", path, params=params, **kwargs)

    def post(self, path: str, json: dict | None = None, **kwargs: Any) -> Any:
        return self.request("POST", path, json=json, **kwargs)

    def request(
        self,
        method: str,
        path: str,
        *,
        json: dict | None = None,
        params: dict | None = None,
        retry_count: int = 0,
        raw_response: bool = False,
    ) -> Any:
        """
        Execute an HTTP request with full retry/auth/rate-limit handling.

        Args:
            method: HTTP method (GET, POST, etc.)
            path: API path (e.g. "/search" — will be prefixed with api_url)
            json: JSON body for POST requests
            params: Query parameters
            retry_count: Internal retry counter
            raw_response: If True, return the raw requests.Response object

        Returns:
            Parsed JSON response (dict/list) or raw Response if raw_response=True
        """
        url = f"{self.settings.api_url}{path}"
        token = self.auth_handler.get_token()
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}",
        }
        max_retries = self.settings.max_retries
        timeout = (self.settings.connect_timeout, self.settings.read_timeout)

        try:
            logger.debug(f"{method} {url} (attempt {retry_count + 1})")

            response = self._session.request(
                method,
                url,
                json=json,
                params=params,
                headers=headers,
                timeout=timeout,
            )

            # 429 — Rate limiting
            if response.status_code == 429:
                self._update_rate_limit_state(is_rate_limited=True)
                if retry_count < max_retries:
                    delay = self._calculate_retry_delay(retry_count, response)
                    logger.warning(
                        f"Rate limited (attempt {retry_count + 1}/{max_retries}), "
                        f"waiting {delay:.1f}s"
                    )
                    time.sleep(delay)
                    return self.request(
                        method, path, json=json, params=params,
                        retry_count=retry_count + 1, raw_response=raw_response,
                    )
                raise RateLimitError(
                    f"Rate limit exceeded after {max_retries} retries",
                    status_code=429,
                    response_data=self._safe_json(response),
                )
            else:
                self._update_rate_limit_state(is_rate_limited=False)

            # 401 — Auth expired, refresh once
            if response.status_code == 401 and retry_count == 0:
                logger.warning("Token expired, refreshing and retrying...")
                self.auth_handler.invalidate_token()
                return self.request(
                    method, path, json=json, params=params,
                    retry_count=retry_count + 1, raw_response=raw_response,
                )

            # 5xx — Server error
            if response.status_code >= 500:
                if retry_count < max_retries:
                    delay = self._calculate_retry_delay(retry_count, response)
                    logger.warning(
                        f"Server error {response.status_code} "
                        f"(attempt {retry_count + 1}/{max_retries}), "
                        f"waiting {delay:.1f}s"
                    )
                    time.sleep(delay)
                    return self.request(
                        method, path, json=json, params=params,
                        retry_count=retry_count + 1, raw_response=raw_response,
                    )
                raise InfobelAPIError(
                    f"Server error after {max_retries} retries",
                    status_code=response.status_code,
                    response_data=self._safe_json(response),
                )

            # Other errors
            if not response.ok:
                raise InfobelAPIError(
                    f"Request failed with status {response.status_code}",
                    status_code=response.status_code,
                    response_data=self._safe_json(response),
                )

            if raw_response:
                return response
            return response.json()

        except requests.exceptions.Timeout as e:
            if retry_count < max_retries:
                delay = self._calculate_retry_delay(retry_count)
                logger.warning(f"Timeout (attempt {retry_count + 1}/{max_retries}), waiting {delay:.1f}s")
                time.sleep(delay)
                return self.request(
                    method, path, json=json, params=params,
                    retry_count=retry_count + 1, raw_response=raw_response,
                )
            raise NetworkError(f"Request timed out after {max_retries} retries: {e}")

        except requests.exceptions.ConnectionError as e:
            if retry_count < max_retries:
                delay = self._calculate_retry_delay(retry_count)
                logger.warning(f"Connection error (attempt {retry_count + 1}/{max_retries}), waiting {delay:.1f}s")
                time.sleep(delay)
                return self.request(
                    method, path, json=json, params=params,
                    retry_count=retry_count + 1, raw_response=raw_response,
                )
            raise NetworkError(f"Connection error after {max_retries} retries: {e}")

        except requests.exceptions.RequestException as e:
            if retry_count < max_retries:
                delay = self._calculate_retry_delay(retry_count)
                logger.warning(f"Network error (attempt {retry_count + 1}/{max_retries}), waiting {delay:.1f}s")
                time.sleep(delay)
                return self.request(
                    method, path, json=json, params=params,
                    retry_count=retry_count + 1, raw_response=raw_response,
                )
            raise NetworkError(f"Network error after {max_retries} retries: {e}")

        except ValueError as e:
            raise InfobelAPIError(f"Invalid JSON response: {e}")

    # -- Rate limiting helpers --

    def _update_rate_limit_state(self, is_rate_limited: bool) -> None:
        if not self.settings.adaptive_rate_limit:
            return
        current_time = time.time()
        if is_rate_limited:
            self._rate_limit_count += 1
            self._last_rate_limit_time = current_time
            if self._rate_limit_count >= self.settings.rate_limit_threshold:
                self._current_call_delay = min(
                    self._current_call_delay * 1.5, self.settings.max_call_delay
                )
                logger.warning(f"Adaptive rate limiting: delay increased to {self._current_call_delay:.1f}s")
                self._rate_limit_count = 0
        else:
            if (current_time - self._last_rate_limit_time) > 300:
                self._current_call_delay = max(
                    self._current_call_delay * 0.9, self.settings.call_delay
                )
                self._rate_limit_count = 0

    def _calculate_retry_delay(
        self, retry_count: int, response: Optional[requests.Response] = None
    ) -> float:
        base_delay = self.settings.rate_limit_retry_delay
        backoff_delay = min(base_delay * (self.settings.backoff_factor ** retry_count), 600)

        if response and self.settings.respect_retry_after:
            retry_after = response.headers.get("Retry-After")
            if retry_after:
                try:
                    return max(backoff_delay, int(retry_after))
                except ValueError:
                    pass
        return backoff_delay

    def get_current_delay(self) -> float:
        if self.settings.adaptive_rate_limit:
            return self._current_call_delay
        return self.settings.call_delay

    # -- Lifecycle --

    def refresh_connections(self) -> None:
        logger.info("Refreshing connection pool...")
        self._session.close()
        self._session = self._create_session()
        self.auth_handler.refresh_connections()
        logger.info("Connection pool refreshed")

    def close(self) -> None:
        self._session.close()
        self.auth_handler.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    @staticmethod
    def _safe_json(response: requests.Response) -> Any:
        try:
            return response.json() if response.content else None
        except ValueError:
            return None
