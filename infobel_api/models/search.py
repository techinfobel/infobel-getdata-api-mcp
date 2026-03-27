"""Search-related models."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field, ConfigDict

from .common import CoordinateOption


class SearchInput(BaseModel):
    """
    Full search payload model. Users write snake_case; pydantic serializes
    to PascalCase via aliases for the API.
    """

    model_config = ConfigDict(populate_by_name=True)

    # Core settings
    data_type: str | None = Field(default="Business", alias="DataType")
    can_match_any_business_filter: bool | None = Field(default=None, alias="CanMatchAnyBusinessFilter")
    page_size: int | None = Field(default=20, alias="PageSize")
    display_language: str | None = Field(default=None, alias="DisplayLanguage")
    international_phone_format: bool | None = Field(default=None, alias="InternationalPhoneFormat")
    validate_filters: bool | None = Field(default=None, alias="ValidateFilters")
    return_first_page: bool | None = Field(default=False, alias="ReturnFirstPage")
    track_scores: bool | None = Field(default=None, alias="TrackScores")
    try_any_location_match: bool | None = Field(default=None, alias="TryAnyLocationMatch")
    sorting_order: list[dict] | None = Field(default=None, alias="SortingOrder")
    detailed_counts: dict | None = Field(default=None, alias="DetailedCounts")
    settings: dict | None = Field(default=None, alias="Settings")
    who: str | None = Field(default=None, alias="Who")
    where: str | None = Field(default=None, alias="Where")

    # Country
    country_codes: list[str] | None = Field(default=None, alias="CountryCodes")

    # Unique IDs
    unique_ids: list[str] | None = Field(default=None, alias="UniqueIDs")
    unique_ids_exclusive: list[str] | None = Field(default=None, alias="UniqueIDsExclusive")

    # Business name
    business_name: list[str] | None = Field(default=None, alias="BusinessName")
    business_name_exclusive: list[str] | None = Field(default=None, alias="BusinessNameExclusive")

    # Languages
    languages: list[str] | None = Field(default=None, alias="Languages")
    languages_exclusive: list[str] | None = Field(default=None, alias="LanguagesExclusive")

    # Location - Cities
    city_codes: list[str] | None = Field(default=None, alias="CityCodes")
    city_names: list[str] | None = Field(default=None, alias="CityNames")
    city_codes_exclusive: list[str] | None = Field(default=None, alias="CityCodesExclusive")

    # Location - Provinces
    province_codes: list[str] | None = Field(default=None, alias="ProvinceCodes")
    province_names: list[str] | None = Field(default=None, alias="ProvinceNames")
    province_codes_exclusive: list[str] | None = Field(default=None, alias="ProvinceCodesExclusive")

    # Location - Regions
    region_codes: list[str] | None = Field(default=None, alias="RegionCodes")
    region_names: list[str] | None = Field(default=None, alias="RegionNames")
    region_codes_exclusive: list[str] | None = Field(default=None, alias="RegionCodesExclusive")

    # Location - Postal codes
    post_codes: list[str] | None = Field(default=None, alias="PostCodes")
    post_codes_exclusive: list[str] | None = Field(default=None, alias="PostCodesExclusive")

    # Location - Coordinates
    coordinate_options: list[CoordinateOption] | None = Field(default=None, alias="CoordinateOptions")
    coordinate_options_exclusive: list[CoordinateOption] | None = Field(default=None, alias="CoordinateOptionsExclusive")

    # Location - Address
    street_address: str | None = Field(default=None, alias="StreetAddress")
    house_number: str | None = Field(default=None, alias="HouseNumber")

    # Categories - International
    international_codes: list[str] | None = Field(default=None, alias="InternationalCodes")
    international_codes_exclusive: list[str] | None = Field(default=None, alias="InternationalCodesExclusive")
    categories_keywords: list[str] | None = Field(default=None, alias="CategoriesKeywords")
    restrict_on_main_category: bool | None = Field(default=None, alias="RestrictOnMainCategory")

    # Categories - Infobel
    infobel_codes: list[str] | None = Field(default=None, alias="InfobelCodes")
    infobel_codes_exclusive: list[str] | None = Field(default=None, alias="InfobelCodesExclusive")

    # Categories - Local
    local_codes: list[str] | None = Field(default=None, alias="LocalCodes")
    local_codes_exclusive: list[str] | None = Field(default=None, alias="LocalCodesExclusive")

    # Categories - Alt International (NACE)
    alt_international_codes: list[str] | None = Field(default=None, alias="AltInternationalCodes")
    alt_international_codes_exclusive: list[str] | None = Field(default=None, alias="AltInternationalCodesExclusive")

    # Contact presence filters
    has_address: bool | None = Field(default=None, alias="HasAddress")
    has_phone: bool | None = Field(default=None, alias="HasPhone")
    has_fax: bool | None = Field(default=None, alias="HasFax")
    has_mobile: bool | None = Field(default=None, alias="HasMobile")
    has_email: bool | None = Field(default=None, alias="HasEmail")
    has_website: int | None = Field(default=None, alias="HasWebsite")  # PresenceType: 0=Ignore, 1=Has, 2=HasNot
    has_national_id: int | None = Field(default=None, alias="HasNationalID")  # PresenceType: 0=Ignore, 1=Has, 2=HasNot
    has_web_contact: bool | None = Field(default=None, alias="HasWebContact")
    has_contact: bool | None = Field(default=None, alias="HasContact")
    has_coordinates: bool | None = Field(default=None, alias="HasCoordinates")

    # Contact value filters
    phone_number: list[str] | None = Field(default=None, alias="PhoneNumber")
    phone_number_exclusive: list[str] | None = Field(default=None, alias="PhoneNumberExclusive")
    email: list[str] | None = Field(default=None, alias="Email")
    email_exclusive: list[str] | None = Field(default=None, alias="EmailExclusive")
    website: list[str] | None = Field(default=None, alias="Website")
    website_exclusive: list[str] | None = Field(default=None, alias="WebsiteExclusive")
    national_id: list[str] | None = Field(default=None, alias="NationalID")
    national_id_exclusive: list[str] | None = Field(default=None, alias="NationalIDExclusive")

    # Deduplication
    has_phone_deduplicated: bool | None = Field(default=None, alias="HasPhoneDeduplicated")
    has_email_deduplicated: bool | None = Field(default=None, alias="HasEmailDeduplicated")
    has_website_deduplicated: bool | None = Field(default=None, alias="HasWebsiteDeduplicated")
    has_web_domain_deduplicated: bool | None = Field(default=None, alias="HasWebDomainDeduplicated")
    has_national_id_deduplicated: bool | None = Field(default=None, alias="HasNationalIDDeduplicated")
    has_mobile_deduplicated: bool | None = Field(default=None, alias="HasMobileDeduplicated")
    has_contact_deduplicated: bool | None = Field(default=None, alias="HasContactDeduplicated")

    # Business data
    year_started_from: str | None = Field(default=None, alias="YearStartedFrom")
    year_started_to: str | None = Field(default=None, alias="YearStartedTo")
    employees_total_from: int | None = Field(default=None, alias="EmployeesTotalFrom")
    employees_total_to: int | None = Field(default=None, alias="EmployeesTotalTo")
    sales_volume_from: int | None = Field(default=None, alias="SalesVolumeFrom")
    sales_volume_to: int | None = Field(default=None, alias="SalesVolumeTo")
    sales_volume_currency: str | None = Field(default=None, alias="SalesVolumeCurrency")
    sales_volum_reliability_codes: list[int] | None = Field(default=None, alias="SalesVolumReliabilityCodes")
    sales_volum_reliability_codes_exclusive: list[int] | None = Field(default=None, alias="SalesVolumReliabilityCodesExclusive")
    family_members_from: str | None = Field(default=None, alias="FamilyMembersFrom")
    family_members_to: str | None = Field(default=None, alias="FamilyMembersTo")

    # Business attributes
    is_published: bool | None = Field(default=None, alias="IsPublished")
    is_vat: bool | None = Field(default=None, alias="IsVAT")
    has_admin: bool | None = Field(default=None, alias="HasAdmin")
    has_marketability: bool | None = Field(default=None, alias="HasMarketability")
    has_building_geometry: bool | None = Field(default=None, alias="HasBuildingGeometry")
    has_linked_in: bool | None = Field(default=None, alias="HasLinkedIn")
    has_logo: bool | None = Field(default=None, alias="HasLogo")
    linked_in_followers_from: str | None = Field(default=None, alias="LinkedInFollowersFrom")
    linked_in_followers_to: str | None = Field(default=None, alias="LinkedInFollowersTo")
    publishing_strength_from: str | None = Field(default=None, alias="PublishingStrengthFrom")
    publishing_strength_to: str | None = Field(default=None, alias="PublishingStrengthTo")
    filter_on_dncm: bool | None = Field(default=None, alias="FilterOnDNCM")

    # Status & geo levels
    status_codes: list[str] | None = Field(default=None, alias="StatusCodes")
    status_codes_exclusive: list[str] | None = Field(default=None, alias="StatusCodesExclusive")
    geo_levels: list[int] | None = Field(default=None, alias="GeoLevels")
    geo_levels_exclusive: list[int] | None = Field(default=None, alias="GeoLevelsExclusive")

    # Corporate structure
    parent_unique_id: list[str] | None = Field(default=None, alias="ParentUniqueID")
    parent_unique_id_exclusive: list[str] | None = Field(default=None, alias="ParentUniqueIDExclusive")
    global_ultimate_unique_id: list[str] | None = Field(default=None, alias="GlobalUltimateUniqueID")
    global_ultimate_unique_id_exclusive: list[str] | None = Field(default=None, alias="GlobalUltimateUniqueIDExclusive")
    global_ultimate_country_codes: list[str] | None = Field(default=None, alias="GlobalUltimateCountryCodes")
    global_ultimate_country_codes_exclusive: list[str] | None = Field(default=None, alias="GlobalUltimateCountryCodesExclusive")
    domestic_ultimate_unique_id: list[str] | None = Field(default=None, alias="DomesticUltimateUniqueID")
    domestic_ultimate_unique_id_exclusive: list[str] | None = Field(default=None, alias="DomesticUltimateUniqueIDExclusive")

    # Executive
    ceo_name: str | None = Field(default=None, alias="CEOName")
    ceo_title: str | None = Field(default=None, alias="CEOTitle")
    executive_tags: list[str] | None = Field(default=None, alias="ExecutiveTags")

    # Legal & identification
    legal_status_codes: list[str] | None = Field(default=None, alias="LegalStatusCodes")
    legal_status_codes_exclusive: list[str] | None = Field(default=None, alias="LegalStatusCodesExclusive")
    national_identification_type_codes: list[str] | None = Field(default=None, alias="NationalIdentificationTypeCodes")
    national_identification_type_codes_exclusive: list[str] | None = Field(default=None, alias="NationalIdentificationTypeCodesExclusive")
    import_export_agent_codes: list[str] | None = Field(default=None, alias="ImportExportAgentCodes")
    import_export_agent_codes_exclusive: list[str] | None = Field(default=None, alias="ImportExportAgentCodesExclusive")

    # Digital & technographic
    has_shop_tool: bool | None = Field(default=None, alias="HasShopTool")
    has_payment: bool | None = Field(default=None, alias="HasPayment")
    has_digital_marketing: bool | None = Field(default=None, alias="HasDigitalMarketing")
    has_e_shop: bool | None = Field(default=None, alias="HasEShop")
    technographical_tags: list[str] | None = Field(default=None, alias="TechnographicalTags")
    website_status_flags: list[int] | None = Field(default=None, alias="WebsiteStatusFlags")
    website_status_flags_exclusive: list[int] | None = Field(default=None, alias="WebsiteStatusFlagsExclusive")
    website_ip_address: str | None = Field(default=None, alias="WebsiteIpAddress")

    # Social
    social_links: list[str] | None = Field(default=None, alias="SocialLinks")
    social_links_exclusive: list[str] | None = Field(default=None, alias="SocialLinksExclusive")

    # Validation
    validate_filters: bool | None = Field(default=None, alias="ValidateFilters")

    def to_api_payload(self) -> dict:
        """Serialize to API-compatible dict with PascalCase keys, excluding None values."""
        return self.model_dump(by_alias=True, exclude_none=True)


class SearchResponse(BaseModel):
    """Response from POST /api/search."""

    search_id: int | None = Field(default=None, alias="searchId")
    counts: dict[str, Any] = Field(default_factory=dict)
    first_page_records: list[dict[str, Any]] = Field(default_factory=list, alias="firstPageRecords")

    model_config = ConfigDict(populate_by_name=True)

    @property
    def total(self) -> int:
        return self.counts.get("total", 0)


class PaginatedResponse(BaseModel):
    """Response from GET /api/search/{id}/records/{page}."""

    search_id: int | None = Field(default=None, alias="searchId")
    page: int = 0
    record_count: int = Field(default=0, alias="recordCount")
    total_record_count: int = Field(default=0, alias="totalRecordCount")
    records: list[dict[str, Any]] = Field(default_factory=list)

    model_config = ConfigDict(populate_by_name=True)
