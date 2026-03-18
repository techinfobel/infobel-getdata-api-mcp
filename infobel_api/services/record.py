"""Record service — individual record endpoints."""

from __future__ import annotations

from typing import Any

from .._base_service import BaseService


class RecordService(BaseService):

    def get(self, country_code: str, unique_id: str) -> dict[str, Any]:
        """GET /api/record/{country}/{uniqueId}"""
        return self._http.get(f"/record/{country_code}/{unique_id}")

    def get_partial(self, country_code: str, unique_id: str) -> dict[str, Any]:
        """GET /api/record/{country}/{uniqueId}/partial"""
        return self._http.get(f"/record/{country_code}/{unique_id}/partial")
