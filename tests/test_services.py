"""Tests for all service classes."""
from __future__ import annotations

from unittest.mock import MagicMock, call

import pytest


def _make_http(responses: dict | None = None):
    """Return a mock HttpClient with configurable return values."""
    http = MagicMock()
    if responses:
        # Configure get/post side effects
        def _get(path, params=None, **kwargs):
            return responses.get(("GET", path), {})
        def _post(path, json=None, params=None, **kwargs):
            return responses.get(("POST", path), {})
        http.get.side_effect = _get
        http.post.side_effect = _post
    return http


# ---------------------------------------------------------------------------
# SearchService
# ---------------------------------------------------------------------------

class TestSearchService:
    def _make_service(self, http=None):
        from infobel_api.services.search import SearchService
        return SearchService(http or _make_http())

    def test_search_with_kwargs_calls_post(self):
        http = _make_http()
        http.post.return_value = {"searchId": 1, "counts": {}}
        svc = self._make_service(http)
        svc.search(country_codes=["GB"])
        http.post.assert_called_once()
        path, kwargs = http.post.call_args[0][0], http.post.call_args[1]
        assert path == "/search"

    def test_search_with_search_input_object(self):
        from infobel_api.models.search import SearchInput
        http = _make_http()
        http.post.return_value = {"searchId": 5}
        svc = self._make_service(http)
        si = SearchInput(country_codes=["DE"])
        svc.search(input=si)
        http.post.assert_called_once()
        payload = http.post.call_args[1]["json"]
        assert "CountryCodes" in payload

    def test_search_payload_has_pascal_case(self):
        http = _make_http()
        http.post.return_value = {}
        svc = self._make_service(http)
        svc.search(country_codes=["FR"], business_name=["Renault"])
        payload = http.post.call_args[1]["json"]
        assert "CountryCodes" in payload
        assert "BusinessName" in payload
        assert "country_codes" not in payload

    def test_coerce_list_fields_scalar_to_list(self):
        from infobel_api.services.search import SearchService
        result = SearchService._coerce_list_fields({"country_codes": "GB"})
        assert result["country_codes"] == ["GB"]

    def test_coerce_list_fields_already_list_unchanged(self):
        from infobel_api.services.search import SearchService
        result = SearchService._coerce_list_fields({"country_codes": ["GB", "DE"]})
        assert result["country_codes"] == ["GB", "DE"]

    def test_coerce_list_fields_non_list_field_unchanged(self):
        from infobel_api.services.search import SearchService
        result = SearchService._coerce_list_fields({"ceo_name": "Alice"})
        assert result["ceo_name"] == "Alice"

    def test_coerce_list_fields_none_not_wrapped(self):
        from infobel_api.services.search import SearchService
        result = SearchService._coerce_list_fields({"country_codes": None})
        assert result["country_codes"] is None

    def test_coerce_multiple_scalar_list_fields(self):
        from infobel_api.services.search import SearchService
        result = SearchService._coerce_list_fields({
            "country_codes": "US",
            "business_name": "Tesla",
            "post_codes": "90210",
        })
        assert result["country_codes"] == ["US"]
        assert result["business_name"] == ["Tesla"]
        assert result["post_codes"] == ["90210"]

    def test_get_status_calls_correct_path(self):
        http = _make_http()
        http.get.return_value = {"status": "complete"}
        svc = self._make_service(http)
        result = svc.get_status(42)
        http.get.assert_called_once_with("/search/42/status")
        assert result == {"status": "complete"}

    def test_get_filters_calls_correct_path(self):
        http = _make_http()
        http.get.return_value = {}
        svc = self._make_service(http)
        svc.get_filters(7)
        http.get.assert_called_once_with("/search/7/filters")

    def test_get_counts_calls_correct_path(self):
        http = _make_http()
        http.get.return_value = {"total": 100}
        svc = self._make_service(http)
        svc.get_counts(3)
        http.get.assert_called_once_with("/search/3/counts")

    def test_get_preview_calls_correct_path(self):
        http = _make_http()
        http.get.return_value = []
        svc = self._make_service(http)
        svc.get_preview(10)
        http.get.assert_called_once_with("/search/10/preview")

    def test_get_records_calls_correct_path(self):
        http = _make_http()
        http.get.return_value = {"records": []}
        svc = self._make_service(http)
        svc.get_records(5, 2)
        http.get.assert_called_once_with("/search/5/records/2")

    def test_get_history_calls_correct_path(self):
        http = _make_http()
        http.get.return_value = []
        svc = self._make_service(http)
        svc.get_history(99)
        http.get.assert_called_once_with("/search/99/history")

    def test_post_records_calls_correct_path_and_payload(self):
        http = _make_http()
        http.post.return_value = {"records": [{"uniqueID": "001"}]}
        svc = self._make_service(http)
        result = svc.post_records(12, 3, ["businessName", "city"])
        http.post.assert_called_once_with(
            "/search/12/records/3",
            json=["businessName", "city"],
            params=None,
        )
        assert result == {"records": [{"uniqueID": "001"}]}

    def test_post_records_with_language_code(self):
        http = _make_http()
        http.post.return_value = {}
        svc = self._make_service(http)
        svc.post_records(1, 1, ["businessName"], language_code="fr")
        http.post.assert_called_once_with(
            "/search/1/records/1",
            json=["businessName"],
            params={"languageCode": "fr"},
        )

    def test_post_preview_calls_correct_path(self):
        http = _make_http()
        http.post.return_value = []
        svc = self._make_service(http)
        svc.post_preview(5, ["businessName"])
        http.post.assert_called_once_with(
            "/search/5/preview",
            json=["businessName"],
            params=None,
        )

    def test_post_preview_with_language_code(self):
        http = _make_http()
        http.post.return_value = []
        svc = self._make_service(http)
        svc.post_preview(5, ["businessName"], language_code="de")
        http.post.assert_called_once_with(
            "/search/5/preview",
            json=["businessName"],
            params={"languageCode": "de"},
        )


