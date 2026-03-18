"""Infobel API data models."""

from .auth import TokenResponse
from .common import CoordinateOption
from .search import SearchInput, SearchResponse, PaginatedResponse

__all__ = [
    "TokenResponse",
    "CoordinateOption",
    "SearchInput",
    "SearchResponse",
    "PaginatedResponse",
]
