"""Flatten Infobel API records to a standard 482-column schema.

This module provides the pure data-transform layer for converting nested
API records into a flat dictionary / DataFrame structure. It contains no
I/O, CLI, or file-writing logic — those live in downstream consumers.

Public API
----------
EXPECTED_COLUMNS   : list[str]  — ordered list of all 482 column names
convert_record_to_flat(record, metadata, latest_only) -> dict
convert_records(records, metadata, latest_only) -> pd.DataFrame
"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from typing import Any

try:
    import pandas as pd
    _HAS_PANDAS = True
except ImportError:  # pragma: no cover
    _HAS_PANDAS = False
    pd = None  # type: ignore[assignment]

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

MAX_EXECUTIVES = 11
MAX_FINANCIAL_HISTORY = 8
MAX_INFOBEL_CODES = 10
MAX_LOCAL_CODES = 15
MAX_INTERNATIONAL_CODES = 6
MAX_NACE_CODES = 6
MAX_ECOMMERCE_ITEMS = 10


# ---------------------------------------------------------------------------
# Column schema
# ---------------------------------------------------------------------------

def build_expected_columns() -> list[str]:
    """Return the ordered list of all 482 flat column names."""
    columns: list[str] = [
        # Metadata (5)
        "Country ISO code", "BuildDate", "TotalRecords", "UniqueID", "UniversalPublicationId",
        # Company Names (3)
        "CompanyName", "TradeName", "DirectoryName",
        # Address (14)
        "Address1", "Address2", "PostCode", "City", "CityCode", "Locality", "LocalityCode",
        "Province", "ProvinceCode", "Region", "RegionCode", "Country", "CountryCode", "Language",
        # Contact (7)
        "PhoneOrMobile", "Phone", "DNCMPhone", "Fax", "Mobile", "DNCMMobile", "Email",
        # Website (13)
        "Website", "WebsiteUUID", "WebsiteCrawlDate", "WebsiteStatusFlag",
        "WebsiteStatusFlagDescription", "WebDomain", "WebDomainUUID",
        "WebSocialMedialinksFacebook", "WebSocialMedialinksTwitter",
        "GenericLinkedInLink", "GenericLinkedInCompanyID", "GenericLinkedInFollowers",
        "WebsiteIpAddress",
        # National ID (4)
        "NationalID", "NationalIdentificationTypeCode",
        "NationalIdentificationTypeCodeDescription", "NationalIDIsVat",
    ]

    # Infobel Codes (20)
    for i in range(1, MAX_INFOBEL_CODES + 1):
        columns += [f"InfobelCode{i:02d}", f"InfobelLabel{i:02d}"]

    # Local Codes (30)
    for i in range(1, MAX_LOCAL_CODES + 1):
        columns += [f"LocalCode{i:02d}", f"LocalLabel{i:02d}"]

    # International Codes / SIC (12)
    for i in range(1, MAX_INTERNATIONAL_CODES + 1):
        columns += [f"InternationalCode{i:02d}", f"InternationalLabel{i:02d}"]

    # NACE Codes (12)
    for i in range(1, MAX_NACE_CODES + 1):
        columns += [f"InternationalNACECode{i:02d}", f"InternationalNACELabel{i:02d}"]

    columns += [
        # Activity & company info
        "PrimaryLocalActivityCode", "LocalActivityTypeCode", "MarketabilityIndicator",
        "YearStarted", "NumberOfFamilyMembers",
        # CEO
        "CEOName", "CEOTitle", "CEOFirstName", "CEOLastName", "CEOGender", "CEOLanguage",
        # Employees
        "EmployeesHere", "EmployeesHereReliabilityCode", "EmployeesHereReliabilityCodeDescription",
        "EmployeesTotal", "EmployeesTotalReliabilityCode", "EmployeesTotalReliabilityCodeDescription",
        # Import/export & status
        "ImportExportAgentCode", "ImportExportAgentCodeDescription",
        "LegalStatusCode", "LegalStatusCodeDescription", "StatusCode", "StatusCodeDescription",
        # Financials
        "SalesVolumeLocal", "CurrencyCode", "SalesVolumeDollars", "SalesVolumeEuros",
        "SalesVolumeReliabilityCode", "SalesVolumeReliabilityCodeDescription",
        # Publishing & opening hours
        "IsPublished", "PublishingStrength", "GenericOpeningHours",
        # Geo
        "Longitude", "Latitude", "GeoLevel", "GeoLevelDescription",
        # Building
        "BuildingName", "BuildingType", "BuildingGeom", "BuildingArea",
        # Corporate hierarchy
        "SubsidiaryIndicator", "DIASCode", "HierarchyCode",
        # Corporate linkage — Domestic Ultimate
        "DomesticUltimateUniqueID", "DomesticUltimateBusinessName",
        "DomesticUltimateStreetAddress", "DomesticUltimateCityName",
        "DomesticUltimatePostalCode", "DomesticUltimateProvince",
        "DomesticUltimateCountry", "DomesticUltimateCountryCode",
        # Corporate linkage — Global Ultimate
        "GlobalUltimateUniqueID", "GlobalUltimateBusinessName",
        "GlobalUltimateStreetAddress", "GlobalUltimateCityName",
        "GlobalUltimatePostalCode", "GlobalUltimateProvince",
        "GlobalUltimateCountry", "GlobalUltimateCountryCode",
        # Corporate linkage — Parent
        "ParentUniqueID", "ParentBusinessName", "ParentStreetAddress",
        "ParentCityName", "ParentPostalCode", "ParentProvince",
        "ParentCountry", "ParentCountryCode",
    ]

    # Executives (11 × 10 = 110)
    for i in range(1, MAX_EXECUTIVES + 1):
        idx = f"{i:02d}"
        columns += [
            f"Exec{idx}Position", f"Exec{idx}FullName", f"Exec{idx}Title",
            f"Exec{idx}TitleCode", f"Exec{idx}FirstName", f"Exec{idx}LastName",
            f"Exec{idx}Gender", f"Exec{idx}GenderCode",
            f"Exec{idx}LangPref", f"Exec{idx}LangPrefCode",
        ]

    # Financial History (8 × 16 = 128)
    for i in range(1, MAX_FINANCIAL_HISTORY + 1):
        idx = f"{i:02d}"
        columns += [
            f"FinancialHistory{idx}UniqueID", f"FinancialHistory{idx}FamilyMembers",
            f"FinancialHistory{idx}EmployeesHere",
            f"FinancialHistory{idx}EmployeesHereReliabilityCode",
            f"FinancialHistory{idx}EmployeesHereReliabilityCodeDescription",
            f"FinancialHistory{idx}EmployeesTotal",
            f"FinancialHistory{idx}EmployeesTotalReliabilityCode",
            f"FinancialHistory{idx}EmployeesTotalReliabilityCodeDescription",
            f"FinancialHistory{idx}SalesVolume", f"FinancialHistory{idx}Currency",
            f"FinancialHistory{idx}SalesVolumeDollars", f"FinancialHistory{idx}SalesVolumeEuros",
            f"FinancialHistory{idx}SalesVolumeReliabilityCode",
            f"FinancialHistory{idx}SalesVolumeReliabilityCodeDescription",
            f"FinancialHistory{idx}YearStat", f"FinancialHistory{idx}Version",
        ]

    # E-commerce (4 booleans + 10×5 arrays = 54)
    columns += ["HasShopTool", "HasPayment", "HasDigitalMarketing", "HasEShop"]
    for i in range(1, MAX_ECOMMERCE_ITEMS + 1):
        columns.append(f"Shop{i:02d}")
    for i in range(1, MAX_ECOMMERCE_ITEMS + 1):
        columns.append(f"OtherShop{i:02d}")
    for i in range(1, MAX_ECOMMERCE_ITEMS + 1):
        columns.append(f"PaymentProvider{i:02d}")
    for i in range(1, MAX_ECOMMERCE_ITEMS + 1):
        columns.append(f"SimplePaymentRule{i:02d}")
    for i in range(1, MAX_ECOMMERCE_ITEMS + 1):
        columns.append(f"MarketingAutomation{i:02d}")

    return columns


EXPECTED_COLUMNS: list[str] = build_expected_columns()


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def _safe_get(obj: dict | None, key: str, default: Any = "") -> Any:
    if obj is None:
        return default
    value = obj.get(key, default)
    return default if value is None else value


def _to_str(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, bool):
        return str(value).lower()
    return str(value)


def _extract_social_links(social_links: list[dict]) -> dict[str, str]:
    result: dict[str, str] = {
        "GenericLinkedInLink": "",
        "GenericLinkedInCompanyID": "",
        "GenericLinkedInFollowers": "",
        "WebSocialMedialinksFacebook": "",
        "WebSocialMedialinksTwitter": "",
    }
    if not social_links:
        return result
    for link in social_links:
        name = _safe_get(link, "socialMediaName", "").lower()
        if name == "linkedin":
            result["GenericLinkedInLink"] = _safe_get(link, "link")
            result["GenericLinkedInCompanyID"] = _to_str(_safe_get(link, "id"))
            result["GenericLinkedInFollowers"] = _to_str(_safe_get(link, "followers"))
        elif name == "facebook":
            result["WebSocialMedialinksFacebook"] = _safe_get(link, "link")
        elif name == "twitter":
            result["WebSocialMedialinksTwitter"] = _safe_get(link, "link")
    return result


def _serialize_opening_hours(opening_hours: dict | None) -> str:
    if not opening_hours:
        return ""
    try:
        parts = []
        for hours_set in opening_hours.get("OpeningHoursSets", []):
            for day in hours_set.get("DaysList", []):
                weekday = day.get("WeekDay", "")[:3]
                intervals = day.get("Intervals", [])
                if intervals:
                    times = [
                        f"{iv.get('OpenHour', '')}-{iv.get('CloseHour', '')}"
                        for iv in intervals
                        if iv.get("OpenHour") and iv.get("CloseHour")
                    ]
                    if times:
                        parts.append(f"{weekday}: {', '.join(times)}")
        return "; ".join(parts)
    except Exception:
        return json.dumps(opening_hours)


def _extract_category_labels(categories: list[dict], max_count: int) -> dict[str, str]:
    result: dict[str, str] = {}
    for i in range(1, max_count + 1):
        idx = f"{i:02d}"
        result[f"code{idx}"] = ""
        result[f"label{idx}"] = ""
    if not categories:
        return result
    for i, cat in enumerate(categories[:max_count], 1):
        idx = f"{i:02d}"
        result[f"code{idx}"] = _safe_get(cat, "code")
        result[f"label{idx}"] = _safe_get(cat, "name")
    return result


def _flatten_linkage(linkage: dict | None, prefix: str) -> dict[str, str]:
    if not linkage:
        return {
            f"{prefix}UniqueID": "", f"{prefix}BusinessName": "",
            f"{prefix}StreetAddress": "", f"{prefix}CityName": "",
            f"{prefix}PostalCode": "", f"{prefix}Province": "",
            f"{prefix}Country": "", f"{prefix}CountryCode": "",
        }
    return {
        f"{prefix}UniqueID": _safe_get(linkage, "uniqueId"),
        f"{prefix}BusinessName": _safe_get(linkage, "businessName"),
        f"{prefix}StreetAddress": _safe_get(linkage, "streetAddress"),
        f"{prefix}CityName": _safe_get(linkage, "cityName"),
        f"{prefix}PostalCode": _safe_get(linkage, "postalCode"),
        f"{prefix}Province": _safe_get(linkage, "province"),
        f"{prefix}Country": _safe_get(linkage, "country"),
        f"{prefix}CountryCode": _safe_get(linkage, "countryCode"),
    }


def _flatten_executives(executives: list[dict]) -> dict[str, str]:
    result: dict[str, str] = {}
    for i in range(1, MAX_EXECUTIVES + 1):
        idx = f"{i:02d}"
        for key in ("Position", "FullName", "Title", "TitleCode", "FirstName",
                    "LastName", "Gender", "GenderCode", "LangPref", "LangPrefCode"):
            result[f"Exec{idx}{key}"] = ""
    if not executives:
        return result
    for i, exec_data in enumerate(executives[:MAX_EXECUTIVES], 1):
        idx = f"{i:02d}"
        result[f"Exec{idx}Position"] = _safe_get(exec_data, "position")
        result[f"Exec{idx}FullName"] = _safe_get(exec_data, "fullName")
        result[f"Exec{idx}Title"] = _safe_get(exec_data, "title")
        result[f"Exec{idx}TitleCode"] = _to_str(_safe_get(exec_data, "titleCode"))
        result[f"Exec{idx}FirstName"] = _safe_get(exec_data, "firstName")
        result[f"Exec{idx}LastName"] = _safe_get(exec_data, "lastName")
        result[f"Exec{idx}Gender"] = _safe_get(exec_data, "gender")
        result[f"Exec{idx}GenderCode"] = _to_str(_safe_get(exec_data, "genderCode"))
        result[f"Exec{idx}LangPref"] = _safe_get(exec_data, "langPref")
        result[f"Exec{idx}LangPrefCode"] = _to_str(_safe_get(exec_data, "langPrefCode"))
    return result


def _pick_latest_financial_entry(history: list[dict]) -> dict | None:
    if not history:
        return None
    best = None
    best_year = -1
    best_version = ""
    for item in history:
        try:
            y = int(str(_safe_get(item, "yearStat", "")).strip())
        except (ValueError, TypeError):
            y = -1
        v = str(_safe_get(item, "version", "") or "")
        if y > best_year or (y == best_year and v > best_version):
            best = item
            best_year = y
            best_version = v
    return best or history[0]


def _flatten_financial_history(history: list[dict], latest_only: bool = False) -> dict[str, str]:
    result: dict[str, str] = {}
    _KEYS = (
        ("UniqueID", "uniqueID", False),
        ("FamilyMembers", "familyMembers", True),
        ("EmployeesHere", "employeesHere", False),
        ("EmployeesHereReliabilityCode", "employeesHereReliabilityCode", True),
        ("EmployeesHereReliabilityCodeDescription", "employeesHereReliabilityCodeDescription", False),
        ("EmployeesTotal", "employeesTotal", False),
        ("EmployeesTotalReliabilityCode", "employeesTotalReliabilityCode", True),
        ("EmployeesTotalReliabilityCodeDescription", "employeesTotalReliabilityCodeDescription", False),
        ("SalesVolume", "salesVolume", False),
        ("Currency", "currency", False),
        ("SalesVolumeDollars", "salesVolumeDollars", False),
        ("SalesVolumeEuros", "salesVolumeEuros", False),
        ("SalesVolumeReliabilityCode", "salesVolumeReliabilityCode", True),
        ("SalesVolumeReliabilityCodeDescription", "salesVolumeReliabilityCodeDescription", False),
        ("YearStat", "yearStat", False),
        ("Version", "version", False),
    )
    for i in range(1, MAX_FINANCIAL_HISTORY + 1):
        idx = f"{i:02d}"
        for col_suffix, _, _ in _KEYS:
            result[f"FinancialHistory{idx}{col_suffix}"] = ""

    if not history:
        return result

    entries = [_pick_latest_financial_entry(history)] if latest_only else history[:MAX_FINANCIAL_HISTORY]
    for i, fin in enumerate(entries, 1):
        if fin is None:
            continue
        idx = f"{i:02d}"
        for col_suffix, api_key, stringify in _KEYS:
            val = _safe_get(fin, api_key)
            result[f"FinancialHistory{idx}{col_suffix}"] = _to_str(val) if stringify else val
    return result


def _extract_ecommerce(record: dict) -> dict[str, str]:
    result: dict[str, str] = {
        "HasShopTool": "", "HasPayment": "", "HasDigitalMarketing": "", "HasEShop": "",
    }
    for i in range(1, MAX_ECOMMERCE_ITEMS + 1):
        idx = f"{i:02d}"
        result[f"Shop{idx}"] = ""
        result[f"OtherShop{idx}"] = ""
        result[f"PaymentProvider{idx}"] = ""
        result[f"SimplePaymentRule{idx}"] = ""
        result[f"MarketingAutomation{idx}"] = ""

    additional = record.get("additionalInfos") or {}
    result["HasShopTool"] = _to_str(_safe_get(record, "hasShopTool", _safe_get(additional, "hasShopTool")))
    result["HasPayment"] = _to_str(_safe_get(record, "hasPayment", _safe_get(additional, "hasPayment")))
    result["HasDigitalMarketing"] = _to_str(_safe_get(record, "hasDigitalMarketing", _safe_get(additional, "hasDigitalMarketing")))
    result["HasEShop"] = _to_str(_safe_get(record, "hasEShop", _safe_get(additional, "hasEShop")))

    for arr_key, col_prefix in (
        ("shops", "Shop"), ("otherShops", "OtherShop"), ("paymentProviders", "PaymentProvider"),
        ("simplePaymentRules", "SimplePaymentRule"), ("marketingAutomation", "MarketingAutomation"),
    ):
        items = (record.get(arr_key) or additional.get(arr_key) or [])[:MAX_ECOMMERCE_ITEMS]
        for i, item in enumerate(items, 1):
            result[f"{col_prefix}{i:02d}"] = _to_str(item)

    return result


# ---------------------------------------------------------------------------
# Public conversion functions
# ---------------------------------------------------------------------------

def convert_record_to_flat(
    record: dict,
    metadata: dict | None = None,
    *,
    latest_only: bool = False,
) -> dict[str, str]:
    """Convert a single API record dict to a flat dict with all 482 columns."""
    if metadata is None:
        metadata = {}

    result: dict[str, Any] = {col: "" for col in EXPECTED_COLUMNS}

    # Metadata
    result["Country ISO code"] = _safe_get(record, "countryCode")
    result["BuildDate"] = metadata.get("BuildDate", datetime.now().strftime("%Y-%m-%d"))
    result["TotalRecords"] = _to_str(metadata.get("TotalRecords", ""))
    result["UniqueID"] = _safe_get(record, "uniqueID")
    result["UniversalPublicationId"] = _safe_get(record, "universalPublicationId")

    # Company names
    result["CompanyName"] = _safe_get(record, "companyName")
    result["TradeName"] = _safe_get(record, "tradeName")
    result["DirectoryName"] = _safe_get(record, "directoryName")

    # Address
    result["Address1"] = _safe_get(record, "address1")
    result["Address2"] = _safe_get(record, "address2")
    result["PostCode"] = _safe_get(record, "postCode")
    result["City"] = _safe_get(record, "city")
    result["CityCode"] = _safe_get(record, "cityCode")
    result["Locality"] = _safe_get(record, "locality")
    result["LocalityCode"] = _safe_get(record, "localityCode")
    result["Province"] = _safe_get(record, "province")
    result["ProvinceCode"] = _safe_get(record, "provinceCode")
    result["Region"] = _safe_get(record, "region")
    result["RegionCode"] = _safe_get(record, "regionCode")
    result["Country"] = _safe_get(record, "country")
    result["CountryCode"] = _safe_get(record, "countryCode")
    result["Language"] = _safe_get(record, "language")

    # Contact
    result["PhoneOrMobile"] = _safe_get(record, "phoneOrMobile")
    result["Phone"] = _safe_get(record, "phone")
    result["DNCMPhone"] = _to_str(_safe_get(record, "dncmPhone"))
    result["Fax"] = _safe_get(record, "fax")
    result["Mobile"] = _safe_get(record, "mobile")
    result["DNCMMobile"] = _to_str(_safe_get(record, "dncmMobile"))
    result["Email"] = _safe_get(record, "email")

    # Website
    result["Website"] = _safe_get(record, "website")
    result["WebsiteUUID"] = _safe_get(record, "websiteUUID")
    result["WebsiteCrawlDate"] = _safe_get(record, "websiteCrawlDate")
    result["WebsiteStatusFlag"] = _to_str(_safe_get(record, "websiteStatusFlag"))
    result["WebsiteStatusFlagDescription"] = _safe_get(record, "websiteStatusFlagDescription")
    result["WebDomain"] = _safe_get(record, "webDomain")
    result["WebDomainUUID"] = _safe_get(record, "webDomainUUID")
    result["WebsiteIpAddress"] = _safe_get(record, "websiteIpAddress")
    result.update(_extract_social_links(record.get("genericSocialLinks") or []))

    # National ID
    result["NationalID"] = _safe_get(record, "nationalID")
    result["NationalIdentificationTypeCode"] = _to_str(_safe_get(record, "nationalIdentificationTypeCode"))
    result["NationalIdentificationTypeCodeDescription"] = _safe_get(record, "nationalIdentificationTypeCodeDescription")
    result["NationalIDIsVat"] = _to_str(_safe_get(record, "nationalIDIsVat"))

    # Category codes
    infobel_cats = _extract_category_labels(record.get("infobelCategories") or [], MAX_INFOBEL_CODES)
    for i in range(1, MAX_INFOBEL_CODES + 1):
        idx = f"{i:02d}"
        code = _safe_get(record, f"infobelCode{idx}")
        result[f"InfobelCode{idx}"] = code or infobel_cats.get(f"code{idx}", "")
        label = _safe_get(record, f"infobelLabel{idx}")
        result[f"InfobelLabel{idx}"] = label or infobel_cats.get(f"label{idx}", "")

    local_cats = _extract_category_labels(record.get("localCategories") or [], MAX_LOCAL_CODES)
    for i in range(1, MAX_LOCAL_CODES + 1):
        idx = f"{i:02d}"
        code = _safe_get(record, f"localCode{idx}")
        result[f"LocalCode{idx}"] = code or local_cats.get(f"code{idx}", "")
        label = _safe_get(record, f"localLabel{idx}")
        result[f"LocalLabel{idx}"] = label or local_cats.get(f"label{idx}", "")

    intl_cats = _extract_category_labels(record.get("internationalCategories") or [], MAX_INTERNATIONAL_CODES)
    for i in range(1, MAX_INTERNATIONAL_CODES + 1):
        idx = f"{i:02d}"
        code = _safe_get(record, f"internationalCode{idx}")
        result[f"InternationalCode{idx}"] = code or intl_cats.get(f"code{idx}", "")
        label = _safe_get(record, f"internationalLabel{idx}")
        result[f"InternationalLabel{idx}"] = label or intl_cats.get(f"label{idx}", "")

    nace_cats = _extract_category_labels(record.get("altInternationalCategories") or [], MAX_NACE_CODES)
    for i in range(1, MAX_NACE_CODES + 1):
        idx = f"{i:02d}"
        code = _safe_get(record, f"altInternationalCode{idx}")
        result[f"InternationalNACECode{idx}"] = code or nace_cats.get(f"code{idx}", "")
        label = _safe_get(record, f"altInternationalLabel{idx}")
        result[f"InternationalNACELabel{idx}"] = label or nace_cats.get(f"label{idx}", "")

    # Activity
    result["PrimaryLocalActivityCode"] = _safe_get(record, "primaryLocalActivityCode")
    result["LocalActivityTypeCode"] = _safe_get(record, "localActivityTypeCode")
    result["MarketabilityIndicator"] = _safe_get(record, "hasMarketability")

    # Company info
    result["YearStarted"] = _safe_get(record, "yearStarted")
    result["NumberOfFamilyMembers"] = _to_str(_safe_get(record, "familyMembers"))

    # CEO
    result["CEOName"] = _safe_get(record, "ceoName")
    result["CEOTitle"] = _safe_get(record, "ceoTitle")
    result["CEOFirstName"] = _safe_get(record, "ceoFirstName")
    result["CEOLastName"] = _safe_get(record, "ceoLastName")
    result["CEOGender"] = _safe_get(record, "ceoGender")
    result["CEOLanguage"] = _safe_get(record, "ceoLanguage") or _safe_get(record, "ceoLangPref")

    # Employees
    result["EmployeesHere"] = _safe_get(record, "employeesHere")
    result["EmployeesHereReliabilityCode"] = _to_str(_safe_get(record, "employeesHereReliabilityCode"))
    result["EmployeesHereReliabilityCodeDescription"] = _safe_get(record, "employeesHereReliabilityCodeDescription")
    result["EmployeesTotal"] = _safe_get(record, "employeesTotal")
    result["EmployeesTotalReliabilityCode"] = _to_str(_safe_get(record, "employeesTotalReliabilityCode"))
    result["EmployeesTotalReliabilityCodeDescription"] = _safe_get(record, "employeesTotalReliabilityCodeDescription")

    # Import/export & legal
    result["ImportExportAgentCode"] = _safe_get(record, "importExportAgentCode")
    result["ImportExportAgentCodeDescription"] = _safe_get(record, "importExportAgentCodeDescription")
    result["LegalStatusCode"] = _to_str(_safe_get(record, "legalStatusCode"))
    result["LegalStatusCodeDescription"] = _safe_get(record, "legalStatusCodeDescription")
    result["StatusCode"] = _safe_get(record, "statusCode")
    result["StatusCodeDescription"] = _safe_get(record, "statusCodeName")

    # Sales
    result["SalesVolumeLocal"] = _safe_get(record, "salesVolume")
    result["CurrencyCode"] = _safe_get(record, "currency")
    result["SalesVolumeDollars"] = _safe_get(record, "salesVolumeDollars")
    result["SalesVolumeEuros"] = _safe_get(record, "salesVolumeEuros")
    result["SalesVolumeReliabilityCode"] = _to_str(_safe_get(record, "salesVolumeReliabilityCode"))
    result["SalesVolumeReliabilityCodeDescription"] = _safe_get(record, "salesVolumeReliabilityCodeDescription")

    # Publishing
    result["IsPublished"] = _to_str(_safe_get(record, "isPublished"))
    result["PublishingStrength"] = _to_str(_safe_get(record, "publishingStrength"))

    # Opening hours (nested inside additionalInfos)
    additional_infos = record.get("additionalInfos") or {}
    result["GenericOpeningHours"] = _serialize_opening_hours(
        additional_infos.get("genericOpeningHours") or {}
    )

    # Geolocation
    result["Longitude"] = _safe_get(record, "longitude")
    result["Latitude"] = _safe_get(record, "latitude")
    result["GeoLevel"] = _to_str(_safe_get(record, "geoLevel"))
    result["GeoLevelDescription"] = _safe_get(record, "geoLevelDescription")

    # Building
    result["BuildingName"] = _safe_get(record, "buildingName")
    result["BuildingType"] = _safe_get(record, "buildingType")
    result["BuildingGeom"] = _safe_get(record, "buildingGeom")
    result["BuildingArea"] = _to_str(_safe_get(record, "buildingArea"))

    # Corporate hierarchy
    result["SubsidiaryIndicator"] = _safe_get(record, "subsidiaryIndicator")
    result["DIASCode"] = _safe_get(record, "diasCode")
    result["HierarchyCode"] = _safe_get(record, "hierarchyCode")

    # Corporate linkage
    result.update(_flatten_linkage(record.get("domesticLinkage"), "DomesticUltimate"))
    result.update(_flatten_linkage(record.get("globalLinkage"), "GlobalUltimate"))
    result.update(_flatten_linkage(record.get("parentLinkage"), "Parent"))

    # Executives
    result.update(_flatten_executives(record.get("executives") or []))

    # Financial history
    result.update(_flatten_financial_history(record.get("financialHistory") or [], latest_only=latest_only))

    # E-commerce
    result.update(_extract_ecommerce(record))

    return result


def convert_records(
    records: list[dict],
    metadata: dict | None = None,
    *,
    latest_only: bool = False,
) -> "pd.DataFrame":
    """Convert a list of API records to a DataFrame with all 482 columns.

    Args:
        records: List of company records from the API response.
        metadata: Optional dict with ``BuildDate`` and ``TotalRecords`` keys.
        latest_only: When True, only the most recent financial history entry
            is mapped (to FinancialHistory01*). Defaults to False.

    Returns:
        ``pandas.DataFrame`` with columns in ``EXPECTED_COLUMNS`` order.

    Raises:
        ImportError: If ``pandas`` is not installed.
    """
    if not _HAS_PANDAS:
        raise ImportError("pandas is required for convert_records(). Install with: pip install pandas")

    if metadata is None:
        metadata = {"BuildDate": datetime.now().strftime("%Y-%m-%d")}

    flat_records = [convert_record_to_flat(r, metadata, latest_only=latest_only) for r in records]

    df = pd.DataFrame(flat_records)
    for col in EXPECTED_COLUMNS:
        if col not in df.columns:
            df[col] = ""
    return df[EXPECTED_COLUMNS]