# ---------------------------------------------------------------------------
# RecordService
# ---------------------------------------------------------------------------

class TestRecordService:
    def _make_service(self, http=None):
        from infobel_api.services.record import RecordService
        return RecordService(http or _make_http())

    def test_get_calls_correct_path(self):
        http = _make_http()
        http.get.return_value = {"uniqueID": "001"}
        svc = self._make_service(http)
        result = svc.get("GB", "001")
        http.get.assert_called_once_with("/record/GB/001")
        assert result == {"uniqueID": "001"}

    def test_get_partial_calls_correct_path(self):
        http = _make_http()
        http.get.return_value = {"uniqueID": "002"}
        svc = self._make_service(http)
        result = svc.get_partial("DE", "002")
        http.get.assert_called_once_with("/record/DE/002/partial")
        assert result == {"uniqueID": "002"}

    def test_get_with_different_country_codes(self):
        http = _make_http()
        http.get.return_value = {}
        svc = self._make_service(http)
        for cc in ["US", "FR", "JP", "BR"]:
            svc.get(cc, "xyz")
            assert http.get.call_args[0][0] == f"/record/{cc}/xyz"


# ---------------------------------------------------------------------------
# CategoriesService
# ---------------------------------------------------------------------------

class TestCategoriesService:
    def _make_service(self, http=None):
        from infobel_api.services.categories import CategoriesService
        return CategoriesService(http or _make_http())

    def test_get_infobel_calls_correct_path(self):
        http = _make_http()
        http.get.return_value = []
        svc = self._make_service(http)
        svc.get_infobel("en")
        http.get.assert_called_once_with("/categories/infobel/en")

    def test_get_infobel_children_calls_correct_path(self):
        http = _make_http()
        http.get.return_value = []
        svc = self._make_service(http)
        svc.get_infobel_children("A01", "fr")
        http.get.assert_called_once_with("/categories/infobel/A01/children/fr")

    def test_get_international_calls_correct_path(self):
        http = _make_http()
        http.get.return_value = []
        svc = self._make_service(http)
        svc.get_international("de")
        http.get.assert_called_once_with("/categories/international/de")

    def test_get_international_children_calls_correct_path(self):
        http = _make_http()
        http.get.return_value = []
        svc = self._make_service(http)
        svc.get_international_children("B02", "en")
        http.get.assert_called_once_with("/categories/international/B02/children/en")

    def test_get_local_calls_correct_path(self):
        http = _make_http()
        http.get.return_value = []
        svc = self._make_service(http)
        svc.get_local("FR", "fr")
        http.get.assert_called_once_with("/categories/local/FR/fr")

    def test_get_local_children_calls_correct_path(self):
        http = _make_http()
        http.get.return_value = []
        svc = self._make_service(http)
        svc.get_local_children("C03", "FR", "fr")
        http.get.assert_called_once_with("/categories/local/C03/children/FR/fr")

    def test_get_alt_international_calls_correct_path(self):
        http = _make_http()
        http.get.return_value = []
        svc = self._make_service(http)
        svc.get_alt_international("en")
        http.get.assert_called_once_with("/categories/altinternational/en")

    def test_get_alt_international_children_calls_correct_path(self):
        http = _make_http()
        http.get.return_value = []
        svc = self._make_service(http)
        svc.get_alt_international_children("D04", "en")
        http.get.assert_called_once_with("/categories/altinternational/D04/children/en")

    def test_get_infobel_by_level_calls_correct_path(self):
        http = _make_http()
        http.get.return_value = []
        svc = self._make_service(http)
        svc.get_infobel_by_level(2, "en")
        http.get.assert_called_once_with("/categories/infobel/level/2/en")

    def test_get_lineage_posts_correct_payload(self):
        http = _make_http()
        http.post.return_value = []
        svc = self._make_service(http)
        svc.get_lineage(["A01", "B02"], "en")
        http.post.assert_called_once_with(
            "/categories/lineage",
            json=["A01", "B02"],
            params={"languageCode": "en"},
        )

    def test_search_get_without_country_code(self):
        http = _make_http()
        http.get.return_value = [{"code": "A", "name": "Agri"}]
        svc = self._make_service(http)
        result = svc.search("en", "agri")
        http.get.assert_called_once_with("/categories/search/en/agri", params=None)
        assert result == [{"code": "A", "name": "Agri"}]

    def test_search_get_with_country_code(self):
        http = _make_http()
        http.get.return_value = []
        svc = self._make_service(http)
        svc.search("fr", "restaurant", country_code="FR")
        http.get.assert_called_once_with(
            "/categories/search/fr/restaurant",
            params={"countryCode": "FR"},
        )

    def test_search_multi_posts_country_codes(self):
        http = _make_http()
        http.post.return_value = []
        svc = self._make_service(http)
        svc.search_multi("en", "bakery", ["FR", "BE"])
        http.post.assert_called_once_with(
            "/categories/search/en/bakery",
            json=["FR", "BE"],
        )

    def test_search_keywords_deduplicates_by_code(self):
        http = _make_http()
        # Both keywords return overlapping results
        item_a = {"code": "A01", "name": "Agriculture"}
        item_b = {"code": "B02", "name": "Bakery"}
        http.get.side_effect = [
            [item_a, item_b],   # keyword 1
            [item_b, item_a],   # keyword 2 — duplicates
        ]
        svc = self._make_service(http)
        result = svc._search_keywords(["agri", "farm"], "en")
        assert len(result) == 2
        codes = {r["code"] for r in result}
        assert codes == {"A01", "B02"}

    def test_search_keywords_skips_empty_keywords(self):
        http = _make_http()
        http.get.return_value = [{"code": "X", "name": "X"}]
        svc = self._make_service(http)
        svc._search_keywords(["valid", "", "  "], "en")
        # Only "valid" should trigger a call; empty/whitespace skipped
        assert http.get.call_count == 1

    def test_search_keywords_fallback_key_when_no_code(self):
        http = _make_http()
        # Item without 'code' key
        item = {"name": "Plumbing", "description": "Pipe work"}
        http.get.return_value = [item]
        svc = self._make_service(http)
        result = svc._search_keywords(["plumbing"], "en")
        assert len(result) == 1

    def test_search_infobel_calls_search_keywords(self):
        http = _make_http()
        http.get.return_value = [{"code": "A", "name": "X"}]
        svc = self._make_service(http)
        result = svc.search_infobel(["bakery", "bread"], language_code="fr")
        assert http.get.call_count == 2
        assert len(result) >= 1

    def test_search_international_calls_search_keywords(self):
        http = _make_http()
        http.get.return_value = []
        svc = self._make_service(http)
        svc.search_international(["tech"], language_code="en")
        http.get.assert_called_once()

    def test_search_local_passes_country_code(self):
        http = _make_http()
        http.get.return_value = [{"code": "L1"}]
        svc = self._make_service(http)
        svc.search_local(["plomberie"], "FR", language_code="fr")
        call_args = http.get.call_args
        assert "FR" in call_args[1].get("params", {}).get("countryCode", "")

    def test_search_alt_international_calls_search_keywords(self):
        http = _make_http()
        http.get.return_value = []
        svc = self._make_service(http)
        svc.search_alt_international(["software"], language_code="en")
        http.get.assert_called_once()


