"""
Configuration for Infobel API client using pydantic-settings.
"""

from pydantic_settings import BaseSettings


class InfobelSettings(BaseSettings):
    """Settings for Infobel API client, loaded from environment variables."""

    model_config = {"env_prefix": "INFOBEL_"}

    # Authentication
    username: str = ""
    password: str = ""
    base_url: str = "https://getdata.infobelpro.com"

    # Connection settings
    connect_timeout: int = 30
    read_timeout: int = 60

    # Rate limiting
    call_delay: float = 0.5
    max_call_delay: float = 10.0
    adaptive_rate_limit: bool = True
    rate_limit_threshold: int = 3
    rate_limit_retry_delay: float = 5.0
    backoff_factor: float = 2.0
    respect_retry_after: bool = True

    # Retry settings
    max_retries: int = 3

    # Token refresh
    token_refresh_threshold: int = 300  # 5 minutes

    # Pagination
    page_size: int = 20
    name_search_page_size: int = 20

    # Concurrency
    max_workers: int = 10

    @property
    def token_url(self) -> str:
        return f"{self.base_url}/api/token"

    @property
    def api_url(self) -> str:
        return f"{self.base_url}/api"
