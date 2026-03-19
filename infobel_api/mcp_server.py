"""MCP server exposing the Infobel API as tools for AI agents."""

from __future__ import annotations

import json
import logging
from typing import Any

from mcp.server.fastmcp import FastMCP

from .client import InfobelClient

logger = logging.getLogger(__name__)

mcp = FastMCP(
    name="infobel",
    instructions=(
        "Infobel business search API — search 375M+ companies worldwide. "
        "CRITICAL: search_businesses and get_search_results require record_fields "
        "(list of field names). Pass [] to get counts only. uniqueID is always "
        "returned. Use get_search_results with the returned search_id for more pages. "
        "Only request the fields you need — this preserves your context window."
    ),
)

_client: InfobelClient | None = None


def _get_client() -> InfobelClient:
    global _client
    if _client is None:
        _client = InfobelClient()
    return _client


def _json(data: Any) -> str:
    """Format response for AI consumption."""
    return json.dumps(data, indent=2, default=str)


def _ensure_unique_id(fields: list[str]) -> list[str]:
    """Guarantee uniqueID is always the first field returned."""
    if "uniqueID" not in fields:
        return ["uniqueID"] + list(fields)
    return list(fields)


# ---------------------------------------------------------------------------
# Search
# ---------------------------------------------------------------------------

