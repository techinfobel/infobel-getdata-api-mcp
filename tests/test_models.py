"""Tests for all Pydantic models (auth, common, search)."""
from __future__ import annotations

from datetime import datetime, timedelta

import pytest


# ---------------------------------------------------------------------------
# TokenResponse
# ---------------------------------------------------------------------------

class TestTokenResponse:
    def test_basic_creation(self):
        from infobel_api.models.auth import TokenResponse
        t = TokenResponse(access_token="abc123")
        assert t.access_token == "abc123"
        assert t.token_type == "Bearer"
        assert t.expires_in == 3600

    def test_expires_at_auto_calculated(self):
        from infobel_api.models.auth import TokenResponse
        t = TokenResponse(access_token="tok")
        assert t.expires_at is not None
        expected = t.issued_at + timedelta(seconds=t.expires_in)
        # Allow a 1-second tolerance
        assert abs((t.expires_at - expected).total_seconds()) < 1

    def test_expires_at_custom_expires_in(self):
        from infobel_api.models.auth import TokenResponse
        t = TokenResponse(access_token="tok", expires_in=7200)
        delta = (t.expires_at - t.issued_at).total_seconds()
        assert abs(delta - 7200) < 1

    def test_is_expired_false_for_new_token(self):
        from infobel_api.models.auth import TokenResponse
        t = TokenResponse(access_token="tok")
        assert t.is_expired is False

    def test_is_expired_true_for_old_token(self):
        from infobel_api.models.auth import TokenResponse
        past = datetime.now() - timedelta(hours=2)
        t = TokenResponse(
            access_token="tok",
            issued_at=past,
            expires_at=past + timedelta(seconds=3600),
        )
        assert t.is_expired is True

    def test_needs_refresh_false_when_plenty_of_time(self):
        from infobel_api.models.auth import TokenResponse
        t = TokenResponse(access_token="tok", expires_in=3600)
        assert t.needs_refresh(300) is False

    def test_needs_refresh_true_when_expiring_soon(self):
        from infobel_api.models.auth import TokenResponse
        soon = datetime.now() + timedelta(seconds=60)
        t = TokenResponse(access_token="tok", expires_at=soon)
        assert t.needs_refresh(300) is True

    def test_needs_refresh_boundary(self):
        from infobel_api.models.auth import TokenResponse
        # Expires exactly at threshold → needs refresh
        threshold = 300
        expires_at = datetime.now() + timedelta(seconds=threshold - 1)
        t = TokenResponse(access_token="tok", expires_at=expires_at)
        assert t.needs_refresh(threshold) is True

    def test_from_api_response_full(self):
        from infobel_api.models.auth import TokenResponse
        data = {
            "access_token": "mytoken",
            "token_type": "Bearer",
            "expires_in": 1800,
        }
        t = TokenResponse.from_api_response(data)
        assert t.access_token == "mytoken"
        assert t.token_type == "Bearer"
        assert t.expires_in == 1800

    def test_from_api_response_minimal(self):
        from infobel_api.models.auth import TokenResponse
        t = TokenResponse.from_api_response({"access_token": "tok"})
        assert t.access_token == "tok"
        assert t.token_type == "Bearer"
        assert t.expires_in == 3600

    def test_from_api_response_missing_token_raises(self):
        from infobel_api.models.auth import TokenResponse
        with pytest.raises(KeyError):
            TokenResponse.from_api_response({"token_type": "Bearer"})


# ---------------------------------------------------------------------------
# CoordinateOption
# ---------------------------------------------------------------------------

class TestCoordinateOption:
    def test_create_with_python_names(self):
        from infobel_api.models.common import CoordinateOption
        c = CoordinateOption(Latitude=51.5, Longitude=-0.1)
        assert c.latitude == 51.5
        assert c.longitude == -0.1
        assert c.distance == 100  # default

    def test_create_with_custom_distance(self):
        from infobel_api.models.common import CoordinateOption
        c = CoordinateOption(Latitude=48.8, Longitude=2.35, Distance=500)
        assert c.distance == 500

    def test_serializes_with_aliases(self):
        from infobel_api.models.common import CoordinateOption
        c = CoordinateOption(Latitude=1.0, Longitude=2.0, Distance=250)
        d = c.model_dump(by_alias=True)
        assert d["Latitude"] == 1.0
        assert d["Longitude"] == 2.0
        assert d["Distance"] == 250


# ---------------------------------------------------------------------------
# SearchInput
# ---------------------------------------------------------------------------

