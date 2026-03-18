"""Test service — connectivity check."""

from __future__ import annotations

from typing import Any

from .._base_service import BaseService


class TestService(BaseService):

    def hello(self) -> Any:
        """GET /api/test/hello"""
        return self._http.get("/test/hello")
