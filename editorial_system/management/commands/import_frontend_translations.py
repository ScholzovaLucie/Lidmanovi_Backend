import ast
import copy
import re
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings

from editorial_system.page.models import Page, PageTranslation
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
    "translation_cenik.js": "/cenik",
    "translations_pokoje.js": "/pokoje",
    "translations_gdpr.js": "/gdpr",
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


def merge_missing_keys(existing, incoming):
    """Add missing object keys without changing existing editorial content."""
    merged = copy.deepcopy(existing)
    changed = False

    for key, value in incoming.items():
        if key not in merged:
            merged[key] = copy.deepcopy(value)
            changed = True
        elif isinstance(merged[key], dict) and isinstance(value, dict):
            nested, nested_changed = merge_missing_keys(merged[key], value)
            if nested_changed:
                merged[key] = nested
                changed = True

    return merged, changed


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
            "--merge-missing",
            action="store_true",
            help="Add missing object keys without overwriting existing content.",
        )
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
        merge_missing = options["merge_missing"]
        should_overwrite = overwrite and not if_empty

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
                defaults={"content_json": {}},
            )
            if created:
                created_count += 1

            page_changed = False
            source_payload = translations[source_lang]
            source_has_content = bool(page.content_json)

            if created or not source_has_content or should_overwrite:
                if page.content_json != source_payload:
                    page.content_json = source_payload
                    page.save(update_fields=["content_json"])
                    page_changed = True
            elif merge_missing:
                merged_payload, changed = merge_missing_keys(page.content_json, source_payload)
                if changed:
                    page.content_json = merged_payload
                    page.save(update_fields=["content_json"])
                    page_changed = True
            else:
                skipped_count += 1

            for lang, payload in translations.items():
                normalized_lang = lang.strip().lower()
                if normalized_lang == source_lang:
                    continue

                existing = PageTranslation.objects.filter(page=page, lang=normalized_lang).first()
                has_existing = existing is not None and bool(existing.content_json)
                is_manually_reviewed = existing is not None and existing.state == TRANSLATION_MANUALLY_REVIEWED

                if is_manually_reviewed and not should_overwrite:
                    skipped_count += 1
                    continue

                if not has_existing or should_overwrite:
                    if existing:
                        if existing.content_json != payload:
                            existing.content_json = payload
                            existing.save(update_fields=["content_json"])
                            page_changed = True
                    else:
                        PageTranslation.objects.create(page=page, lang=normalized_lang, content_json=payload)
                        page_changed = True
                elif merge_missing:
                    merged_payload, changed = merge_missing_keys(existing.content_json, payload)
                    if changed:
                        existing.content_json = merged_payload
                        existing.save(update_fields=["content_json"])
                        page_changed = True
                else:
                    skipped_count += 1

            if page_changed:
                updated_count += 1
                self.stdout.write(self.style.SUCCESS(f"Imported {file_path.name} -> {path}"))

        self.stdout.write(
            self.style.SUCCESS(
                f"DONE: created={created_count}, updated={updated_count}, skipped={skipped_count}"
            )
        )
