"""Tests for task tools (count_businesses, resolvers) and zero-result diagnosis."""
from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest


def make_search_response(search_id=123, total=42, **extra_counts):
    counts = {"total": total, "hasPhone": 10}
    counts.update(extra_counts)
    return {"searchId": search_id, "counts": counts, "firstPageRecords": []}


# ---------------------------------------------------------------------------
# Knowledge helpers
# ---------------------------------------------------------------------------

class TestKnowledge:
    def test_code_warning_for_known_conflation(self):
        from infobel_api.knowledge import category_code_warnings
        items = [{"code": "018513", "name": "Department Stores"}]
        warnings = category_code_warnings(items)
        assert len(warnings) == 1
        assert "018513" in warnings[0]

    def test_no_warning_for_clean_codes(self):
        from infobel_api.knowledge import category_code_warnings
        assert category_code_warnings([{"code": "012345", "name": "Bakeries"}]) == []

    def test_code_warnings_deduplicated(self):
        from infobel_api.knowledge import category_code_warnings
        items = [{"code": "017102"}, {"code": "017102"}]
        assert len(category_code_warnings(items)) == 1

    def test_keyword_caution_substring_match(self):
        from infobel_api.knowledge import category_keyword_cautions
        cautions = category_keyword_cautions(["Shopping Mall"])
        assert len(cautions) == 1
        assert "018513" in cautions[0]

    def test_keyword_caution_no_false_positive(self):
        from infobel_api.knowledge import category_keyword_cautions
        assert category_keyword_cautions(["bakery"]) == []


# ---------------------------------------------------------------------------
# count_businesses
# ---------------------------------------------------------------------------

class TestCountBusinesses:
    @patch("infobel_api.mcp_server._get_client")
    def test_single_search_counts_only(self, mock_get_client):
        mock_client = MagicMock()
        mock_client.search.search.return_value = make_search_response(search_id=7, total=99)
        mock_get_client.return_value = mock_client

        from infobel_api.mcp_server import count_businesses
        data = json.loads(count_businesses(country_codes=["GB", "DE"]))

        assert data["searchId"] == 7
        assert data["counts"]["total"] == 99
        assert data["filters"]["country_codes"] == ["GB", "DE"]
        mock_client.search.post_records.assert_not_called()
        kwargs = mock_client.search.search.call_args[1]
        assert kwargs["country_codes"] == ["GB", "DE"]
        assert kwargs["return_first_page"] is False

    @patch("infobel_api.mcp_server._get_client")
    def test_has_website_bool_maps_to_presence_type(self, mock_get_client):
        mock_client = MagicMock()
        mock_client.search.search.return_value = make_search_response()
        mock_get_client.return_value = mock_client

        from infobel_api.mcp_server import count_businesses
        count_businesses(country_codes=["GB"], has_website=True)
        assert mock_client.search.search.call_args[1]["has_website"] == 1

        count_businesses(country_codes=["GB"], has_website=False)
        assert mock_client.search.search.call_args[1]["has_website"] == 2

    @patch("infobel_api.mcp_server._get_client")
    def test_group_by_country_fans_out_and_sums(self, mock_get_client):
        totals = {"GB": 30, "DE": 50, "FR": 20}
        mock_client = MagicMock()

        def _search(**kwargs):
            cc = kwargs["country_codes"][0]
            return make_search_response(search_id=hash(cc) % 1000, total=totals[cc])

        mock_client.search.search.side_effect = _search
        mock_get_client.return_value = mock_client

        from infobel_api.mcp_server import count_businesses
        data = json.loads(
            count_businesses(country_codes=["GB", "DE", "FR"], group_by_country=True)
        )

        assert data["group_by"] == "country"
        assert data["total_all_countries"] == 100
        assert [r["country"] for r in data["rows"]] == ["DE", "GB", "FR"]  # sorted by total
        assert all("searchId" in r for r in data["rows"])
        assert mock_client.search.search.call_count == 3

    @patch("infobel_api.mcp_server._get_client")
    def test_group_by_single_country_stays_single_search(self, mock_get_client):
        mock_client = MagicMock()
        mock_client.search.search.return_value = make_search_response()
        mock_get_client.return_value = mock_client

        from infobel_api.mcp_server import count_businesses
        data = json.loads(count_businesses(country_codes=["GB"], group_by_country=True))
        assert "searchId" in data
        assert mock_client.search.search.call_count == 1

    @patch("infobel_api.mcp_server._get_client")
    def test_api_error_returns_error_json(self, mock_get_client):
        from infobel_api.exceptions import InfobelAPIError
        mock_client = MagicMock()
        mock_client.search.search.side_effect = InfobelAPIError("boom", status_code=400)
        mock_get_client.return_value = mock_client

        from infobel_api.mcp_server import count_businesses
        data = json.loads(count_businesses(country_codes=["GB"]))
        assert "error" in data
        assert data["status_code"] == 400


# ---------------------------------------------------------------------------
# Zero-result diagnosis
# ---------------------------------------------------------------------------

