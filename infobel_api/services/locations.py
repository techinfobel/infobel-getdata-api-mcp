"""Locations service — geographic lookup endpoints."""

from __future__ import annotations

from typing import Any

from .._base_service import BaseService


class LocationsService(BaseService):

    def get_cities(self, country_code: str) -> list[dict[str, Any]]:
        """GET /api/locations/cities/{country}"""
        return self._http.get(f"/locations/cities/{country_code}")

    def get_cities_by_region(self, country_code: str, region_code: str) -> list[dict[str, Any]]:
        """GET /api/locations/cities/{country}/{region}"""
        return self._http.get(f"/locations/cities/{country_code}/{region_code}")

    def get_provinces(self, country_code: str) -> list[dict[str, Any]]:
        """GET /api/locations/provinces/{country}"""
        return self._http.get(f"/locations/provinces/{country_code}")

    def get_provinces_by_region(self, country_code: str, region_code: str) -> list[dict[str, Any]]:
        """GET /api/locations/provinces/{country}/{region}"""
        return self._http.get(f"/locations/provinces/{country_code}/{region_code}")

    def get_regions(self, country_code: str) -> list[dict[str, Any]]:
        """GET /api/locations/regions/{country}"""
        return self._http.get(f"/locations/regions/{country_code}")

    def get_post_codes(self, country_code: str) -> list[dict[str, Any]]:
        """GET /api/locations/postcodes/{country}"""
        return self._http.get(f"/locations/postcodes/{country_code}")

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
            for item in self.search(country_code, kw, language_code=language_code):
                key = item.get("code") or repr(item)
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
    ) -> list[dict[str, Any]]:
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