# ---------------------------------------------------------------------------
# LocationsService
# ---------------------------------------------------------------------------

class TestLocationsService:
    def _make_service(self, http=None):
        from infobel_api.services.locations import LocationsService
        return LocationsService(http or _make_http())

    def test_get_cities_calls_correct_path(self):
        http = _make_http()
        http.get.return_value = []
        svc = self._make_service(http)
        svc.get_cities("GB")
        http.get.assert_called_once_with("/locations/cities/GB")

    def test_get_cities_by_region_calls_correct_path(self):
        http = _make_http()
        http.get.return_value = []
        svc = self._make_service(http)
        svc.get_cities_by_region("DE", "BY")
        http.get.assert_called_once_with("/locations/cities/DE/BY")

    def test_get_provinces_calls_correct_path(self):
        http = _make_http()
        http.get.return_value = []
        svc = self._make_service(http)
        svc.get_provinces("FR")
        http.get.assert_called_once_with("/locations/provinces/FR")

    def test_get_provinces_by_region_calls_correct_path(self):
        http = _make_http()
        http.get.return_value = []
        svc = self._make_service(http)
        svc.get_provinces_by_region("ES", "CAT")
        http.get.assert_called_once_with("/locations/provinces/ES/CAT")

    def test_get_regions_calls_correct_path(self):
        http = _make_http()
        http.get.return_value = []
        svc = self._make_service(http)
        svc.get_regions("IT")
        http.get.assert_called_once_with("/locations/regions/IT")

    def test_get_post_codes_calls_correct_path(self):
        http = _make_http()
        http.get.return_value = []
        svc = self._make_service(http)
        svc.get_post_codes("US")
        http.get.assert_called_once_with("/locations/postcodes/US")

    def test_get_lineage_without_language_code(self):
        http = _make_http()
        http.post.return_value = []
        svc = self._make_service(http)
        svc.get_lineage("GB", ["LON", "MAN"])
        http.post.assert_called_once_with(
            "/locations/GB/lineage",
            json=["LON", "MAN"],
            params=None,
        )

    def test_get_lineage_with_language_code(self):
        http = _make_http()
        http.post.return_value = []
        svc = self._make_service(http)
        svc.get_lineage("FR", ["PAR"], language_code="fr")
        http.post.assert_called_once_with(
            "/locations/FR/lineage",
            json=["PAR"],
            params={"languageCode": "fr"},
        )

    def test_search_without_language_code(self):
        http = _make_http()
        http.get.return_value = [{"code": "LON", "name": "London"}]
        svc = self._make_service(http)
        result = svc.search("GB", "London")
        http.get.assert_called_once_with("/locations/GB/search/London", params=None)
        assert result[0]["name"] == "London"

    def test_search_with_language_code(self):
        http = _make_http()
        http.get.return_value = []
        svc = self._make_service(http)
        svc.search("DE", "Munich", language_code="de")
        http.get.assert_called_once_with(
            "/locations/DE/search/Munich",
            params={"languageCode": "de"},
        )

    def test_search_multi_without_params(self):
        http = _make_http()
        http.post.return_value = []
        svc = self._make_service(http)
        svc.search_multi("Berlin")
        http.post.assert_called_once_with(
            "/locations/search/Berlin",
            json=None,
            params=None,
        )

    def test_search_multi_with_take_and_country_codes(self):
        http = _make_http()
        http.post.return_value = []
        svc = self._make_service(http)
        svc.search_multi("Paris", country_codes=["FR", "BE"], take=10)
        http.post.assert_called_once_with(
            "/locations/search/Paris",
            json=["FR", "BE"],
            params={"take": 10},
        )

    def test_search_keywords_deduplicates(self):
        http = _make_http()
        city_a = {"code": "LON", "name": "London"}
        city_b = {"code": "MAN", "name": "Manchester"}
        http.get.side_effect = [
            [city_a, city_b],
            [city_b],  # duplicate
        ]
        svc = self._make_service(http)
        result = svc.search_keywords(["London", "Manchester"], "GB")
        assert len(result) == 2

    def test_search_keywords_skips_empty(self):
        http = _make_http()
        http.get.return_value = [{"code": "LON"}]
        svc = self._make_service(http)
        svc.search_keywords(["London", "", "  "], "GB")
        assert http.get.call_count == 1

    def test_search_keywords_with_language_code(self):
        http = _make_http()
        http.get.return_value = []
        svc = self._make_service(http)
        svc.search_keywords(["München"], "DE", language_code="de")
        call_args = http.get.call_args
        assert call_args[1].get("params", {}).get("languageCode") == "de"