class TestZeroResultDiagnosis:
    @patch("infobel_api.mcp_server._get_client")
    def test_single_filter_group_returns_note_without_probes(self, mock_get_client):
        mock_client = MagicMock()
        mock_client.search.search.return_value = make_search_response(total=0)
        mock_get_client.return_value = mock_client

        from infobel_api.mcp_server import count_businesses
        data = json.loads(count_businesses(country_codes=["GB"], business_name=["Nonexistent"]))

        assert data["counts"]["total"] == 0
        assert "note" in data["diagnosis"]
        # base search only — a single present group is never probed
        assert mock_client.search.search.call_count == 1

    @patch("infobel_api.mcp_server._get_client")
    def test_probes_identify_blocking_filter_group(self, mock_get_client):
        mock_client = MagicMock()

        def _search(**kwargs):
            # Results exist only once the business_name filter is removed.
            if "business_name" in kwargs:
                return make_search_response(total=0)
            return make_search_response(total=55)

        mock_client.search.search.side_effect = _search
        mock_get_client.return_value = mock_client

        from infobel_api.mcp_server import count_businesses
        data = json.loads(count_businesses(
            country_codes=["GB"],
            business_name=["Misspelled Ltd"],
            city_codes=["LON01"],
        ))

        diagnosis = data["diagnosis"]
        assert diagnosis["likely_blocking_filters"] == ["business_name"]
        probe_groups = {p["removed_filter_group"] for p in diagnosis["probes"]}
        assert probe_groups == {"business_name", "location"}
        # base search + one probe per present group
        assert mock_client.search.search.call_count == 3

    @patch("infobel_api.mcp_server._get_client")
    def test_no_diagnosis_when_no_filter_groups(self, mock_get_client):
        mock_client = MagicMock()
        mock_client.search.search.return_value = make_search_response(total=0)
        mock_get_client.return_value = mock_client

        from infobel_api.mcp_server import count_businesses
        data = json.loads(count_businesses(country_codes=["GB"]))
        assert "diagnosis" not in data

    @patch("infobel_api.mcp_server._get_client")
    def test_search_businesses_attaches_diagnosis_and_skips_page_fetch(self, mock_get_client):
        mock_client = MagicMock()
        mock_client.search.search.return_value = make_search_response(total=0)
        mock_get_client.return_value = mock_client

        from infobel_api.mcp_server import search_businesses
        data = json.loads(search_businesses(
            country_codes=["GB"],
            record_fields=["businessName"],
            business_name=["Ghost Corp"],
        ))

        assert data["records"] == []
        assert "diagnosis" in data
        mock_client.search.post_records.assert_not_called()


# ---------------------------------------------------------------------------
# resolve_categories
# ---------------------------------------------------------------------------

class TestResolveCategories:
    def _client(self):
        client = MagicMock()
        client.categories.search_infobel.return_value = [
            {"code": "018513", "name": "Department Stores & Shopping Centres"}
        ]
        client.categories.search_international.return_value = [
            {"code": "4711", "name": "Retail sale in non-specialised stores"}
        ]
        client.categories.search_alt_international.return_value = [
            {"code": "47.19", "name": "Other retail sale in non-specialised stores"}
        ]
        client.categories.search_local.return_value = [
            {"code": "5311", "name": "Department stores"}
        ]
        return client

    @patch("infobel_api.mcp_server._get_client")
    def test_systems_named_with_search_parameters(self, mock_get_client):
        mock_get_client.return_value = self._client()

        from infobel_api.mcp_server import resolve_categories
        data = json.loads(resolve_categories(keywords=["department store"]))

        assert data["systems"]["infobel"]["search_parameter"] == "infobel_codes"
        assert data["systems"]["international_isic"]["search_parameter"] == "international_codes"
        assert data["systems"]["nace"]["search_parameter"] == "alt_international_codes"
        assert "local" not in data["systems"]

    @patch("infobel_api.mcp_server._get_client")
    def test_local_system_included_with_country_code(self, mock_get_client):
        client = self._client()
        mock_get_client.return_value = client

        from infobel_api.mcp_server import resolve_categories
        data = json.loads(resolve_categories(keywords=["department store"], country_code="US"))

        assert data["systems"]["local"]["search_parameter"] == "local_codes"
        client.categories.search_local.assert_called_once_with(["department store"], "US", "en")

    @patch("infobel_api.mcp_server._get_client")
    def test_conflation_warnings_from_keywords_and_codes(self, mock_get_client):
        mock_get_client.return_value = self._client()

        from infobel_api.mcp_server import resolve_categories
        data = json.loads(resolve_categories(keywords=["shopping mall"]))

        # keyword caution + returned-code conflation, both mentioning 018513
        assert any("018513" in w for w in data["warnings"])
        assert len(data["warnings"]) == 2

    @patch("infobel_api.mcp_server._get_client")
    def test_one_failing_system_does_not_break_the_rest(self, mock_get_client):
        from infobel_api.exceptions import InfobelAPIError
        client = self._client()
        client.categories.search_international.side_effect = InfobelAPIError("down", status_code=500)
        mock_get_client.return_value = client

        from infobel_api.mcp_server import resolve_categories
        data = json.loads(resolve_categories(keywords=["retail"]))

        assert data["systems"]["international_isic"]["matches"] == []
        assert "error" in data["systems"]["international_isic"]
        assert data["systems"]["infobel"]["matches"]


