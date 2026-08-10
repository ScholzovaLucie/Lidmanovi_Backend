TRANSLATION_MANUALLY_REVIEWED = "manually_reviewed"


def resolve_translation(page, requested_lang):
    """
    Finds the PageTranslation matching requested_lang, trying an exact match first, then the
    base language (e.g. "en" for "en-US"), then any translation sharing that base language.
    Returns None if requested_lang is the page's own source language or no translation matches
    at all - callers should fall back to the page's own content_json in that case.

    This is the single source of truth for language fallback: both the response content
    (get_translated_content) and the reported translation_status use it, so they can't disagree
    about which translation was actually used.
    """
    normalized_lang = (requested_lang or page.lang or "cs").strip().lower()

    if normalized_lang == page.lang:
        return None

    translations_by_lang = {t.lang: t for t in page.translations.all()}

    if normalized_lang in translations_by_lang:
        return translations_by_lang[normalized_lang]

    base_lang = normalized_lang.split("-")[0]
    if base_lang in translations_by_lang:
        return translations_by_lang[base_lang]

    for lang, translation in translations_by_lang.items():
        if lang.split("-")[0] == base_lang:
            return translation

    return None


def get_translated_content(page, requested_lang):
    translation = resolve_translation(page, requested_lang)
    return translation.content_json if translation else page.content_json