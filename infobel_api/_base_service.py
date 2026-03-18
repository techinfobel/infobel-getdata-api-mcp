"""
Base class for all API service namespaces.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ._http import HttpClient


class BaseService:
    def __init__(self, http: HttpClient):
        self._http = http
