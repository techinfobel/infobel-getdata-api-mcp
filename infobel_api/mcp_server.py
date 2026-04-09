"""MCP server exposing the Infobel API as tools for AI agents."""

from __future__ import annotations

import json
import logging
from contextlib import asynccontextmanager
from typing import Any

from mcp.server.fastmcp import FastMCP

from .client import InfobelClient
from .exceptions import InfobelAPIError

logger = logging.getLogger(__name__)

_client: InfobelClient | None = None


@asynccontextmanager
async def _lifespan(server: FastMCP):  # noqa: ARG001
    """Manage InfobelClient lifecycle — create on startup, close on shutdown."""
    global _client
    _client = InfobelClient()
    try:
        yield
    finally:
        if _client is not None:
            _client.close()
            _client = None


mcp = FastMCP(
    name="infobel",
    instructions=(
        "Infobel business search API — search 375M+ companies worldwide. "
        "CRITICAL: search_businesses and get_search_results require record_fields "
        "(list of field names). Pass [] to get counts only. uniqueID is always "
        "returned. Use get_search_results with the returned search_id for more pages. "
        "Only request the fields you need — this preserves your context window."
    ),
    lifespan=_lifespan,
)


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
def search_businesses(  # noqa: PLR0913
    country_codes: list[str],
    record_fields: list[str],
    # Identity
    business_name: list[str] | None = None,
    business_name_exclusive: list[str] | None = None,
    national_id: list[str] | None = None,
    national_id_exclusive: list[str] | None = None,
    unique_ids: list[str] | None = None,
    unique_ids_exclusive: list[str] | None = None,
    # Location - cities
    city_names: list[str] | None = None,
    city_codes: list[str] | None = None,
    city_codes_exclusive: list[str] | None = None,
    # Location - provinces
    province_names: list[str] | None = None,
    province_codes: list[str] | None = None,
    province_codes_exclusive: list[str] | None = None,
    # Location - regions
    region_names: list[str] | None = None,
    region_codes: list[str] | None = None,
    region_codes_exclusive: list[str] | None = None,
    # Location - postal
    post_codes: list[str] | None = None,
    post_codes_exclusive: list[str] | None = None,
    # Location - address
    street_address: str | None = None,
    house_number: str | None = None,
    # Location - coordinates (inclusive)
    coordinate_latitude: float | None = None,
    coordinate_longitude: float | None = None,
    coordinate_distance: int | None = None,
    # Location - coordinates (exclusive)
    coordinate_latitude_exclusive: float | None = None,
    coordinate_longitude_exclusive: float | None = None,
    coordinate_distance_exclusive: int | None = None,
    # Contact values
    phone_number: list[str] | None = None,
    phone_number_exclusive: list[str] | None = None,
    email: list[str] | None = None,
    email_exclusive: list[str] | None = None,
    website: list[str] | None = None,
    website_exclusive: list[str] | None = None,
    website_ip_address: str | None = None,
    # Categories
    international_codes: list[str] | None = None,
    international_codes_exclusive: list[str] | None = None,
    infobel_codes: list[str] | None = None,
    infobel_codes_exclusive: list[str] | None = None,
    local_codes: list[str] | None = None,
    local_codes_exclusive: list[str] | None = None,
    alt_international_codes: list[str] | None = None,
    alt_international_codes_exclusive: list[str] | None = None,
    categories_keywords: list[str] | None = None,
    restrict_on_main_category: bool | None = None,
    # Presence filters
    has_address: bool | None = None,
    has_phone: bool | None = None,
    has_fax: bool | None = None,
    has_mobile: bool | None = None,
    has_email: bool | None = None,
    has_website: int | None = None,
    has_national_id: int | None = None,
    has_web_contact: bool | None = None,
    has_contact: bool | None = None,
    has_coordinates: bool | None = None,
    has_linked_in: bool | None = None,
    has_logo: bool | None = None,
    has_admin: bool | None = None,
    has_marketability: bool | None = None,
    has_building_geometry: bool | None = None,
    has_shop_tool: bool | None = None,
    has_payment: bool | None = None,
    has_digital_marketing: bool | None = None,
    has_e_shop: bool | None = None,
    # Deduplication filters
    has_phone_deduplicated: bool | None = None,
    has_email_deduplicated: bool | None = None,
    has_website_deduplicated: bool | None = None,
    has_web_domain_deduplicated: bool | None = None,
    has_national_id_deduplicated: bool | None = None,
    has_mobile_deduplicated: bool | None = None,
    has_contact_deduplicated: bool | None = None,
    # Business data
    year_started_from: str | None = None,
    year_started_to: str | None = None,
    employees_total_from: int | None = None,
    employees_total_to: int | None = None,
    sales_volume_from: int | None = None,
    sales_volume_to: int | None = None,
    sales_volume_currency: str | None = None,
    sales_volum_reliability_codes: list[int] | None = None,
    sales_volum_reliability_codes_exclusive: list[int] | None = None,
    family_members_from: str | None = None,
    family_members_to: str | None = None,
    # Business attributes
    is_published: bool | None = None,
    is_vat: bool | None = None,
    filter_on_dncm: bool | None = None,
    publishing_strength_from: str | None = None,
    publishing_strength_to: str | None = None,
    linked_in_followers_from: str | None = None,
    linked_in_followers_to: str | None = None,
    # Status & geo
    status_codes: list[str] | None = None,
    status_codes_exclusive: list[str] | None = None,
    geo_levels: list[int] | None = None,
    geo_levels_exclusive: list[int] | None = None,
    # Corporate structure
    parent_unique_id: list[str] | None = None,
    parent_unique_id_exclusive: list[str] | None = None,
    global_ultimate_unique_id: list[str] | None = None,
    global_ultimate_unique_id_exclusive: list[str] | None = None,
    global_ultimate_country_codes: list[str] | None = None,
    global_ultimate_country_codes_exclusive: list[str] | None = None,
    domestic_ultimate_unique_id: list[str] | None = None,
    domestic_ultimate_unique_id_exclusive: list[str] | None = None,
    # Executive
    ceo_name: str | None = None,
    ceo_title: str | None = None,
    executive_tags: list[str] | None = None,
    # Legal & identification
    legal_status_codes: list[str] | None = None,
    legal_status_codes_exclusive: list[str] | None = None,
    national_identification_type_codes: list[str] | None = None,
    national_identification_type_codes_exclusive: list[str] | None = None,
    import_export_agent_codes: list[str] | None = None,
    import_export_agent_codes_exclusive: list[str] | None = None,
    # Digital & technographic
    technographical_tags: list[str] | None = None,
    website_status_flags: list[int] | None = None,
    website_status_flags_exclusive: list[int] | None = None,
    social_links: list[str] | None = None,
    social_links_exclusive: list[str] | None = None,
    # Language
    languages: list[str] | None = None,
    languages_exclusive: list[str] | None = None,
    # Search settings
    can_match_any_business_filter: bool | None = None,
    try_any_location_match: bool | None = None,
    international_phone_format: bool | None = None,
    validate_filters: bool | None = None,
    display_language: str | None = None,
    page_size: int | None = None,
    sorting_order: list[dict] | None = None,
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
        business_name_exclusive: Business names to exclude.
        national_id: National registration numbers to include.
        national_id_exclusive: National registration numbers to exclude.
        unique_ids: Infobel unique IDs to look up directly.
        unique_ids_exclusive: Infobel unique IDs to exclude.
        city_names: Filter by city names (e.g. ["London", "Manchester"]).
        city_codes: Filter by city codes.
        city_codes_exclusive: City codes to exclude.
        province_names: Filter by province/state names.
        province_codes: Filter by province codes.
        province_codes_exclusive: Province codes to exclude.
        region_names: Filter by region names.
        region_codes: Filter by region codes.
        region_codes_exclusive: Region codes to exclude.
        post_codes: Filter by postal/zip codes.
        post_codes_exclusive: Postal codes to exclude.
        street_address: Street address filter.
        house_number: House number filter.
        coordinate_latitude: Latitude for inclusive geo-search.
        coordinate_longitude: Longitude for inclusive geo-search.
        coordinate_distance: Radius in meters for inclusive geo-search (default 100).
        coordinate_latitude_exclusive: Latitude for exclusive geo-search.
        coordinate_longitude_exclusive: Longitude for exclusive geo-search.
        coordinate_distance_exclusive: Radius in meters for exclusive geo-search.
        phone_number: Phone numbers to include.
        phone_number_exclusive: Phone numbers to exclude.
        email: Email addresses to include.
        email_exclusive: Email addresses to exclude.
        website: Website URLs to include.
        website_exclusive: Website URLs to exclude.
        website_ip_address: Filter by website IP address.
        international_codes: ISIC international category codes to include.
        international_codes_exclusive: ISIC codes to exclude.
        infobel_codes: Infobel proprietary category codes to include.
        infobel_codes_exclusive: Infobel codes to exclude.
        local_codes: Local/national category codes to include (e.g. SIC, NAF).
        local_codes_exclusive: Local codes to exclude.
        alt_international_codes: NACE category codes to include.
        alt_international_codes_exclusive: NACE codes to exclude.
        categories_keywords: Free-text category keywords.
        restrict_on_main_category: When True, match only the primary category.
        has_address: Filter for businesses with an address.
        has_phone: Filter for businesses with phone numbers.
        has_fax: Filter for businesses with fax numbers.
        has_mobile: Filter for businesses with mobile numbers.
        has_email: Filter for businesses with email addresses.
        has_website: PresenceType for website: 0=Ignore, 1=Has, 2=HasNot.
        has_national_id: PresenceType for national ID: 0=Ignore, 1=Has, 2=HasNot.
        has_web_contact: Filter for businesses with website or email.
        has_contact: Filter for businesses with phone or mobile.
        has_coordinates: Filter for businesses with GPS coordinates.
        has_linked_in: Filter for businesses with LinkedIn profiles.
        has_logo: Filter for businesses with logos.
        has_admin: Filter for businesses with admin data.
        has_marketability: Filter for marketable records.
        has_building_geometry: Filter for records with building geometry.
        has_shop_tool: Filter for businesses with shop tools.
        has_payment: Filter for businesses with payment capabilities.
        has_digital_marketing: Filter for businesses with digital marketing.
        has_e_shop: Filter for businesses with e-shops.
        has_phone_deduplicated: Deduplicate on phone (requires has_phone).
        has_email_deduplicated: Deduplicate on email (requires has_email).
        has_website_deduplicated: Deduplicate on website (requires has_website).
        has_web_domain_deduplicated: Deduplicate on domain (requires has_website).
        has_national_id_deduplicated: Deduplicate on national ID.
        has_mobile_deduplicated: Deduplicate on mobile.
        has_contact_deduplicated: Deduplicate on contact.
        year_started_from: Minimum year started (e.g. "2000").
        year_started_to: Maximum year started (e.g. "2020").
        employees_total_from: Minimum employee count.
        employees_total_to: Maximum employee count.
        sales_volume_from: Minimum sales volume.
        sales_volume_to: Maximum sales volume.
        sales_volume_currency: Currency for sales volume (use get_currencies for codes).
        sales_volum_reliability_codes: Sales reliability codes to include.
        sales_volum_reliability_codes_exclusive: Sales reliability codes to exclude.
        family_members_from: Minimum family member count.
        family_members_to: Maximum family member count.
        is_published: Filter by published status on infobel.com.
        is_vat: Filter where NationalID is also a VAT number.
        filter_on_dncm: Exclude DoNotCallMe records (Belgium only).
        publishing_strength_from: Minimum publishing strength (0+).
        publishing_strength_to: Maximum publishing strength (max 100).
        linked_in_followers_from: Minimum LinkedIn followers.
        linked_in_followers_to: Maximum LinkedIn followers.
        status_codes: Business hierarchy/status codes to include (use get_status_codes).
        status_codes_exclusive: Business status codes to exclude.
        geo_levels: Geographic precision levels to include (use get_geo_levels).
        geo_levels_exclusive: Geographic precision levels to exclude.
        parent_unique_id: Filter by parent company unique ID.
        parent_unique_id_exclusive: Parent unique IDs to exclude.
        global_ultimate_unique_id: Filter by global ultimate owner unique ID.
        global_ultimate_unique_id_exclusive: Global ultimate unique IDs to exclude.
        global_ultimate_country_codes: Filter by global ultimate country codes.
        global_ultimate_country_codes_exclusive: Global ultimate country codes to exclude.
        domestic_ultimate_unique_id: Filter by domestic ultimate owner unique ID.
        domestic_ultimate_unique_id_exclusive: Domestic ultimate unique IDs to exclude.
        ceo_name: CEO/executive name search.
        ceo_title: CEO/executive title search.
        executive_tags: Filter by executive tags (use get_executive_tags for values).
        legal_status_codes: Legal form codes to include (use get_legal_status_codes).
        legal_status_codes_exclusive: Legal form codes to exclude.
        national_identification_type_codes: National ID type codes to include.
        national_identification_type_codes_exclusive: National ID type codes to exclude.
        import_export_agent_codes: Import/export agent codes to include.
        import_export_agent_codes_exclusive: Import/export agent codes to exclude.
        technographical_tags: Filter by web technologies (use get_technographical_tags).
        website_status_flags: Website status flags to include (use get_website_status_flags).
        website_status_flags_exclusive: Website status flags to exclude.
        social_links: Social media platforms to include (use get_social_links for codes).
        social_links_exclusive: Social media platforms to exclude.
        languages: ISO 639-3 language codes to include.
        languages_exclusive: ISO 639-3 language codes to exclude.
        can_match_any_business_filter: When True, OR logic instead of AND.
        try_any_location_match: Use partial location matches if exact not found.
        international_phone_format: Return phone numbers with +xxx prefix.
        validate_filters: Validate provided filters before searching.
        display_language: Language for result display (e.g. "en", "fr").
        page_size: Results per page (default 20).
        sorting_order: Sorting options (use get_sorting_orders for values).
        data_type: Data type: "Business" (default), "YellowPages", or "WhitePages".
    """
    try:
        kwargs: dict[str, Any] = {"country_codes": country_codes, "return_first_page": False}

        # Map all non-None params into SearchInput kwargs
        _locals = {
            # Identity
            "business_name": business_name,
            "business_name_exclusive": business_name_exclusive,
            "national_id": national_id,
            "national_id_exclusive": national_id_exclusive,
            "unique_ids": unique_ids,
            "unique_ids_exclusive": unique_ids_exclusive,
            # Location
            "city_names": city_names,
            "city_codes": city_codes,
            "city_codes_exclusive": city_codes_exclusive,
            "province_names": province_names,
            "province_codes": province_codes,
            "province_codes_exclusive": province_codes_exclusive,
            "region_names": region_names,
            "region_codes": region_codes,
            "region_codes_exclusive": region_codes_exclusive,
            "post_codes": post_codes,
            "post_codes_exclusive": post_codes_exclusive,
            "street_address": street_address,
            "house_number": house_number,
            "website_ip_address": website_ip_address,
            # Contact
            "phone_number": phone_number,
            "phone_number_exclusive": phone_number_exclusive,
            "email": email,
            "email_exclusive": email_exclusive,
            "website": website,
            "website_exclusive": website_exclusive,
            # Categories
            "international_codes": international_codes,
            "international_codes_exclusive": international_codes_exclusive,
            "infobel_codes": infobel_codes,
            "infobel_codes_exclusive": infobel_codes_exclusive,
            "local_codes": local_codes,
            "local_codes_exclusive": local_codes_exclusive,
            "alt_international_codes": alt_international_codes,
            "alt_international_codes_exclusive": alt_international_codes_exclusive,
            "categories_keywords": categories_keywords,
            "restrict_on_main_category": restrict_on_main_category,
            # Presence
            "has_address": has_address,
            "has_phone": has_phone,
            "has_fax": has_fax,
            "has_mobile": has_mobile,
            "has_email": has_email,
            "has_website": has_website,
            "has_national_id": has_national_id,
            "has_web_contact": has_web_contact,
            "has_contact": has_contact,
            "has_coordinates": has_coordinates,
            "has_linked_in": has_linked_in,
            "has_logo": has_logo,
            "has_admin": has_admin,
            "has_marketability": has_marketability,
            "has_building_geometry": has_building_geometry,
            "has_shop_tool": has_shop_tool,
            "has_payment": has_payment,
            "has_digital_marketing": has_digital_marketing,
            "has_e_shop": has_e_shop,
            # Deduplication
            "has_phone_deduplicated": has_phone_deduplicated,
            "has_email_deduplicated": has_email_deduplicated,
            "has_website_deduplicated": has_website_deduplicated,
            "has_web_domain_deduplicated": has_web_domain_deduplicated,
            "has_national_id_deduplicated": has_national_id_deduplicated,
            "has_mobile_deduplicated": has_mobile_deduplicated,
            "has_contact_deduplicated": has_contact_deduplicated,
            # Business data
            "year_started_from": year_started_from,
            "year_started_to": year_started_to,
            "employees_total_from": employees_total_from,
            "employees_total_to": employees_total_to,
            "sales_volume_from": sales_volume_from,
            "sales_volume_to": sales_volume_to,
            "sales_volume_currency": sales_volume_currency,
            "sales_volum_reliability_codes": sales_volum_reliability_codes,
            "sales_volum_reliability_codes_exclusive": sales_volum_reliability_codes_exclusive,
            "family_members_from": family_members_from,
            "family_members_to": family_members_to,
            # Attributes
            "is_published": is_published,
            "is_vat": is_vat,
            "filter_on_dncm": filter_on_dncm,
            "publishing_strength_from": publishing_strength_from,
            "publishing_strength_to": publishing_strength_to,
            "linked_in_followers_from": linked_in_followers_from,
            "linked_in_followers_to": linked_in_followers_to,
            # Status & geo
            "status_codes": status_codes,
            "status_codes_exclusive": status_codes_exclusive,
            "geo_levels": geo_levels,
            "geo_levels_exclusive": geo_levels_exclusive,
            # Corporate
            "parent_unique_id": parent_unique_id,
            "parent_unique_id_exclusive": parent_unique_id_exclusive,
            "global_ultimate_unique_id": global_ultimate_unique_id,
            "global_ultimate_unique_id_exclusive": global_ultimate_unique_id_exclusive,
            "global_ultimate_country_codes": global_ultimate_country_codes,
            "global_ultimate_country_codes_exclusive": global_ultimate_country_codes_exclusive,
            "domestic_ultimate_unique_id": domestic_ultimate_unique_id,
            "domestic_ultimate_unique_id_exclusive": domestic_ultimate_unique_id_exclusive,
            # Executive
            "ceo_name": ceo_name,
            "ceo_title": ceo_title,
            "executive_tags": executive_tags,
            # Legal & identification
            "legal_status_codes": legal_status_codes,
            "legal_status_codes_exclusive": legal_status_codes_exclusive,
            "national_identification_type_codes": national_identification_type_codes,
            "national_identification_type_codes_exclusive": national_identification_type_codes_exclusive,
            "import_export_agent_codes": import_export_agent_codes,
            "import_export_agent_codes_exclusive": import_export_agent_codes_exclusive,
            # Digital & technographic
            "technographical_tags": technographical_tags,
            "website_status_flags": website_status_flags,
            "website_status_flags_exclusive": website_status_flags_exclusive,
            "social_links": social_links,
            "social_links_exclusive": social_links_exclusive,
            # Language
            "languages": languages,
            "languages_exclusive": languages_exclusive,
            # Settings
            "can_match_any_business_filter": can_match_any_business_filter,
            "try_any_location_match": try_any_location_match,
            "international_phone_format": international_phone_format,
            "validate_filters": validate_filters,
            "display_language": display_language,
            "page_size": page_size,
            "sorting_order": sorting_order,
            "data_type": data_type,
        }

        for k, v in _locals.items():
            if v is not None:
                kwargs[k] = v

        # Handle inclusive coordinate option
        if coordinate_latitude is not None and coordinate_longitude is not None:
            coord = {"Latitude": coordinate_latitude, "Longitude": coordinate_longitude}
            if coordinate_distance is not None:
                coord["Distance"] = coordinate_distance
            from .models.common import CoordinateOption
            kwargs["coordinate_options"] = [CoordinateOption(**coord)]

        # Handle exclusive coordinate option
        if coordinate_latitude_exclusive is not None and coordinate_longitude_exclusive is not None:
            coord_excl = {"Latitude": coordinate_latitude_exclusive, "Longitude": coordinate_longitude_exclusive}
            if coordinate_distance_exclusive is not None:
                coord_excl["Distance"] = coordinate_distance_exclusive
            from .models.common import CoordinateOption
            kwargs["coordinate_options_exclusive"] = [CoordinateOption(**coord_excl)]

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
    except InfobelAPIError as e:
        return _json({"error": str(e), "status_code": e.status_code})


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
    try:
        fields = _ensure_unique_id(record_fields)
        return _json(_get_client().search.post_records(search_id, page, fields))
    except InfobelAPIError as e:
        return _json({"error": str(e), "status_code": e.status_code})


@mcp.tool()
def get_search_status(search_id: int) -> str:
    """Check the status of a previous search.

    Args:
        search_id: Search ID returned by search_businesses.
    """
    try:
        return _json(_get_client().search.get_status(search_id))
    except InfobelAPIError as e:
        return _json({"error": str(e), "status_code": e.status_code})


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
    try:
        return _json(_get_client().record.get(country_code, unique_id))
    except InfobelAPIError as e:
        return _json({"error": str(e), "status_code": e.status_code})


@mcp.tool()
def get_record_partial(country_code: str, unique_id: str) -> str:
    """Get a partial (lighter) record for a business.

    Args:
        country_code: ISO 3166-1 alpha-2 country code (e.g. "GB").
        unique_id: Infobel unique ID for the business.
    """
    try:
        return _json(_get_client().record.get_partial(country_code, unique_id))
    except InfobelAPIError as e:
        return _json({"error": str(e), "status_code": e.status_code})


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
    try:
        return _json(_get_client().categories.search_infobel(keywords, language_code))
    except InfobelAPIError as e:
        return _json({"error": str(e), "status_code": e.status_code})


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
    try:
        return _json(_get_client().categories.search_international(keywords, language_code))
    except InfobelAPIError as e:
        return _json({"error": str(e), "status_code": e.status_code})


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
    try:
        return _json(_get_client().categories.search_local(keywords, country_code, language_code))
    except InfobelAPIError as e:
        return _json({"error": str(e), "status_code": e.status_code})


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
    try:
        return _json(_get_client().categories.search_alt_international(keywords, language_code))
    except InfobelAPIError as e:
        return _json({"error": str(e), "status_code": e.status_code})


# ---------------------------------------------------------------------------
# Locations — hierarchy: regions → provinces → cities
# ---------------------------------------------------------------------------

@mcp.tool()
def get_regions(country_code: str, language_code: str = "en") -> str:
    """List all regions for a country. Use the returned codes as region_code in get_provinces.

    Args:
        country_code: ISO 3166-1 alpha-2 country code (e.g. "GB", "DE").
        language_code: Display language for results (e.g. "en", "de", "fr").
    """
    try:
        return _json(_get_client().locations.get_regions(country_code, language_code=language_code))
    except InfobelAPIError as e:
        return _json({"error": str(e), "status_code": e.status_code})


@mcp.tool()
def get_provinces(country_code: str, region_code: str | None = None, language_code: str = "en") -> str:
    """List provinces for a country, optionally filtered by region code.

    Use the returned codes as province_code in get_cities or search_businesses.

    Args:
        country_code: ISO 3166-1 alpha-2 country code (e.g. "GB", "DE").
        region_code: Optional region code from get_regions to narrow results.
        language_code: Display language for results (e.g. "en", "de", "fr").
    """
    try:
        client = _get_client()
        if region_code:
            data = client.locations.get_provinces_by_region(country_code, region_code, language_code=language_code)
        else:
            data = client.locations.get_provinces(country_code, language_code=language_code)
        return _json(data)
    except InfobelAPIError as e:
        return _json({"error": str(e), "status_code": e.status_code})


@mcp.tool()
def get_cities(country_code: str, keyword: str, province_code: str | None = None, language_code: str = "en") -> str:
    """Search cities within a country by keyword.

    Use the returned codes as city_codes in search_businesses filters.
    Always provide a specific city name or partial name — never call without a keyword.

    Args:
        country_code: ISO 3166-1 alpha-2 country code (e.g. "US", "GB").
        keyword: City name or partial name to search for (e.g. "New York", "Munich").
        province_code: Optional province code to narrow results to a specific province/state.
        language_code: Display language for results (e.g. "en", "de", "fr").
    """
    try:
        results = _get_client().locations.search_keywords([keyword], country_code, language_code=language_code)
        cities = [r for r in results if isinstance(r, dict) and r.get("type") == "City"]
        if province_code:
            cities = [c for c in cities if c.get("parentCode") == province_code]
        return _json(cities)
    except InfobelAPIError as e:
        return _json({"error": str(e), "status_code": e.status_code})


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
    try:
        return _json(_get_client().locations.search_keywords(keywords, country_code, language_code=language_code))
    except InfobelAPIError as e:
        return _json({"error": str(e), "status_code": e.status_code})


# ---------------------------------------------------------------------------
# Reference data
# ---------------------------------------------------------------------------

@mcp.tool()
def get_available_countries() -> str:
    """List all countries available in the Infobel database."""
    try:
        return _json(_get_client().countries.get_all())
    except InfobelAPIError as e:
        return _json({"error": str(e), "status_code": e.status_code})


@mcp.tool()
def get_languages() -> str:
    """List available display languages for API results."""
    try:
        return _json(_get_client().utils.get_languages())
    except InfobelAPIError as e:
        return _json({"error": str(e), "status_code": e.status_code})


@mcp.tool()
def get_reliability_codes() -> str:
    """List reliability codes and their meanings."""
    try:
        return _json(_get_client().utils.get_reliability_codes())
    except InfobelAPIError as e:
        return _json({"error": str(e), "status_code": e.status_code})


@mcp.tool()
def get_status_codes() -> str:
    """List business status / hierarchy codes and their meanings.

    Returns the BusinessStatusCode enum values used in the search_businesses
    `status_codes` and `status_codes_exclusive` filters. Values indicate the
    physical location type: SingleLocation (0), HQ (1), Branch (2).
    """
    try:
        return _json(_get_client().utils.get_status_codes())
    except InfobelAPIError as e:
        return _json({"error": str(e), "status_code": e.status_code})


@mcp.tool()
def get_geo_levels() -> str:
    """List geographic precision levels used in the `geo_levels` search filter.

    Returns codes and descriptions indicating the geocoding accuracy of a record
    (e.g. address-level, city-level, country-level).
    """
    try:
        return _json(_get_client().utils.get_geo_levels())
    except InfobelAPIError as e:
        return _json({"error": str(e), "status_code": e.status_code})


@mcp.tool()
def get_currencies() -> str:
    """List supported currencies for the `sales_volume_currency` search filter.

    Returns currency codes such as Local (0), USD (1), EUR (2).
    """
    try:
        return _json(_get_client().utils.get_currencies())
    except InfobelAPIError as e:
        return _json({"error": str(e), "status_code": e.status_code})


@mcp.tool()
def get_sorting_orders() -> str:
    """List available sorting order options for the `sorting_order` search parameter."""
    try:
        return _json(_get_client().utils.get_sorting_orders())
    except InfobelAPIError as e:
        return _json({"error": str(e), "status_code": e.status_code})


@mcp.tool()
def get_website_status_flags() -> str:
    """List website status flags used in the `website_status_flags` search filter.

    Returns integer codes and descriptions indicating the crawl/availability
    status of a business website.
    """
    try:
        return _json(_get_client().utils.get_website_status_flags())
    except InfobelAPIError as e:
        return _json({"error": str(e), "status_code": e.status_code})


@mcp.tool()
def get_social_links() -> str:
    """List supported social media platforms for the `social_links` search filter.

    Returns platform codes (e.g. "linkedin", "facebook") to use when filtering
    businesses by social media presence.
    """
    try:
        return _json(_get_client().utils.get_social_links())
    except InfobelAPIError as e:
        return _json({"error": str(e), "status_code": e.status_code})


@mcp.tool()
def get_import_export_agent_codes() -> str:
    """List import/export agent codes for the `import_export_agent_codes` search filter."""
    try:
        return _json(_get_client().utils.get_import_export_agent_codes())
    except InfobelAPIError as e:
        return _json({"error": str(e), "status_code": e.status_code})


def _filter_by_keyword(items: list[dict], keyword: str | None) -> list[dict]:
    """Prefilter a list of dicts by keyword match against any value (case-insensitive)."""
    if not keyword:
        return items
    kw = keyword.lower()
    return [item for item in items if any(kw in str(v).lower() for v in item.values())]


@mcp.tool()
def get_legal_status_codes(country_code: str, keyword: str | None = None) -> str:
    """List legal status codes (business legal forms) for a country.

    Use the returned codes in the search_businesses `legal_status_codes` and
    `legal_status_codes_exclusive` filters.

    Args:
        country_code: ISO 3166-1 alpha-2 country code (e.g. "BE", "DE", "FR").
        keyword: Optional keyword to filter results (e.g. "SA", "GmbH", "Ltd").
    """
    try:
        data = _get_client().utils.get_legal_status_codes(country_code)
        return _json(_filter_by_keyword(data, keyword))
    except InfobelAPIError as e:
        return _json({"error": str(e), "status_code": e.status_code})


@mcp.tool()
def get_national_id_types(country_code: str) -> str:
    """List national identification type codes for a country.

    Use the returned codes in the search_businesses
    `national_identification_type_codes` filter.

    Args:
        country_code: ISO 3166-1 alpha-2 country code (e.g. "BE", "GB", "US").
    """
    try:
        return _json(_get_client().utils.get_national_id_types(country_code))
    except InfobelAPIError as e:
        return _json({"error": str(e), "status_code": e.status_code})


@mcp.tool()
def get_technographical_tags(keyword: str | None = None) -> str:
    """List technographic tags for the `technographical_tags` search filter.

    Technographic tags identify web technologies used by a business
    (e.g. specific CMS, e-commerce platforms, analytics tools).

    Args:
        keyword: Optional keyword to filter results (e.g. "shopify", "wordpress").
    """
    try:
        data = _get_client().utils.get_technographical_tags()
        return _json(_filter_by_keyword(data, keyword))
    except InfobelAPIError as e:
        return _json({"error": str(e), "status_code": e.status_code})


@mcp.tool()
def get_executive_tags(keyword: str | None = None) -> str:
    """List executive tags for the `executive_tags` search filter.

    Executive tags describe attributes or roles of business executives.

    Args:
        keyword: Optional keyword to filter results (e.g. "ceo", "founder").
    """
    try:
        data = _get_client().utils.get_executive_tags()
        return _json(_filter_by_keyword(data, keyword))
    except InfobelAPIError as e:
        return _json({"error": str(e), "status_code": e.status_code})


@mcp.tool()
def test_connection() -> str:
    """Verify API connectivity and authentication."""
    try:
        return _json(_get_client().test.hello())
    except InfobelAPIError as e:
        return _json({"error": str(e), "status_code": e.status_code})


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
