"""Categories service — category tree endpoints."""

from __future__ import annotations

from typing import Any

from .._base_service import BaseService


class CategoriesService(BaseService):

    def get_infobel(self, language_code: str) -> list[dict[str, Any]]:
        """GET /api/categories/infobel/{lang}"""
        return self._http.get(f"/categories/infobel/{language_code}")

    def get_infobel_children(self, code: str, language_code: str) -> list[dict[str, Any]]:
        """GET /api/categories/infobel/{code}/children/{lang}"""
        return self._http.get(f"/categories/infobel/{code}/children/{language_code}")

    def get_international(self, language_code: str) -> list[dict[str, Any]]:
        """GET /api/categories/international/{lang}"""
        return self._http.get(f"/categories/international/{language_code}")

    def get_international_children(self, code: str, language_code: str) -> list[dict[str, Any]]:
        """GET /api/categories/international/{code}/children/{lang}"""
        return self._http.get(f"/categories/international/{code}/children/{language_code}")

    def get_local(self, country_code: str, language_code: str) -> list[dict[str, Any]]:
        """GET /api/categories/local/{country}/{lang}"""
        return self._http.get(f"/categories/local/{country_code}/{language_code}")

    def get_local_children(self, code: str, country_code: str, language_code: str) -> list[dict[str, Any]]:
        """GET /api/categories/local/{code}/children/{country}/{lang}"""
        return self._http.get(f"/categories/local/{code}/children/{country_code}/{language_code}")

    def get_alt_international(self, language_code: str) -> list[dict[str, Any]]:
        """GET /api/categories/altinternational/{lang}"""
        return self._http.get(f"/categories/altinternational/{language_code}")

    def get_alt_international_children(self, code: str, language_code: str) -> list[dict[str, Any]]:
        """GET /api/categories/altinternational/{code}/children/{lang}"""
        return self._http.get(f"/categories/altinternational/{code}/children/{language_code}")

    def get_infobel_by_level(self, level: int, language_code: str) -> list[dict[str, Any]]:
        """GET /api/categories/infobel/level/{level}/{lang}"""
        return self._http.get(f"/categories/infobel/level/{level}/{language_code}")

    def get_lineage(self, codes: list[str], language_code: str) -> list[dict[str, Any]]:
        """POST /api/categories/lineage?languageCode={lang}"""
        return self._http.post(
            "/categories/lineage",
            json=codes,
            params={"languageCode": language_code},
        )

    def search(
        self,
        language_code: str,
        filter: str,
        *,
        country_code: str | None = None,
    ) -> list[dict[str, Any]]:
        """GET /api/categories/search/{lang}/{filter}?countryCode={cc}"""
        params = {}
        if country_code is not None:
            params["countryCode"] = country_code
        return self._http.get(
            f"/categories/search/{language_code}/{filter}",
            params=params or None,
        )

    def search_multi(
        self,
        language_code: str,
        filter: str,
        country_codes: list[str],
    ) -> list[dict[str, Any]]:
        """POST /api/categories/search/{lang}/{filter}"""
        return self._http.post(
            f"/categories/search/{language_code}/{filter}",
            json=country_codes,
        )

    def _search_keywords(
        self,
        keywords: list[str],
        language_code: str,
        country_code: str | None = None,
    ) -> list[dict[str, Any]]:
        """Fan out over multiple keywords, deduplicate results by code."""
        seen: set[str] = set()
        results: list[dict[str, Any]] = []
        for kw in keywords:
            kw = kw.strip()
            if not kw:
                continue
            for item in self.search(language_code, kw, country_code=country_code):
                key = item.get("code") or repr(item)
                if key not in seen:
                    seen.add(key)
                    results.append(item)
        return results

    def search_infobel(self, keywords: list[str], language_code: str = "en") -> list[dict[str, Any]]:
        """Search Infobel proprietary categories by one or more keywords."""
        return self._search_keywords(keywords, language_code)

    def search_international(self, keywords: list[str], language_code: str = "en") -> list[dict[str, Any]]:
        """Search ISIC international categories by one or more keywords."""
        return self._search_keywords(keywords, language_code)

    def search_local(self, keywords: list[str], country_code: str, language_code: str = "en") -> list[dict[str, Any]]:
        """Search country-specific local categories by one or more keywords."""
        return self._search_keywords(keywords, language_code, country_code=country_code)

    def search_alt_international(self, keywords: list[str], language_code: str = "en") -> list[dict[str, Any]]:
        """Search NACE (AltInternational) categories by one or more keywords."""
        return self._search_keywords(keywords, language_code)
