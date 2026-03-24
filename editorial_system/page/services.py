TRANSLATION_MANUALLY_REVIEWED = "manually_reviewed"


def get_translated_content(page, requested_lang):
    def _is_state_payload(value):
        if not isinstance(value, dict):
            return False
        if "state" in value and set(value.keys()).issubset({"state", "updated_at"}):
            return True
        return bool(value) and all(
            isinstance(item, dict)
            and "state" in item
            and set(item.keys()).issubset({"state", "updated_at"})
            for item in value.values()
        )

    normalized_lang = (requested_lang or page.lang or "cs").strip().lower()
    translation_map = page.content_i18n or {}

    if normalized_lang == page.lang:
        return page.content_json
    if normalized_lang in translation_map and not _is_state_payload(translation_map[normalized_lang]):
        return translation_map[normalized_lang]

    base_lang = normalized_lang.split("-")[0]
    if base_lang in translation_map and not _is_state_payload(translation_map[base_lang]):
        return translation_map[base_lang]

    for key, value in translation_map.items():
        if key.split("-")[0] == base_lang and not _is_state_payload(value):
            return value

    return page.content_json
