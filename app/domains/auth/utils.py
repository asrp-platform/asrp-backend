from functools import lru_cache


SUPPORTED_COUNTRIES = [
    {"code": "US", "name": "United States"},
    {"code": "RU", "name": "Russia"},
    {"code": "KZ", "name": "Kazakhstan"},
    {"code": "BY", "name": "Belarus"},
    {"code": "UA", "name": "Ukraine"},
    {"code": "AM", "name": "Armenia"},
    {"code": "GE", "name": "Georgia"},
    {"code": "TR", "name": "Türkiye"},
    {"code": "DE", "name": "Germany"},
    {"code": "IL", "name": "Israel"},
    {"code": "CA", "name": "Canada"},
]


COUNTRY_ADDRESS_RULES = {
    "US": {
        "state_required": True,
        "postal_code_required": True,
        "state_label": "State",
        "postal_code_label": "ZIP Code",
        "postal_code_pattern": r"^\d{5}(-\d{4})?$",
        "supports_us_tax_calculation": True,
    },
}

DEFAULT_ADDRESS_RULES = {
    "state_required": False,
    "postal_code_required": False,
    "state_label": "State / Province",
    "postal_code_label": "Postal Code",
    "postal_code_pattern": None,
    "supports_us_tax_calculation": False,
}


@lru_cache
def get_countries() -> list[dict]:
    result = []

    for country in SUPPORTED_COUNTRIES:
        code = country["code"]

        result.append({
            **country,
            **DEFAULT_ADDRESS_RULES,
            **COUNTRY_ADDRESS_RULES.get(code, {}),
        })

    result.append({
        "code": "__OTHER__",
        "name": "Other country",
        **DEFAULT_ADDRESS_RULES,
    })

    return result