@mcp.tool()
def search_businesses(
    country_codes: list[str],
    record_fields: list[str],
    business_name: list[str] | None = None,
    national_id: list[str] | None = None,
    unique_ids: list[str] | None = None,
    city_names: list[str] | None = None,
    city_codes: list[str] | None = None,
    province_names: list[str] | None = None,
    province_codes: list[str] | None = None,
    region_names: list[str] | None = None,
    region_codes: list[str] | None = None,
    post_codes: list[str] | None = None,
    street_address: str | None = None,
    house_number: str | None = None,
    phone_number: list[str] | None = None,
    email: list[str] | None = None,
    website: list[str] | None = None,
    international_codes: list[str] | None = None,
    infobel_codes: list[str] | None = None,
    local_codes: list[str] | None = None,
    alt_international_codes: list[str] | None = None,
    categories_keywords: list[str] | None = None,
    has_phone: bool | None = None,
    has_email: bool | None = None,
    has_website: str | None = None,
    has_national_id: str | None = None,
    has_coordinates: bool | None = None,
    has_linked_in: bool | None = None,
    year_started_from: str | None = None,
    year_started_to: str | None = None,
    employees_total_from: int | None = None,
    employees_total_to: int | None = None,
    sales_volume_from: int | None = None,
    sales_volume_to: int | None = None,
    sales_volume_currency: str | None = None,
    status_codes: list[str] | None = None,
    legal_status_codes: list[str] | None = None,
    ceo_name: str | None = None,
    parent_unique_id: list[str] | None = None,
    global_ultimate_unique_id: list[str] | None = None,
    domestic_ultimate_unique_id: list[str] | None = None,
    display_language: str | None = None,
    page_size: int | None = None,
    sorting_order: list[dict] | None = None,
    coordinate_latitude: float | None = None,
    coordinate_longitude: float | None = None,
    coordinate_distance: int | None = None,
    technographical_tags: list[str] | None = None,
    executive_tags: list[str] | None = None,
    social_links: list[str] | None = None,
    website_status_flags: list[int] | None = None,
    import_export_agent_codes: list[str] | None = None,
    is_published: bool | None = None,
    is_vat: bool | None = None,
    has_admin: bool | None = None,
    has_marketability: bool | None = None,
    has_building_geometry: bool | None = None,
    has_logo: bool | None = None,
    has_shop_tool: bool | None = None,
    has_payment: bool | None = None,
    has_digital_marketing: bool | None = None,
    has_e_shop: bool | None = None,
    linked_in_followers_from: str | None = None,
    linked_in_followers_to: str | None = None,
    data_type: str | None = None,
) -> str:
    """Search the Infobel worldwide business database.

    IMPORTANT — record_fields is required. You MUST decide upfront which fields
    you need. Pass [] (empty list) for counts-only queries. uniqueID is always
    included automatically so callers can fetch full records.

    Use-case examples for record_fields:
      Counts only (no records):
        record_fields=[]
        → Returns searchId + counts only (fastest, cheapest)

      Name matching / deduplication:
        record_fields=["businessName", "tradeName", "companyName", "directoryName"]

      Address verification:
        record_fields=["businessName", "address1", "address2", "postCode", "city",
                       "province", "countryCode"]

      Contact lookup:
        record_fields=["businessName", "phone", "email", "website"]

      Full identity + location:
        record_fields=["businessName", "tradeName", "nationalID", "address1",
                       "postCode", "city", "countryCode"]

    Available field names (camelCase, as returned by the API):
      Identity:  uniqueID, businessName, companyName, tradeName, directoryName,
                 diasCode, nationalID, universalPublicationId
      Address:   address1, address2, addressStreet, addressHouseNumber,
                 postCode, city, cityCode, locality, localityCode,
                 province, provinceCode, region, regionCode, country, countryCode
      Contact:   phone, mobile, fax, email, website, webDomain, phoneOrMobile
      Corporate: yearStarted, employeesTotal, employeesHere, salesVolume,
                 salesVolumeDollars, salesVolumeEuros, statusCode, statusCodeName,
                 hierarchyCode, subsidiaryIndicator, importExportAgentCode,
                 legalStatus
      Executive: ceoName, ceoTitle
      Geo:       latitude, longitude, geoLevel, geoLevelDescription
      Digital:   hasEShop, hasPayment, hasDigitalMarketing, hasShopTool,
                 hasBuildingGeometry, hasMarketability, dncmPhone,
                 websiteStatusFlag, websiteUUID, websiteIpAddress, websiteCrawlDate,
                 webDomainUUID
      Linkage:   parentLinkage, domesticLinkage, globalLinkage, familyMembers
      Categories: internationalCode01-06, infobelCode01-10, localCode01-15,
                  altInternationalCode01-06, internationalCategories,
                  altInternationalCategories
      Financial: financialHistory, salesVolumeReliabilityCode,
                 employeesTotalReliabilityCode, employeesHereReliabilityCode
      Misc:      language, reportDate, additionalInfos, genericSocialLinks

    Returns JSON with:
      searchId  — use with get_search_results for subsequent pages
      counts    — total, hasPhone, hasEmail, etc.
      records   — list of field-filtered records (empty when record_fields=[])
      page      — current page number (omitted when record_fields=[])

    Args:
        country_codes: ISO 3166-1 alpha-2 country codes (e.g. ["GB", "DE"]).
        record_fields: Fields to return per record. Empty list = counts only.
                       uniqueID is always included automatically.
        business_name: Business names to search for (e.g. ["Acme Corp"]).
        national_id: National registration numbers (e.g. company house numbers).
        unique_ids: Infobel unique IDs to look up directly.
        city_names: Filter by city names (e.g. ["London", "Manchester"]).
        city_codes: Filter by city codes.
        province_names: Filter by province/state names.
        province_codes: Filter by province codes.
        region_names: Filter by region names.
        region_codes: Filter by region codes.
        post_codes: Filter by postal/zip codes.
        street_address: Street address filter.
        house_number: House number filter.
        phone_number: Phone numbers to search.
        email: Email addresses to search.
        website: Website URLs to search.
        international_codes: ISIC international category codes.
        infobel_codes: Infobel proprietary category codes.
        local_codes: Local/national category codes (e.g. SIC, NAF).
        alt_international_codes: NACE category codes.
        categories_keywords: Free-text category keywords.
        has_phone: Filter for businesses with phone numbers.
        has_email: Filter for businesses with email addresses.
        has_website: Filter for businesses with websites ("true"/"false").
        has_national_id: Filter for businesses with national ID ("true"/"false").
        has_coordinates: Filter for businesses with GPS coordinates.
        has_linked_in: Filter for businesses with LinkedIn profiles.
        year_started_from: Minimum year started (e.g. "2000").
        year_started_to: Maximum year started (e.g. "2020").
        employees_total_from: Minimum employee count.
        employees_total_to: Maximum employee count.
        sales_volume_from: Minimum sales volume.
        sales_volume_to: Maximum sales volume.
        sales_volume_currency: Currency for sales volume filter (e.g. "EUR", "USD").
        status_codes: Business status codes (e.g. ["Active"]).
        legal_status_codes: Legal form codes.
        ceo_name: CEO/executive name search.
        parent_unique_id: Filter by parent company unique ID.
        global_ultimate_unique_id: Filter by global ultimate owner unique ID.
        domestic_ultimate_unique_id: Filter by domestic ultimate owner unique ID.
        display_language: Language for result display (e.g. "en", "fr").
        page_size: Results per page (default 20, max varies by plan).
        sorting_order: Sorting options.
        coordinate_latitude: Latitude for geo-search.
        coordinate_longitude: Longitude for geo-search.
        coordinate_distance: Radius in meters for geo-search (default 100).
        technographical_tags: Filter by web technologies used.
        executive_tags: Filter by executive characteristics.
        social_links: Filter by social media presence.
        website_status_flags: Filter by website status.
        import_export_agent_codes: Filter by import/export activity.
        is_published: Filter by published status.
        is_vat: Filter by VAT registration.
        has_admin: Filter for businesses with admin data.
        has_marketability: Filter for marketable records.
        has_building_geometry: Filter for records with building geometry.
        has_logo: Filter for businesses with logos.
        has_shop_tool: Filter for businesses with shop tools.
        has_payment: Filter for businesses with payment capabilities.
        has_digital_marketing: Filter for businesses with digital marketing.
        has_e_shop: Filter for businesses with e-shops.
        linked_in_followers_from: Minimum LinkedIn followers.
        linked_in_followers_to: Maximum LinkedIn followers.
        data_type: Data type to search (default "Business").
    """
    kwargs: dict[str, Any] = {"country_codes": country_codes, "return_first_page": False}

    # Map all non-None params into SearchInput kwargs
    _locals = {
        "business_name": business_name,
        "national_id": national_id,
        "unique_ids": unique_ids,
        "city_names": city_names,
        "city_codes": city_codes,
        "province_names": province_names,
        "province_codes": province_codes,
        "region_names": region_names,
        "region_codes": region_codes,
        "post_codes": post_codes,
        "street_address": street_address,
        "house_number": house_number,
        "phone_number": phone_number,
        "email": email,
        "website": website,
        "international_codes": international_codes,
        "infobel_codes": infobel_codes,
        "local_codes": local_codes,
        "alt_international_codes": alt_international_codes,
        "categories_keywords": categories_keywords,
        "has_phone": has_phone,
        "has_email": has_email,
        "has_website": has_website,
        "has_national_id": has_national_id,
        "has_coordinates": has_coordinates,
        "has_linked_in": has_linked_in,
        "year_started_from": year_started_from,
        "year_started_to": year_started_to,
        "employees_total_from": employees_total_from,
        "employees_total_to": employees_total_to,
        "sales_volume_from": sales_volume_from,
        "sales_volume_to": sales_volume_to,
        "sales_volume_currency": sales_volume_currency,
        "status_codes": status_codes,
        "legal_status_codes": legal_status_codes,
        "ceo_name": ceo_name,
        "parent_unique_id": parent_unique_id,
        "global_ultimate_unique_id": global_ultimate_unique_id,
        "domestic_ultimate_unique_id": domestic_ultimate_unique_id,
        "display_language": display_language,
        "page_size": page_size,
        "sorting_order": sorting_order,
        "technographical_tags": technographical_tags,
        "executive_tags": executive_tags,
        "social_links": social_links,
        "website_status_flags": website_status_flags,
        "import_export_agent_codes": import_export_agent_codes,
        "is_published": is_published,
        "is_vat": is_vat,
        "has_admin": has_admin,
        "has_marketability": has_marketability,
        "has_building_geometry": has_building_geometry,
        "has_logo": has_logo,
        "has_shop_tool": has_shop_tool,
        "has_payment": has_payment,
        "has_digital_marketing": has_digital_marketing,
        "has_e_shop": has_e_shop,
        "linked_in_followers_from": linked_in_followers_from,
        "linked_in_followers_to": linked_in_followers_to,
        "data_type": data_type,
    }

    for k, v in _locals.items():
        if v is not None:
            kwargs[k] = v

    # Handle coordinate option
    if coordinate_latitude is not None and coordinate_longitude is not None:
        coord = {"Latitude": coordinate_latitude, "Longitude": coordinate_longitude}
        if coordinate_distance is not None:
            coord["Distance"] = coordinate_distance
        from .models.common import CoordinateOption
        kwargs["coordinate_options"] = [CoordinateOption(**coord)]

    result = _get_client().search.search(**kwargs)
    search_id = result["searchId"]

    output: dict[str, Any] = {
        "searchId": search_id,
        "counts": result.get("counts", {}),
    }

    if record_fields:
        fields = _ensure_unique_id(record_fields)
        records_resp = _get_client().search.post_records(search_id, 1, fields)
        output["page"] = 1
        output["records"] = records_resp.get("records", [])
    else:
        output["records"] = []

    return _json(output)


