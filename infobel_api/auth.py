"""Authentication handler for Infobel API with automatic token refresh."""

import logging
import threading
import time
from typing import Optional

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from .config import InfobelSettings
from .models.auth import TokenResponse
from .exceptions import AuthenticationError, NetworkError

logger = logging.getLogger(__name__)


class AuthenticationHandler:
    """Thread-safe authentication handler with automatic token refresh."""

    def __init__(self, settings: InfobelSettings):
        self.settings = settings
        self._token: Optional[TokenResponse] = None
        self._lock = threading.Lock()
        self._session = self._create_session()

    def _create_session(self) -> requests.Session:
        session = requests.Session()
        retry_strategy = Retry(
            total=0, connect=0, read=0, raise_on_status=False
        )
        adapter = HTTPAdapter(
            pool_connections=10,
            pool_maxsize=20,
            max_retries=retry_strategy,
            pool_block=False,
        )
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        session.timeout = (self.settings.connect_timeout, self.settings.read_timeout)
        session.headers.update({"Connection": "keep-alive"})
        return session

    def get_token(self, force_refresh: bool = False) -> str:
        """Get valid access token, refreshing if necessary."""
        with self._lock:
            if (
                force_refresh
                or self._token is None
                or self._token.is_expired
                or self._token.needs_refresh(self.settings.token_refresh_threshold)
            ):
                logger.info("Refreshing authentication token")
                self._token = self._fetch_token()
                logger.info("Token refreshed successfully")
            return self._token.access_token

    def _fetch_token(self, retry_count: int = 0) -> TokenResponse:
        data = {
            "grant_type": "password",
            "username": self.settings.username,
            "password": self.settings.password,
        }
        max_retries = self.settings.max_retries

        try:
            response = self._session.post(
                self.settings.token_url,
                data=data,
                timeout=(self.settings.connect_timeout, self.settings.read_timeout),
            )

            if response.status_code == 401:
                raise AuthenticationError(
                    "Invalid credentials",
                    status_code=401,
                    response_data=response.json() if response.content else None,
                )

            if response.status_code == 429:
                if retry_count < max_retries:
                    delay = self._retry_delay(retry_count, response)
                    logger.warning(f"Auth rate limited, waiting {delay:.1f}s")
                    time.sleep(delay)
                    return self._fetch_token(retry_count + 1)
                raise AuthenticationError(
                    f"Rate limited during auth after {max_retries} retries",
                    status_code=429,
                )

            if response.status_code >= 500:
                if retry_count < max_retries:
                    delay = self._retry_delay(retry_count, response)
                    logger.warning(f"Auth server error {response.status_code}, waiting {delay:.1f}s")
                    time.sleep(delay)
                    return self._fetch_token(retry_count + 1)
                raise AuthenticationError(
                    f"Server error during auth after {max_retries} retries",
                    status_code=response.status_code,
                )

            if not response.ok:
                raise AuthenticationError(
                    f"Authentication failed with status {response.status_code}",
                    status_code=response.status_code,
                    response_data=response.json() if response.content else None,
                )

            token_data = response.json()
            if "access_token" not in token_data:
                raise AuthenticationError("No access token in response")
            return TokenResponse.from_api_response(token_data)

        except requests.exceptions.Timeout as e:
            if retry_count < max_retries:
                time.sleep(self._retry_delay(retry_count))
                return self._fetch_token(retry_count + 1)
            raise NetworkError(f"Token request timed out after {max_retries} retries: {e}")

        except requests.exceptions.ConnectionError as e:
            if retry_count < max_retries:
                time.sleep(self._retry_delay(retry_count))
                return self._fetch_token(retry_count + 1)
            raise NetworkError(f"Connection error during token request after {max_retries} retries: {e}")

        except requests.exceptions.RequestException as e:
            if retry_count < max_retries:
                time.sleep(self._retry_delay(retry_count))
                return self._fetch_token(retry_count + 1)
            raise NetworkError(f"Network error during token request after {max_retries} retries: {e}")

        except ValueError as e:
            raise AuthenticationError(f"Invalid JSON response: {e}")

    def _retry_delay(
        self, retry_count: int, response: Optional[requests.Response] = None
    ) -> float:
        base = self.settings.rate_limit_retry_delay
        delay = base * (self.settings.backoff_factor ** retry_count)
        if response and self.settings.respect_retry_after:
            retry_after = response.headers.get("Retry-After")
            if retry_after:
                try:
                    return max(delay, int(retry_after))
                except ValueError:
                    pass
        return delay

    def invalidate_token(self) -> None:
        with self._lock:
            self._token = None

    def is_token_valid(self) -> bool:
        with self._lock:
            return (
                self._token is not None
                and not self._token.is_expired
                and not self._token.needs_refresh(self.settings.token_refresh_threshold)
            )

    def refresh_connections(self) -> None:
        with self._lock:
            self._session.close()
            self._session = self._create_session()

    def close(self) -> None:
        self._session.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
