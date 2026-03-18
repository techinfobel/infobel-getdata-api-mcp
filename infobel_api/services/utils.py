"""Utils service — reference data endpoints."""

from __future__ import annotations

from typing import Any

from .._base_service import BaseService


class UtilsService(BaseService):

    def get_languages(self) -> list[dict[str, Any]]:
        """GET /api/utils/languages"""
        return self._http.get("/utils/languages")

    def get_reliability_codes(self) -> list[dict[str, Any]]:
        """GET /api/utils/reliabilitycodes"""
        return self._http.get("/utils/reliabilitycodes")

    def get_status_codes(self) -> list[dict[str, Any]]:
        """GET /api/utils/statuscodes"""
        return self._http.get("/utils/statuscodes")

    def get_geo_levels(self) -> list[dict[str, Any]]:
        """GET /api/utils/geolevels"""
        return self._http.get("/utils/geolevels")

    def get_legal_status_codes(self, country_code: str) -> list[dict[str, Any]]:
        """GET /api/utils/legalstatuscodes/{country}"""
        return self._http.get(f"/utils/legalstatuscodes/{country_code}")

    def get_national_id_types(self, country_code: str) -> list[dict[str, Any]]:
        """GET /api/utils/nationalidentificationtypecodes/{country}"""
        return self._http.get(f"/utils/nationalidentificationtypecodes/{country_code}")

    def get_import_export_agent_codes(self) -> list[dict[str, Any]]:
        """GET /api/utils/importexportagentcodes"""
        return self._http.get("/utils/importexportagentcodes")

    def get_currencies(self) -> list[dict[str, Any]]:
        """GET /api/utils/currencies"""
        return self._http.get("/utils/currencies")

    def get_sorting_orders(self) -> list[dict[str, Any]]:
        """GET /api/utils/sortingorders"""
        return self._http.get("/utils/sortingorders")

    def get_technographical_tags(self) -> list[dict[str, Any]]:
        """GET /api/utils/technographicaltags"""
        return self._http.get("/utils/technographicaltags")

    def get_executive_tags(self) -> list[dict[str, Any]]:
        """GET /api/utils/executivetags"""
        return self._http.get("/utils/executivetags")

    def get_website_status_flags(self) -> list[dict[str, Any]]:
        """GET /api/utils/websitestatusflags"""
        return self._http.get("/utils/websitestatusflags")

    def get_social_links(self) -> list[dict[str, Any]]:
        """GET /api/utils/sociallinks"""
        return self._http.get("/utils/sociallinks")

    def get_gender_codes(self) -> list[dict[str, Any]]:
        """GET /api/utils/gendercodes"""
        return self._http.get("/utils/gendercodes")

    def get_title_codes(self) -> list[dict[str, Any]]:
        """GET /api/utils/titlecodes"""
        return self._http.get("/utils/titlecodes")

    def get_local_activity_type_codes(self) -> list[dict[str, Any]]:
        """GET /api/utils/localactivitytypecodes"""
        return self._http.get("/utils/localactivitytypecodes")