@mcp.tool()
def get_search_results(search_id: int, page: int, record_fields: list[str]) -> str:
    """Get paginated results from a previous search.

    IMPORTANT — record_fields is required. Pass the same field list you used in
    search_businesses to get consistent, context-efficient results. uniqueID is
    always included automatically.

    Args:
        search_id: Search ID returned by search_businesses.
        page: Page number (1-indexed). Pages must be fetched sequentially.
        record_fields: Fields to return per record. Must be non-empty.
                       uniqueID is always included automatically.
    """
    fields = _ensure_unique_id(record_fields)
    return _json(_get_client().search.post_records(search_id, page, fields))


@mcp.tool()
def get_search_status(search_id: int) -> str:
    """Check the status of a previous search.

    Args:
        search_id: Search ID returned by search_businesses.
    """
    return _json(_get_client().search.get_status(search_id))


# ---------------------------------------------------------------------------
# Record
# ---------------------------------------------------------------------------

@mcp.tool()
def get_record(country_code: str, unique_id: str) -> str:
    """Get the full record for a business by country code and unique ID.

    Args:
        country_code: ISO 3166-1 alpha-2 country code (e.g. "GB").
        unique_id: Infobel unique ID for the business.
    """
    return _json(_get_client().record.get(country_code, unique_id))


