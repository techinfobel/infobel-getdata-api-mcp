"""Search service — all search-related endpoints and convenience methods."""

from __future__ import annotations

import logging
from typing import Any, get_args, get_origin

from .._base_service import BaseService
from ..models.search import SearchInput, SearchResponse

logger = logging.getLogger(__name__)

# Pre-compute which SearchInput fields expect a list type.
_LIST_FIELDS: frozenset[str] = frozenset(
    name
    for name, field in SearchInput.model_fields.items()
    if get_origin(field.annotation) is list
    or (
        # Handle Optional[list[...]] → Union[list[...], None]
        get_origin(field.annotation) is type(None)  # won't match, but check args
        or any(get_origin(a) is list for a in get_args(field.annotation))
    )
)


class SearchService(BaseService):
    """POST /api/search and related endpoints."""

    # -- Core endpoints --

    def search(self, input: SearchInput | None = None, **kwargs: Any) -> dict[str, Any]:
        """Execute a search. Accepts a SearchInput or keyword args matching its fields.

        Scalar values passed for list fields are auto-wrapped, e.g.
        ``search(national_id='123')`` becomes ``national_id=['123']``.
        """
        if input is None:
            kwargs = self._coerce_list_fields(kwargs)
            input = SearchInput(**kwargs)
        payload = input.to_api_payload()
        return self._http.post("/search", json=payload)

    @staticmethod
    def _coerce_list_fields(kwargs: dict[str, Any]) -> dict[str, Any]:
        """Wrap scalar values in lists for SearchInput fields that expect lists."""
        result = {}
        for k, v in kwargs.items():
            if k in _LIST_FIELDS and v is not None and not isinstance(v, list):
                result[k] = [v]
            else:
                result[k] = v
        return result

    def get_status(self, search_id: int) -> dict[str, Any]:
        """GET /api/search/{id}/status"""
        return self._http.get(f"/search/{search_id}/status")

    def get_filters(self, search_id: int) -> dict[str, Any]:
        """GET /api/search/{id}/filters"""
        return self._http.get(f"/search/{search_id}/filters")

    def get_counts(self, search_id: int) -> dict[str, Any]:
        """GET /api/search/{id}/counts"""
        return self._http.get(f"/search/{search_id}/counts")

    def get_preview(self, search_id: int) -> dict[str, Any]:
        """GET /api/search/{id}/preview"""
        return self._http.get(f"/search/{search_id}/preview")

    def get_records(self, search_id: int, page: int) -> dict[str, Any]:
        """GET /api/search/{id}/records/{page}"""
        return self._http.get(f"/search/{search_id}/records/{page}")

    def get_history(self, search_id: int) -> dict[str, Any]:
        """GET /api/search/{id}/history"""
        return self._http.get(f"/search/{search_id}/history")

    def post_preview(
        self,
        search_id: int,
        fields: list[str],
        *,
        language_code: str | None = None,
    ) -> dict[str, Any]:
        """POST /api/search/{id}/preview — select specific fields."""
        params = {}
        if language_code is not None:
            params["languageCode"] = language_code
        return self._http.post(
            f"/search/{search_id}/preview",
            json=fields,
            params=params or None,
        )

    def post_records(
        self,
        search_id: int,
        page: int,
        fields: list[str],
        *,
        language_code: str | None = None,
    ) -> dict[str, Any]:
        """POST /api/search/{id}/records/{page} — select specific fields."""
        params = {}
        if language_code is not None:
            params["languageCode"] = language_code
        return self._http.post(
            f"/search/{search_id}/records/{page}",
            json=fields,
            params=params or None,
        )

