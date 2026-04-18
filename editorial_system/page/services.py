TRANSLATION_MANUALLY_REVIEWED = "manually_reviewed"


def get_translated_content(page, requested_lang):
    normalized_lang = (requested_lang or page.lang or "cs").strip().lower()

    if normalized_lang == page.lang:
        return page.content_json

    translation_map = {t.lang: t.content_json for t in page.translations.all()}

    if normalized_lang in translation_map:
        return translation_map[normalized_lang]

    base_lang = normalized_lang.split("-")[0]
    if base_lang in translation_map:
        return translation_map[base_lang]

    for lang, content in translation_map.items():
        if lang.split("-")[0] == base_lang:
            return content

    return page.content_json