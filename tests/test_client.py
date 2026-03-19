"""Tests for InfobelClient facade."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest


class TestInfobelClientConstruction:
    def test_default_construction_uses_env_or_empty_creds(self):
        from infobel_api.client import InfobelClient
        client = InfobelClient()
        assert client._settings is not None
        client.close()

    def test_credentials_override(self):
        from infobel_api.client import InfobelClient
        client = InfobelClient(username="alice", password="secret")
        assert client._settings.username == "alice"
        assert client._settings.password == "secret"
        client.close()

    def test_base_url_override(self):
        from infobel_api.client import InfobelClient
        client = InfobelClient(base_url="https://staging.test.com")
        assert client._settings.base_url == "https://staging.test.com"
        client.close()

    def test_all_overrides(self):
        from infobel_api.client import InfobelClient
        client = InfobelClient(
            username="bob",
            password="pw",
            base_url="https://local.test",
        )
        assert client._settings.username == "bob"
        assert client._settings.base_url == "https://local.test"
        client.close()


class TestInfobelClientServiceNamespaces:
    def setup_method(self):
        from infobel_api.client import InfobelClient
        self.client = InfobelClient()

    def teardown_method(self):
        self.client.close()

    def test_search_service_present(self):
        from infobel_api.services.search import SearchService
        assert isinstance(self.client.search, SearchService)

    def test_categories_service_present(self):
        from infobel_api.services.categories import CategoriesService
        assert isinstance(self.client.categories, CategoriesService)

    def test_locations_service_present(self):
        from infobel_api.services.locations import LocationsService
        assert isinstance(self.client.locations, LocationsService)

    def test_record_service_present(self):
        from infobel_api.services.record import RecordService
        assert isinstance(self.client.record, RecordService)

    def test_utils_service_present(self):
        from infobel_api.services.utils import UtilsService
        assert isinstance(self.client.utils, UtilsService)

    def test_countries_service_present(self):
        from infobel_api.services.countries import CountriesService
        assert isinstance(self.client.countries, CountriesService)

    def test_test_service_present(self):
        from infobel_api.services.test import TestService
        assert isinstance(self.client.test, TestService)

    def test_all_services_share_same_http_client(self):
        # All services must use the same underlying HttpClient instance
        http = self.client._http
        assert self.client.search._http is http
        assert self.client.categories._http is http
        assert self.client.locations._http is http
        assert self.client.record._http is http
        assert self.client.utils._http is http
        assert self.client.countries._http is http
        assert self.client.test._http is http


class TestInfobelClientLifecycle:
    def test_close_closes_http_client(self):
        from infobel_api.client import InfobelClient
        client = InfobelClient()
        client._http = MagicMock()
        client.close()
        client._http.close.assert_called_once()

    def test_context_manager_calls_close(self):
        from infobel_api.client import InfobelClient
        with InfobelClient() as client:
            client._http = MagicMock()
            http_mock = client._http
        http_mock.close.assert_called_once()

    def test_context_manager_returns_client(self):
        from infobel_api.client import InfobelClient
        with InfobelClient() as client:
            assert isinstance(client, InfobelClient)

    def test_context_manager_closes_on_exception(self):
        from infobel_api.client import InfobelClient
        mock_http = MagicMock()
        try:
            with InfobelClient() as client:
                client._http = mock_http
                raise ValueError("test error")
        except ValueError:
            pass
        mock_http.close.assert_called_once()


class TestInfobelClientSettings:
    def test_settings_are_infobel_settings_instance(self):
        from infobel_api.client import InfobelClient
        from infobel_api.config import InfobelSettings
        client = InfobelClient()
        assert isinstance(client._settings, InfobelSettings)
        client.close()

    def test_auth_handler_initialized(self):
        from infobel_api.client import InfobelClient
        from infobel_api.auth import AuthenticationHandler
        client = InfobelClient()
        assert isinstance(client._auth, AuthenticationHandler)
        client.close()

    def test_http_client_initialized(self):
        from infobel_api.client import InfobelClient
        from infobel_api._http import HttpClient
        client = InfobelClient()
        assert isinstance(client._http, HttpClient)
        client.close()
