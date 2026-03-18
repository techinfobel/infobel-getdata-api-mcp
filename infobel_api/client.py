"""Infobel API client — thin facade over service namespaces."""

from __future__ import annotations

from .config import InfobelSettings
from .auth import AuthenticationHandler
from ._http import HttpClient
from .services import (
    SearchService,
    CategoriesService,
    LocationsService,
    RecordService,
    UtilsService,
    CountriesService,
    TestService,
)


class InfobelClient:
    """High-level client for the Infobel business-search API.

    Usage::

        client = InfobelClient(username="...", password="...")
        result = client.search.search(country_codes="GB", business_name="Acme")
        client.close()
    """

    def __init__(
        self,
        username: str | None = None,
        password: str | None = None,
        *,
        base_url: str | None = None,
    ):
        overrides: dict[str, str] = {}
        if username is not None:
            overrides["username"] = username
        if password is not None:
            overrides["password"] = password
        if base_url is not None:
            overrides["base_url"] = base_url

        self._settings = InfobelSettings(**overrides)
        self._auth = AuthenticationHandler(self._settings)
        self._http = HttpClient(self._settings, self._auth)

        self.search = SearchService(self._http)
        self.categories = CategoriesService(self._http)
        self.locations = LocationsService(self._http)
        self.record = RecordService(self._http)
        self.utils = UtilsService(self._http)
        self.countries = CountriesService(self._http)
        self.test = TestService(self._http)

    def close(self) -> None:
        self._http.close()

    def __enter__(self) -> InfobelClient:
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()