class TestSearchInput:
    def test_defaults(self):
        from infobel_api.models.search import SearchInput
        s = SearchInput()
        assert s.data_type == "Business"
        assert s.page_size == 20
        assert s.return_first_page is False
        assert s.country_codes is None

    def test_to_api_payload_excludes_none(self):
        from infobel_api.models.search import SearchInput
        s = SearchInput(country_codes=["GB"])
        payload = s.to_api_payload()
        assert "CountryCodes" in payload
        assert "BusinessName" not in payload
        # None fields should not appear
        for v in payload.values():
            assert v is not None

    def test_to_api_payload_uses_aliases(self):
        from infobel_api.models.search import SearchInput
        s = SearchInput(
            country_codes=["DE"],
            business_name=["Siemens"],
            has_email=True,
        )
        payload = s.to_api_payload()
        assert "CountryCodes" in payload
        assert "BusinessName" in payload
        assert "HasEmail" in payload
        # snake_case keys should NOT appear
        assert "country_codes" not in payload
        assert "business_name" not in payload

    def test_coordinate_options_serialized(self):
        from infobel_api.models.search import SearchInput
        from infobel_api.models.common import CoordinateOption
        coord = CoordinateOption(Latitude=51.5, Longitude=-0.1, Distance=200)
        s = SearchInput(coordinate_options=[coord])
        payload = s.to_api_payload()
        assert "CoordinateOptions" in payload
        assert payload["CoordinateOptions"][0]["Latitude"] == 51.5

    def test_return_first_page_included_when_false(self):
        from infobel_api.models.search import SearchInput
        s = SearchInput(return_first_page=False)
        payload = s.to_api_payload()
        # False is not None so it's included
        assert "ReturnFirstPage" in payload
        assert payload["ReturnFirstPage"] is False

    def test_all_none_gives_minimal_payload(self):
        from infobel_api.models.search import SearchInput
        s = SearchInput(
            data_type=None,
            page_size=None,
            return_first_page=None,
        )
        payload = s.to_api_payload()
        assert "DataType" not in payload
        assert "PageSize" not in payload

    def test_populate_by_alias(self):
        from infobel_api.models.search import SearchInput
        # Should be possible to instantiate using aliases
        s = SearchInput(**{"CountryCodes": ["FR"]})
        assert s.country_codes == ["FR"]


# ---------------------------------------------------------------------------
# SearchResponse
# ---------------------------------------------------------------------------

class TestSearchResponse:
    def test_creation_with_search_id(self):
        from infobel_api.models.search import SearchResponse
        r = SearchResponse(**{"searchId": 42, "counts": {"total": 100}})
        assert r.search_id == 42
        assert r.counts == {"total": 100}

    def test_total_property(self):
        from infobel_api.models.search import SearchResponse
        r = SearchResponse(counts={"total": 250})
        assert r.total == 250

    def test_total_missing_in_counts(self):
        from infobel_api.models.search import SearchResponse
        r = SearchResponse(counts={})
        assert r.total == 0

    def test_first_page_records_default_empty(self):
        from infobel_api.models.search import SearchResponse
        r = SearchResponse()
        assert r.first_page_records == []

    def test_first_page_records_populated(self):
        from infobel_api.models.search import SearchResponse
        records = [{"uniqueID": "001"}, {"uniqueID": "002"}]
        r = SearchResponse(**{"firstPageRecords": records})
        assert len(r.first_page_records) == 2


# ---------------------------------------------------------------------------
# PaginatedResponse
# ---------------------------------------------------------------------------

class TestPaginatedResponse:
    def test_defaults(self):
        from infobel_api.models.search import PaginatedResponse
        r = PaginatedResponse()
        assert r.page == 0
        assert r.record_count == 0
        assert r.total_record_count == 0
        assert r.records == []
        assert r.search_id is None

    def test_with_data(self):
        from infobel_api.models.search import PaginatedResponse
        r = PaginatedResponse(
            **{
                "searchId": 99,
                "page": 2,
                "recordCount": 20,
                "totalRecordCount": 200,
                "records": [{"uniqueID": "x"}],
            }
        )
        assert r.search_id == 99
        assert r.page == 2
        assert r.record_count == 20
        assert r.total_record_count == 200
        assert len(r.records) == 1

    def test_populate_by_name(self):
        from infobel_api.models.search import PaginatedResponse
        r = PaginatedResponse(record_count=5, total_record_count=50)
        assert r.record_count == 5
        assert r.total_record_count == 50
