"""Infobel API service namespaces."""

from .search import SearchService
from .categories import CategoriesService
from .locations import LocationsService
from .record import RecordService
from .utils import UtilsService
from .countries import CountriesService
from .test import TestService

__all__ = [
    "SearchService",
    "CategoriesService",
    "LocationsService",
    "RecordService",
    "UtilsService",
    "CountriesService",
    "TestService",
]
