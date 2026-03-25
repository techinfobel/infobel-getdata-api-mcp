"""Locations service — geographic lookup endpoints."""

from __future__ import annotations

from typing import Any

from .._base_service import BaseService


class LocationsService(BaseService):

    def get_regions(self, country_code: str, *, language_code: str | None = None) -> list[dict[str, Any]]:
        """GET /api/locations/{countryCode}/regions?languageCode={lang}"""
        params = {}
        if language_code is not None:
            params["languageCode"] = language_code
        return self._http.get(f"/locations/{country_code}/regions", params=params or None)

    def get_provinces(
        self,
        country_code: str,
        *,
        region_code: str | None = None,
        language_code: str | None = None,
    ) -> list[dict[str, Any]]:
        """GET /api/locations/{countryCode}/provinces?regionCode={regionCode}&languageCode={lang}"""
        params = {}
        if region_code is not None:
            params["regionCode"] = region_code
        if language_code is not None:
            params["languageCode"] = language_code
        return self._http.get(f"/locations/{country_code}/provinces", params=params or None)

    def get_cities(
        self,
        country_code: str,
        keyword: str,
        *,
        province_code: str | None = None,
        language_code: str | None = None,
    ) -> list[dict[str, Any]]:
        """Search cities within a country by keyword, optionally narrowed by province."""
        results = self.search_keywords([keyword], country_code, language_code=language_code)
        cities = [r for r in results if r.get("type") == "City"]
        if province_code:
            cities = [c for c in cities if c.get("parentCode") == province_code]
        return cities

    def get_post_codes(self, country_code: str, *, language_code: str | None = None) -> list[dict[str, Any]]:
        """GET /api/locations/{countryCode}/postcodes?languageCode={lang}"""
        params = {}
        if language_code is not None:
            params["languageCode"] = language_code
        return self._http.get(f"/locations/{country_code}/postcodes", params=params or None)

    def get_lineage(
        self,
        country_code: str,
        codes: list[str],
        language_code: str | None = None,
    ) -> list[dict[str, Any]]:
        """POST /api/locations/{cc}/lineage?languageCode={lang}"""
        params = {}
        if language_code is not None:
            params["languageCode"] = language_code
        return self._http.post(
            f"/locations/{country_code}/lineage",
            json=codes,
            params=params or None,
        )

    def search_keywords(
        self,
        keywords: list[str],
        country_code: str,
        language_code: str | None = None,
    ) -> list[dict[str, Any]]:
        """Fan out over multiple keywords, deduplicate results by code."""
        seen: set[str] = set()
        results: list[dict[str, Any]] = []
        for kw in keywords:
            kw = kw.strip()
            if not kw:
                continue
            raw = self.search(country_code, kw, language_code=language_code)
            items: list[Any] = []
            if isinstance(raw, dict):
                for v in raw.values():
                    if isinstance(v, list):
                        items.extend(v)
            else:
                items = raw
            for item in items:
                key = (item.get("code") if isinstance(item, dict) else item) or repr(item)
                if key not in seen:
                    seen.add(key)
                    results.append(item)
        return results

    def search(
        self,
        country_code: str,
        filter: str,
        *,
        language_code: str | None = None,
    ) -> dict[str, list[dict[str, Any]]]:
        """GET /api/locations/{cc}/search/{filter}?languageCode={lang}"""
        params = {}
        if language_code is not None:
            params["languageCode"] = language_code
        return self._http.get(
            f"/locations/{country_code}/search/{filter}",
            params=params or None,
        )

    def search_multi(
        self,
        filter: str,
        *,
        country_codes: list[str] | None = None,
        take: int | None = None,
    ) -> list[dict[str, Any]]:
        """POST /api/locations/search/{filter}?take={take}"""
        params = {}
        if take is not None:
            params["take"] = take
        return self._http.post(
            f"/locations/search/{filter}",
            json=country_codes,
            params=params or None,
        )
