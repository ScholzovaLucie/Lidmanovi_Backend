import json
import os
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from django.utils import timezone


SUPPORTED_PAGE_LANGUAGES = ("cs", "en", "de", "pl")
TRANSLATION_AUTO_GENERATED = "auto_generated"
TRANSLATION_MANUALLY_REVIEWED = "manually_reviewed"


def _translate_text_with_libretranslate(text, source_lang, target_lang):
    url = os.environ.get("LIBRETRANSLATE_URL")
    if not url:
        return None

    payload = {
        "q": text,
        "source": source_lang,
        "target": target_lang,
        "format": "text",
    }
    api_key = os.environ.get("LIBRETRANSLATE_API_KEY")
    if api_key:
        payload["api_key"] = api_key

    request = Request(
        url=url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urlopen(request, timeout=15) as response:
            body = response.read().decode("utf-8")
        parsed = json.loads(body)
        translated = parsed.get("translatedText")
        if isinstance(translated, str) and translated.strip():
            return translated
    except (HTTPError, URLError, TimeoutError, json.JSONDecodeError):
        return None

    return None


def _translate_text(text, source_lang, target_lang):
    translated = _translate_text_with_libretranslate(
        text=text,
        source_lang=source_lang,
        target_lang=target_lang,
    )
    if translated is not None:
        return translated

    # Dev fallback/seed mode when translation engine is not configured.
    return text


def _translate_json_value(value, source_lang, target_lang):
    if isinstance(value, str):
        return _translate_text(value, source_lang=source_lang, target_lang=target_lang)
    if isinstance(value, list):
        return [
            _translate_json_value(item, source_lang=source_lang, target_lang=target_lang)
            for item in value
        ]
    if isinstance(value, dict):
        return {
            key: _translate_json_value(item, source_lang=source_lang, target_lang=target_lang)
            for key, item in value.items()
        }
    return value


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


def run_page_translation_job(page, overwrite=False, target_langs=None):
    source_lang = (page.lang or "cs").strip().lower()
    source_content = page.content_json
    if source_content is None:
        return

    normalized_targets = target_langs or SUPPORTED_PAGE_LANGUAGES
    normalized_targets = [lang.strip().lower() for lang in normalized_targets if lang]

    translations = dict(page.content_i18n or {})
    states = dict(page.translation_state_i18n or {})
    updated = False

    if translations.get(source_lang) != source_content:
        translations[source_lang] = source_content
        updated = True

    for target_lang in normalized_targets:
        if target_lang == source_lang:
            continue

        existing_state = states.get(target_lang, {})
        existing_state_name = existing_state.get("state")
        if not overwrite and existing_state_name == TRANSLATION_MANUALLY_REVIEWED:
            continue

        if not overwrite and target_lang in translations and existing_state_name:
            continue

        translated_content = _translate_json_value(
            source_content,
            source_lang=source_lang,
            target_lang=target_lang,
        )
        translations[target_lang] = translated_content
        states[target_lang] = {
            "state": TRANSLATION_AUTO_GENERATED,
            "updated_at": timezone.now().isoformat(),
        }
        updated = True

    if updated:
        page.content_i18n = translations
        page.translation_state_i18n = states
        page.save(update_fields=["content_i18n", "translation_state_i18n"])
