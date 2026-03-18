"""Countries service."""

from __future__ import annotations

from typing import Any

from .._base_service import BaseService


class CountriesService(BaseService):

    def get_all(self) -> list[dict[str, Any]]:
        """GET /api/countries"""
        return self._http.get("/countries")
