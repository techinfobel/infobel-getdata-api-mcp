"""
Custom exceptions for Infobel API client.
"""

from typing import Optional, Any


class InfobelAPIError(Exception):
    """Base exception for Infobel API errors."""
    
    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        response_data: Optional[Any] = None
    ):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.response_data = response_data


class AuthenticationError(InfobelAPIError):
    """Authentication failed."""
    pass


class NetworkError(InfobelAPIError):
    """Network-related error."""
    pass


class RateLimitError(InfobelAPIError):
    """API rate limit exceeded."""
    pass


class SearchError(InfobelAPIError):
    """Error during search operation."""
    pass

