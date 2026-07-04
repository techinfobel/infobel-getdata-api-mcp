"""Domain knowledge tables used to annotate resolver results.

Static tables of known quirks in the category and location systems. They
capture recurring pitfalls observed in real customer engagements so that
callers get a warning at code-resolution time instead of discovering the
problem in a wrong count.
"""

from __future__ import annotations

from typing import Any

# ---------------------------------------------------------------------------
# Categories
# ---------------------------------------------------------------------------

# Infobel category codes known to cover more than one everyday concept.
# Applies to the Infobel proprietary system only (other systems have their
# own code spaces and may collide numerically).
CATEGORY_CODE_CONFLATIONS: dict[str, str] = {
    "018513": (
        "covers both shopping malls/shopping centres and department stores; "
        "counts on this code include both concepts."
    ),
    "017102": (
        "covers both cafes/coffee houses and bars; counts on this code "
        "include both concepts."
    ),
}

# Free-text terms whose category mapping is regularly misread. Matched as
# case-insensitive substrings of the caller's keywords.
CATEGORY_KEYWORD_CAUTIONS: dict[str, str] = {
    "mall": "Shopping malls share Infobel code 018513 with department stores.",
    "department store": "Department stores share Infobel code 018513 with shopping malls.",
    "cafe": "Cafes share Infobel code 017102 with bars.",
    "café": "Cafes share Infobel code 017102 with bars.",
    "coffee": "Coffee houses share Infobel code 017102 with bars.",
    "bar": "Bars share Infobel code 017102 with cafes/coffee houses.",
    "parking": "Parking and garage concepts are conflated in the category system; review the returned codes before counting.",
    "garage": "Parking and garage concepts are conflated in the category system; review the returned codes before counting.",
    "school": "School category codes cover formal educational institutions; training businesses such as driving or flight schools sit under separate codes.",
}


def category_code_warnings(items: list[Any]) -> list[str]:
    """Return warnings for known-conflated Infobel codes present in items."""
    warnings: list[str] = []
    for item in items:
        code = item.get("code") if isinstance(item, dict) else None
        note = CATEGORY_CODE_CONFLATIONS.get(str(code)) if code is not None else None
        if note:
            warnings.append(f"Code {code} {note}")
    return _dedupe(warnings)


def category_keyword_cautions(keywords: list[str]) -> list[str]:
    """Return cautions triggered by the caller's free-text keywords."""
    cautions: list[str] = []
    for kw in keywords:
        lowered = kw.lower()
        for term, note in CATEGORY_KEYWORD_CAUTIONS.items():
            if term in lowered:
                cautions.append(note)
    return _dedupe(cautions)


# ---------------------------------------------------------------------------
# Locations
# ---------------------------------------------------------------------------

# Location result types mapped to the search_businesses filter that accepts
# their codes. Filtering at the wrong level (city vs province/state) is a
# recurring source of wrong counts.
LOCATION_TYPE_TO_FILTER: dict[str, str] = {
    "City": "city_codes",
    "Province": "province_codes",
    "Region": "region_codes",
}


def _dedupe(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for v in values:
        if v not in seen:
            seen.add(v)
            result.append(v)
    return result