# ---------------------------------------------------------------------------
# resolve_location
# ---------------------------------------------------------------------------

class TestResolveLocation:
    @patch("infobel_api.mcp_server._get_client")
    def test_groups_by_type_with_filter_parameter(self, mock_get_client):
        mock_client = MagicMock()
        mock_client.locations.search_keywords.return_value = [
            {"type": "City", "code": "SP001", "name": "São Paulo"},
            {"type": "Province", "code": "SP", "name": "São Paulo"},
        ]
        mock_get_client.return_value = mock_client

        from infobel_api.mcp_server import resolve_location
        data = json.loads(resolve_location(text="São Paulo", country_code="BR"))

        assert data["location_types"]["City"]["search_parameter"] == "city_codes"
        assert data["location_types"]["Province"]["search_parameter"] == "province_codes"

    @patch("infobel_api.mcp_server._get_client")
    def test_ambiguity_warning_when_multiple_levels_match(self, mock_get_client):
        mock_client = MagicMock()
        mock_client.locations.search_keywords.return_value = [
            {"type": "City", "code": "SP001", "name": "São Paulo"},
            {"type": "Province", "code": "SP", "name": "São Paulo"},
        ]
        mock_get_client.return_value = mock_client

        from infobel_api.mcp_server import resolve_location
        data = json.loads(resolve_location(text="São Paulo", country_code="BR"))
        assert len(data["warnings"]) == 1
        assert "more than one location level" in data["warnings"][0]

    @patch("infobel_api.mcp_server._get_client")
    def test_single_level_has_no_ambiguity_warning(self, mock_get_client):
        mock_client = MagicMock()
        mock_client.locations.search_keywords.return_value = [
            {"type": "City", "code": "MUC01", "name": "München"},
        ]
        mock_get_client.return_value = mock_client

        from infobel_api.mcp_server import resolve_location
        data = json.loads(resolve_location(text="Munich", country_code="DE"))
        assert data["warnings"] == []

    @patch("infobel_api.mcp_server._get_client")
    def test_no_match_returns_spelling_warning(self, mock_get_client):
        mock_client = MagicMock()
        mock_client.locations.search_keywords.return_value = []
        mock_get_client.return_value = mock_client

        from infobel_api.mcp_server import resolve_location
        data = json.loads(resolve_location(text="Munchen", country_code="DE"))
        assert data["location_types"] == {}
        assert any("spelling" in w for w in data["warnings"])

    @patch("infobel_api.mcp_server._get_client")
    def test_unknown_type_reported_without_filter(self, mock_get_client):
        mock_client = MagicMock()
        mock_client.locations.search_keywords.return_value = [
            {"type": "Locality", "code": "X1", "name": "Somewhere"},
        ]
        mock_get_client.return_value = mock_client

        from infobel_api.mcp_server import resolve_location
        data = json.loads(resolve_location(text="Somewhere", country_code="BE"))
        assert data["location_types"]["Locality"]["search_parameter"] == (
            "no direct search filter for this type"
        )


# ---------------------------------------------------------------------------
# Parallel keyword fan-out in services
# ---------------------------------------------------------------------------

class TestParallelKeywordFanout:
    def test_categories_multi_keyword_parallel_dedup_and_order(self):
        from infobel_api.services.categories import CategoriesService

        http = MagicMock()

        def _get(path, params=None, **kwargs):
            if path.endswith("/alpha"):
                return {"infobel": [{"code": "A", "name": "First"}, {"code": "B", "name": "Shared"}]}
            if path.endswith("/beta"):
                return {"infobel": [{"code": "B", "name": "Shared"}, {"code": "C", "name": "Third"}]}
            return {"infobel": []}

        http.get.side_effect = _get
        svc = CategoriesService(http)
        results = svc.search_infobel(["alpha", "beta"])

        assert [r["code"] for r in results] == ["A", "B", "C"]
        assert http.get.call_count == 2

    def test_categories_blank_keywords_skipped(self):
        from infobel_api.services.categories import CategoriesService
        http = MagicMock()
        svc = CategoriesService(http)
        assert svc.search_infobel(["", "  "]) == []
        http.get.assert_not_called()

    def test_locations_multi_keyword_parallel_dedup(self):
        from infobel_api.services.locations import LocationsService

        http = MagicMock()

        def _get(path, params=None, **kwargs):
            if path.endswith("/munich"):
                return {"cities": [{"code": "MUC01", "type": "City"}]}
            if path.endswith("/bavaria"):
                return {"provinces": [{"code": "BY", "type": "Province"}], "cities": [{"code": "MUC01", "type": "City"}]}
            return {}

        http.get.side_effect = _get
        svc = LocationsService(http)
        results = svc.search_keywords(["munich", "bavaria"], "DE")

        assert [r["code"] for r in results] == ["MUC01", "BY"]
        assert http.get.call_count == 2
