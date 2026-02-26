import json
import re
import unicodedata
from urllib.error import URLError, HTTPError
from urllib.request import Request, urlopen

from django.core.management.base import BaseCommand, CommandError

from pension.room.models import Room


DEFAULT_LIBRETRANSLATE_URL = "https://libretranslate.com/translate"


MANUAL_EN_TRANSLATIONS = {
    "jednoluzkovy": "Single room",
    "dvouluzkovy": "Double room",
    "triluzkovy": "Triple room",
    "ctyrluzkovy": "Quad room",
    "rodinny pokoj": "Family room",
    "apartman": "Apartment",
    "pokoj pro jednoho": "Room for one",
    "pokoj pro dva": "Room for two",
    "pokoj pro tri": "Room for three",
    "pokoj pro ctyri": "Room for four",
}


def normalize_text(value):
    if not value:
        return ""
    normalized = unicodedata.normalize("NFKD", value)
    ascii_only = normalized.encode("ascii", "ignore").decode("ascii")
    ascii_only = ascii_only.lower().strip()
    ascii_only = re.sub(r"\s+", " ", ascii_only)
    return ascii_only


def translate_with_libretranslate(text, source_lang, target_lang, url, api_key=None):
    payload = {
        "q": text,
        "source": source_lang,
        "target": target_lang,
        "format": "text",
    }
    if api_key:
        payload["api_key"] = api_key

    request = Request(
        url=url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urlopen(request, timeout=20) as response:
            body = response.read().decode("utf-8")
    except HTTPError as exc:
        raise CommandError(f"LibreTranslate HTTP error: {exc.code}") from exc
    except URLError as exc:
        raise CommandError(f"LibreTranslate connection error: {exc.reason}") from exc

    parsed = json.loads(body)
    translated = parsed.get("translatedText")
    if not translated:
        raise CommandError("LibreTranslate did not return translatedText")
    return translated


def translate_with_manual_map(text, target_lang):
    if target_lang != "en":
        return None

    normalized = normalize_text(text)
    if normalized in MANUAL_EN_TRANSLATIONS:
        return MANUAL_EN_TRANSLATIONS[normalized]

    if normalized.startswith("pokoj pro "):
        tail = normalized.replace("pokoj pro ", "", 1).strip()
        if tail in {"1", "jednoho", "jednu", "jednu osobu", "jednu osobu."}:
            return "Room for one"
        if tail in {"2", "dva", "dve", "dve osoby", "dve osoby."}:
            return "Room for two"
        if tail in {"3", "tri", "tri osoby", "tri osoby."}:
            return "Room for three"
        if tail in {"4", "ctyri", "ctyri osoby", "ctyri osoby."}:
            return "Room for four"

    return None


class Command(BaseCommand):
    help = "Translate room name/description into room JSON i18n fields."

    def add_arguments(self, parser):
        parser.add_argument("--source", default="cs", help="Source language code (default: cs)")
        parser.add_argument("--target", default="en", help="Target language code (default: en)")
        parser.add_argument(
            "--engine",
            choices=["manual", "libretranslate"],
            default="manual",
            help="Translation engine (default: manual).",
        )
        parser.add_argument(
            "--libretranslate-url",
            default=DEFAULT_LIBRETRANSLATE_URL,
            help=f"LibreTranslate endpoint (default: {DEFAULT_LIBRETRANSLATE_URL})",
        )
        parser.add_argument("--api-key", default=None, help="Optional LibreTranslate API key.")
        parser.add_argument("--overwrite", action="store_true", help="Overwrite existing translations.")
        parser.add_argument("--dry-run", action="store_true", help="Do not write changes to DB.")
        parser.add_argument(
            "--fallback-to-original",
            action="store_true",
            help="If translation fails, use original text as translation.",
        )

    def handle(self, *args, **options):
        source_lang = options["source"].strip().lower()
        target_lang = options["target"].strip().lower()
        engine = options["engine"]
        overwrite = options["overwrite"]
        dry_run = options["dry_run"]
        fallback_to_original = options["fallback_to_original"]
        libretranslate_url = options["libretranslate_url"]
        api_key = options["api_key"]

        translated_count = 0
        skipped_count = 0
        failed_count = 0

        rooms = Room.objects.all().order_by("id")
        for room in rooms:
            name_i18n = dict(room.name_i18n or {})
            description_i18n = dict(room.description_i18n or {})
            updated = False

            name_exists = bool(name_i18n.get(target_lang))
            description_exists = bool(description_i18n.get(target_lang))

            if not overwrite and name_exists and description_exists:
                skipped_count += 1
                continue

            def translate_text(value):
                if not value:
                    return ""
                if engine == "manual":
                    translated = translate_with_manual_map(value, target_lang=target_lang)
                else:
                    translated = translate_with_libretranslate(
                        value,
                        source_lang=source_lang,
                        target_lang=target_lang,
                        url=libretranslate_url,
                        api_key=api_key,
                    )

                if translated:
                    return translated
                if fallback_to_original:
                    return value
                return None

            if overwrite or not name_exists:
                translated_name = translate_text(room.name)
                if translated_name:
                    name_i18n[target_lang] = translated_name
                    updated = True
                else:
                    failed_count += 1

            if overwrite or not description_exists:
                translated_description = translate_text(room.description)
                if translated_description is not None:
                    description_i18n[target_lang] = translated_description
                    updated = True
                elif room.description:
                    failed_count += 1

            if updated:
                translated_count += 1
                if not dry_run:
                    room.name_i18n = name_i18n
                    room.description_i18n = description_i18n
                    room.save(update_fields=["name_i18n", "description_i18n"])

                self.stdout.write(
                    f"Room #{room.id}: "
                    f"name[{target_lang}]={name_i18n.get(target_lang)!r}, "
                    f"description[{target_lang}]={description_i18n.get(target_lang)!r}"
                )
            else:
                skipped_count += 1

        mode = "DRY RUN" if dry_run else "DONE"
        self.stdout.write(
            self.style.SUCCESS(
                f"{mode}: updated={translated_count}, skipped={skipped_count}, failed_fields={failed_count}"
            )
        )
