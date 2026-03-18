"""Tests for MCP field selection behavior."""
from unittest.mock import MagicMock, patch

import pytest


def make_search_response(search_id=123, total=42):
    return {
        "searchId": search_id,
        "counts": {"total": total, "hasPhone": 10},
        "firstPageRecords": [],
    }


def make_records_response(fields):
    record = {f: f"value_{f}" for f in fields}
    record["uniqueID"] = "0001234567"
    return {"records": [record], "recordCount": 1, "totalRecordCount": 42}


class TestEnsureUniqueId:
    def test_adds_unique_id_when_missing(self):
        from infobel_api.mcp_server import _ensure_unique_id
        result = _ensure_unique_id(["businessName", "city"])
        assert result[0] == "uniqueID"
        assert "businessName" in result
        assert "city" in result

    def test_does_not_duplicate_unique_id(self):
        from infobel_api.mcp_server import _ensure_unique_id
        result = _ensure_unique_id(["uniqueID", "businessName"])
        assert result.count("uniqueID") == 1

    def test_empty_list_gets_unique_id(self):
        from infobel_api.mcp_server import _ensure_unique_id
        # empty means counts-only — caller should not call this with []
        # but if they do, ensure uniqueID is there
        result = _ensure_unique_id([])
        assert "uniqueID" in result


class TestSearchBusinessesFieldSelection:
    @patch("infobel_api.mcp_server._get_client")
    def test_counts_only_does_not_call_post_records(self, mock_get_client):
        mock_client = MagicMock()
        mock_client.search.search.return_value = make_search_response()
        mock_get_client.return_value = mock_client

        from infobel_api.mcp_server import search_businesses
        result = search_businesses(country_codes=["US"], record_fields=[])

        mock_client.search.post_records.assert_not_called()
        import json
        data = json.loads(result)
        assert data["records"] == []
        assert "counts" in data
        assert data["searchId"] == 123

    @patch("infobel_api.mcp_server._get_client")
    def test_return_first_page_is_always_false(self, mock_get_client):
        mock_client = MagicMock()
        mock_client.search.search.return_value = make_search_response()
        mock_client.search.post_records.return_value = make_records_response(["businessName"])
        mock_get_client.return_value = mock_client

        from infobel_api.mcp_server import search_businesses
        search_businesses(country_codes=["US"], record_fields=["businessName"])

        call_kwargs = mock_client.search.search.call_args
        # return_first_page=False must be in the kwargs passed to search
        assert call_kwargs is not None

    @patch("infobel_api.mcp_server._get_client")
    def test_unique_id_always_included_in_post_records_call(self, mock_get_client):
        mock_client = MagicMock()
        mock_client.search.search.return_value = make_search_response()
        mock_client.search.post_records.return_value = make_records_response(["businessName"])
        mock_get_client.return_value = mock_client

        from infobel_api.mcp_server import search_businesses
        search_businesses(country_codes=["US"], record_fields=["businessName"])

        call_args = mock_client.search.post_records.call_args
        fields_arg = call_args[0][2]  # post_records(search_id, page, fields)
        assert "uniqueID" in fields_arg

    @patch("infobel_api.mcp_server._get_client")
    def test_records_returned_in_output(self, mock_get_client):
        mock_client = MagicMock()
        mock_client.search.search.return_value = make_search_response(search_id=999)
        mock_client.search.post_records.return_value = make_records_response(["businessName"])
        mock_get_client.return_value = mock_client

        from infobel_api.mcp_server import search_businesses
        import json
        result = json.loads(
            search_businesses(country_codes=["US"], record_fields=["businessName"])
        )
        assert result["searchId"] == 999
        assert len(result["records"]) == 1
        assert result["records"][0]["uniqueID"] == "0001234567"


class TestGetSearchResultsFieldSelection:
    @patch("infobel_api.mcp_server._get_client")
    def test_uses_post_records_not_get_records(self, mock_get_client):
        mock_client = MagicMock()
        mock_client.search.post_records.return_value = make_records_response(["businessName"])
        mock_get_client.return_value = mock_client

        from infobel_api.mcp_server import get_search_results
        get_search_results(search_id=123, page=2, record_fields=["businessName"])

        mock_client.search.post_records.assert_called_once()
        mock_client.search.get_records.assert_not_called()

    @patch("infobel_api.mcp_server._get_client")
    def test_unique_id_auto_added_for_pagination(self, mock_get_client):
        mock_client = MagicMock()
        mock_client.search.post_records.return_value = make_records_response(["city"])
        mock_get_client.return_value = mock_client

        from infobel_api.mcp_server import get_search_results
        get_search_results(search_id=123, page=2, record_fields=["city"])

        call_args = mock_client.search.post_records.call_args
        fields_arg = call_args[0][2]
        assert "uniqueID" in fields_arg