@mcp.tool()
def get_record_partial(country_code: str, unique_id: str) -> str:
    """Get a partial (lighter) record for a business.

    Args:
        country_code: ISO 3166-1 alpha-2 country code (e.g. "GB").
        unique_id: Infobel unique ID for the business.
    """
    return _json(_get_client().record.get_partial(country_code, unique_id))


# ---------------------------------------------------------------------------
# Categories (search — never dump full trees)
# ---------------------------------------------------------------------------

@mcp.tool()
def search_categories_infobel(keywords: list[str], language_code: str = "en") -> str:
    """Search Infobel's proprietary category hierarchy by one or more keywords.

    Each keyword triggers a separate API call; results are merged and deduplicated.
    Use multiple keywords to widen coverage — e.g. ["plumbing", "plumber", "pipes"].
    Returns matching categories with their codes for use in search_businesses
    `infobel_codes` field.

    Args:
        keywords: One or more search terms (e.g. ["restaurant"], ["computer", "software", "IT"]).
        language_code: Display language for results (e.g. "en", "fr", "de").
    """
    return _json(_get_client().categories.search_infobel(keywords, language_code))


@mcp.tool()
def search_categories_international(keywords: list[str], language_code: str = "en") -> str:
    """Search ISIC international category codes (UN standard) by one or more keywords.

    Each keyword triggers a separate API call; results are merged and deduplicated.
    Returns matching codes for use in search_businesses `international_codes` field.
    Use for cross-country industry searches using UN classification.

    Args:
        keywords: One or more search terms (e.g. ["manufacturing"], ["retail", "wholesale", "trade"]).
        language_code: Display language for results (e.g. "en", "fr").
    """
    return _json(_get_client().categories.search_international(keywords, language_code))


@mcp.tool()
def search_categories_local(keywords: list[str], country_code: str, language_code: str = "en") -> str:
    """Search country-specific category codes by one or more keywords.

    Each keyword triggers a separate API call; results are merged and deduplicated.
    Returns matching local codes (e.g. SIC for US, NAF for France, WZ for Germany)
    for use in search_businesses `local_codes` field.

    Args:
        keywords: One or more search terms (e.g. ["plomberie"], ["bakery", "boulangerie", "pastry"]).
        country_code: ISO 3166-1 alpha-2 country code (e.g. "FR", "DE", "US").
        language_code: Display language for results (e.g. "en", "fr").
    """
    return _json(_get_client().categories.search_local(keywords, country_code, language_code))


@mcp.tool()
def search_categories_alt_international(keywords: list[str], language_code: str = "en") -> str:
    """Search NACE codes (European standard, AltInternational) by one or more keywords.

    Each keyword triggers a separate API call; results are merged and deduplicated.
    Returns matching NACE codes for use in search_businesses `alt_international_codes`
    field. Use this for EU industry classification queries.

    Args:
        keywords: One or more search terms (e.g. ["computer programming"], ["software", "IT", "development"]).
        language_code: Display language for results (e.g. "en", "fr", "de").
    """
    return _json(_get_client().categories.search_alt_international(keywords, language_code))


# ---------------------------------------------------------------------------
# Locations (search — never dump full lists)
# ---------------------------------------------------------------------------

@mcp.tool()
def search_locations(keywords: list[str], country_code: str, language_code: str = "en") -> str:
    """Search cities, regions, and provinces within a country by one or more keywords.

    Each keyword triggers a separate API call; results are merged and deduplicated.
    Returns matching location codes for use in search_businesses filters
    (city_codes, region_codes, province_codes). Always use this instead of
    fetching full location lists.

    Args:
        keywords: One or more search terms (e.g. ["Munich"], ["Bavaria", "Bayern", "Munich"]).
        country_code: ISO 3166-1 alpha-2 country code (e.g. "DE", "GB").
        language_code: Display language for results (e.g. "en", "de", "fr").
    """
    return _json(_get_client().locations.search_keywords(keywords, country_code, language_code=language_code))


# ---------------------------------------------------------------------------
# Reference data
# ---------------------------------------------------------------------------

@mcp.tool()
def get_available_countries() -> str:
    """List all countries available in the Infobel database."""
    return _json(_get_client().countries.get_all())


@mcp.tool()
def get_languages() -> str:
    """List available display languages for API results."""
    return _json(_get_client().utils.get_languages())


@mcp.tool()
def get_reliability_codes() -> str:
    """List reliability codes and their meanings."""
    return _json(_get_client().utils.get_reliability_codes())


@mcp.tool()
def test_connection() -> str:
    """Verify API connectivity and authentication."""
    return _json(_get_client().test.hello())


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
