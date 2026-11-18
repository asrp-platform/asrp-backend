HEAR_ABOUT_ASRP_OPTIONS: tuple[dict[str, str], ...] = (
    {"value": "colleague", "label": "Colleague"},
    {"value": "friend", "label": "Friend"},
    {"value": "social_media", "label": "Social media"},
    {"value": "telegram", "label": "Telegram"},
    {"value": "conference", "label": "Conference / meeting"},
    {"value": "web_search", "label": "Web search"},
    {"value": "other", "label": "Other"},
)

HEAR_ABOUT_ASRP_VALUES: tuple[str, ...] = tuple(option["value"] for option in HEAR_ABOUT_ASRP_OPTIONS)
