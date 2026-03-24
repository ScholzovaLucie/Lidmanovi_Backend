import ast
import re
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings

from editorial_system.page.models import Page
from editorial_system.page.services import TRANSLATION_MANUALLY_REVIEWED


DEFAULT_LOCALES_DIR = str(Path(settings.BASE_DIR) / "tmp" / "locales")
FILE_TO_PATH = {
    "translations_index.js": "/",
    "translations_global.js": "/global",
    "translations_kontakt.js": "/kontakt",
    "translations_restaurace.js": "/restaurace",
    "translations_ubytovani.js": "/ubytovani",
    "translations_svatby.js": "/svatby",
    "translations_balicky.js": "/balicky",
    "translations_rezervace.js": "/rezervace",
    "translations_galerie.js": "/galerie",
}


def strip_js_comments(value):
    return re.sub(r"//.*$", "", value, flags=re.MULTILINE)


def to_python_literal(value):
    without_comments = strip_js_comments(value)
    quoted_keys = re.sub(
        r'([{\[,]\s*)([A-Za-z_][A-Za-z0-9_]*)(\s*:)',
        r'\1"\2"\3',
        without_comments,
    )
    normalized = quoted_keys.replace("true", "True").replace("false", "False").replace("null", "None")
    normalized = re.sub(r",(\s*[}\]])", r"\1", normalized)
    return normalized


def parse_translations_file(file_path):
    content = Path(file_path).read_text(encoding="utf-8")

    object_match = re.search(
        r"export\s+const\s+(translations_[A-Za-z0-9_]+)\s*=\s*({.*?})\s*;",
        content,
        flags=re.DOTALL,
    )
    if object_match:
        return ast.literal_eval(to_python_literal(object_match.group(2)))

    assignments = re.findall(
        r"export\s+const\s+([A-Za-z_][A-Za-z0-9_]*)\s*=\s*({.*?})\s*;",
        content,
        flags=re.DOTALL,
    )
    parsed = {}
    for name, payload in assignments:
        if re.fullmatch(r"[a-z]{2}(?:-[A-Za-z]{2})?", name):
            parsed[name.lower()] = ast.literal_eval(to_python_literal(payload))
    if parsed:
        return parsed

    raise CommandError(f"Could not parse translations from '{file_path}'.")


class Command(BaseCommand):
    help = "Import frontend locale files into editorial page content."

    def add_arguments(self, parser):
        parser.add_argument(
            "--locales-dir",
            default=DEFAULT_LOCALES_DIR,
            help=f"Directory containing translations_*.js files (default: {DEFAULT_LOCALES_DIR})",
        )
        parser.add_argument("--source-lang", default="cs", help="Source language stored in Page.lang (default: cs)")
        parser.add_argument("--overwrite", action="store_true", help="Overwrite already populated content.")
        parser.add_argument(
            "--if-empty",
            action="store_true",
            help="Only fill empty fields. Takes precedence over overwrite for existing content.",
        )

    def handle(self, *args, **options):
        locales_dir = Path(options["locales_dir"]).expanduser()
        source_lang = options["source_lang"].strip().lower()
        overwrite = options["overwrite"]
        if_empty = options["if_empty"]

        if not locales_dir.exists():
            raise CommandError(f"Locales directory '{locales_dir}' does not exist.")
        if not locales_dir.is_dir():
            raise CommandError(f"Locales path '{locales_dir}' is not a directory.")

        created_count = 0
        updated_count = 0
        skipped_count = 0

        for filename, path in FILE_TO_PATH.items():
            file_path = locales_dir / filename
            if not file_path.exists():
                self.stdout.write(self.style.WARNING(f"Skipping missing file: {file_path}"))
                continue

            translations = parse_translations_file(file_path)
            if source_lang not in translations:
                raise CommandError(f"Source language '{source_lang}' not found in '{file_path.name}'.")

            page, created = Page.objects.get_or_create(
                path=path,
                lang=source_lang,
                defaults={"content_json": {}, "content_i18n": {}, "translation_state_i18n": {}},
            )
            if created:
                created_count += 1

            content_i18n = dict(page.content_i18n or {})
            translation_state_i18n = dict(page.translation_state_i18n or {})
            page_changed = False

            source_payload = translations[source_lang]
            source_has_content = bool(page.content_json)
            if created or (not source_has_content) or (overwrite and not if_empty):
                if page.content_json != source_payload:
                    page.content_json = source_payload
                    page_changed = True
            else:
                skipped_count += 1

            for lang, payload in translations.items():
                normalized_lang = lang.strip().lower()
                if normalized_lang == source_lang:
                    continue

                existing_payload = content_i18n.get(normalized_lang)
                existing_state = translation_state_i18n.get(normalized_lang, {}).get("state")
                has_existing_payload = bool(existing_payload)
                should_fill_empty = not has_existing_payload
                should_overwrite = overwrite and not if_empty

                if existing_state == TRANSLATION_MANUALLY_REVIEWED and not should_overwrite:
                    skipped_count += 1
                    continue

                if should_fill_empty or should_overwrite:
                    if existing_payload != payload:
                        content_i18n[normalized_lang] = payload
                        page_changed = True
                else:
                    skipped_count += 1

            if page_changed:
                page.content_i18n = content_i18n
                page.translation_state_i18n = translation_state_i18n
                update_fields = ["content_json", "content_i18n", "translation_state_i18n"]
                page.save(update_fields=update_fields)
                updated_count += 1
                self.stdout.write(self.style.SUCCESS(f"Imported {file_path.name} -> {path}"))
            elif created:
                page.save(update_fields=["content_json", "content_i18n", "translation_state_i18n"])

        self.stdout.write(
            self.style.SUCCESS(
                f"DONE: created={created_count}, updated={updated_count}, skipped={skipped_count}"
            )
        )