# ---------------------------------------------------------------------------
# CountriesService
# ---------------------------------------------------------------------------

class TestCountriesService:
    def _make_service(self, http=None):
        from infobel_api.services.countries import CountriesService
        return CountriesService(http or _make_http())

    def test_get_all_calls_correct_path(self):
        http = _make_http()
        http.get.return_value = [{"code": "GB"}, {"code": "DE"}]
        svc = self._make_service(http)
        result = svc.get_all()
        http.get.assert_called_once_with("/countries")
        assert len(result) == 2

    def test_get_all_returns_list(self):
        http = _make_http()
        http.get.return_value = []
        svc = self._make_service(http)
        result = svc.get_all()
        assert isinstance(result, list)


# ---------------------------------------------------------------------------
# UtilsService
# ---------------------------------------------------------------------------

class TestUtilsService:
    def _make_service(self, http=None):
        from infobel_api.services.utils import UtilsService
        return UtilsService(http or _make_http())

    @pytest.mark.parametrize("method,expected_path", [
        ("get_languages", "/utils/languages"),
        ("get_reliability_codes", "/utils/reliabilitycodes"),
        ("get_status_codes", "/utils/statuscodes"),
        ("get_geo_levels", "/utils/geolevels"),
        ("get_import_export_agent_codes", "/utils/importexportagentcodes"),
        ("get_currencies", "/utils/currencies"),
        ("get_sorting_orders", "/utils/sortingorders"),
        ("get_technographical_tags", "/utils/technographicaltags"),
        ("get_executive_tags", "/utils/executivetags"),
        ("get_website_status_flags", "/utils/websitestatusflags"),
        ("get_social_links", "/utils/sociallinks"),
        ("get_gender_codes", "/utils/gendercodes"),
        ("get_title_codes", "/utils/titlecodes"),
        ("get_local_activity_type_codes", "/utils/localactivitytypecodes"),
    ])
    def test_simple_get_endpoints(self, method, expected_path):
        http = _make_http()
        http.get.return_value = []
        svc = self._make_service(http)
        getattr(svc, method)()
        http.get.assert_called_once_with(expected_path)

    def test_get_legal_status_codes_with_country(self):
        http = _make_http()
        http.get.return_value = []
        svc = self._make_service(http)
        svc.get_legal_status_codes("DE")
        http.get.assert_called_once_with("/utils/legalstatuscodes/DE")

    def test_get_national_id_types_with_country(self):
        http = _make_http()
        http.get.return_value = []
        svc = self._make_service(http)
        svc.get_national_id_types("GB")
        http.get.assert_called_once_with("/utils/nationalidentificationtypecodes/GB")


# ---------------------------------------------------------------------------
# TestService
# ---------------------------------------------------------------------------

class TestTestService:
    def _make_service(self, http=None):
        from infobel_api.services.test import TestService
        return TestService(http or _make_http())

    def test_hello_calls_correct_path(self):
        http = _make_http()
        http.get.return_value = {"message": "hello"}
        svc = self._make_service(http)
        result = svc.hello()
        http.get.assert_called_once_with("/test/hello")
        assert result == {"message": "hello"}
