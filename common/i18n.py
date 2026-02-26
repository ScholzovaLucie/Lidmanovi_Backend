def extract_requested_language(request, default_language="cs"):
    if request is None:
        return default_language

    query_language = request.query_params.get("lang")
    if query_language:
        return query_language.strip().lower()

    explicit_language = request.headers.get("X-Language")
    if explicit_language:
        return explicit_language.strip().lower()

    accept_language = request.headers.get("Accept-Language", "")
    if accept_language:
        first_language = accept_language.split(",")[0].split(";")[0].strip().lower()
        if first_language:
            return first_language

    return default_language


def resolve_translated_value(base_value, translations, language):
    if not isinstance(translations, dict) or not translations:
        return base_value

    normalized_language = (language or "").strip().lower()
    language_base = normalized_language.split("-")[0]

    if normalized_language in translations and translations[normalized_language]:
        return translations[normalized_language]

    if language_base in translations and translations[language_base]:
        return translations[language_base]

    for key, value in translations.items():
        if key.split("-")[0] == language_base and value:
            return value

    if base_value:
        return base_value

    for value in translations.values():
        if value:
            return value

    return base_value
