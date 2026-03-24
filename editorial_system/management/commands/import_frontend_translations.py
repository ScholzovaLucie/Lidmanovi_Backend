import json
import re
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from editorial_system.page.models import Page
from editorial_system.page.services import TRANSLATION_MANUALLY_REVIEWED


NAMESPACE_TO_PATHS = {
    "global": ["/global"],
    "home": ["/"],
    "kontakt": ["/kontakt"],
    "restaurace": ["/restaurace"],
    "galerie": ["/galerie"],
    "svatby": ["/svatby"],
    "ubytovani": ["/ubytovani"],
    # Keep both legacy and new route in sync.
    "balicky": ["/balicky", "/pobytove_balicky"],
    "cenik": ["/cenik"],
    "rezervace": ["/rezervace"],
}


FILE_MAPPINGS = [
    {"ns": "global", "file": "translations_global.js"},
    {"ns": "home", "file": "translations_index.js"},
    {"ns": "kontakt", "file": "translations_kontakt.js"},
    {"ns": "restaurace", "file": "translations_restaurace.js"},
    {"ns": "galerie", "file": "translations_galerie.js"},
    {"ns": "svatby", "file": "translations_svatby.js"},
    {"ns": "ubytovani", "file": "translations_ubytovani.js"},
    {"ns": "balicky", "file": "translations_balicky.js"},
    {"ns": "cenik", "file": "translation_cenik.js"},
    {"ns": "rezervace", "file": "translations_rezervace.js"},
]

SUPPORTED_LANGS = ["cs", "en", "de", "pl"]


def _extract_braced_object(source, start_index):
    depth = 0
    in_string = False
    string_quote = ""
    escaped = False
    end_index = None

    for i in range(start_index, len(source)):
        ch = source[i]

        if in_string:
            if escaped:
                escaped = False
            elif ch == "\\":
                escaped = True
            elif ch == string_quote:
                in_string = False
            continue

        if ch in ("'", '"'):
            in_string = True
            string_quote = ch
            continue

        if ch == "{":
            depth += 1
            continue

        if ch == "}":
            depth -= 1
            if depth == 0:
                end_index = i
                break

    if end_index is None:
        raise CommandError("Could not parse JS object literal.")
    return source[start_index : end_index + 1]


def _js_object_to_json(js_object_text):
    # Remove line comments only when outside string literals.
    out = []
    in_single = False
    in_double = False
    escaped = False
    i = 0
    while i < len(js_object_text):
        ch = js_object_text[i]
        nxt = js_object_text[i + 1] if i + 1 < len(js_object_text) else ""

        if escaped:
            out.append(ch)
            escaped = False
            i += 1
            continue

        if ch == "\\" and (in_single or in_double):
            out.append(ch)
            escaped = True
            i += 1
            continue

        if not in_double and ch == "'":
            in_single = not in_single
            out.append(ch)
            i += 1
            continue
        if not in_single and ch == '"':
            in_double = not in_double
            out.append(ch)
            i += 1
            continue

        if not in_single and not in_double and ch == "/" and nxt == "/":
            i += 2
            while i < len(js_object_text) and js_object_text[i] != "\n":
                i += 1
            continue

        out.append(ch)
        i += 1

    no_comments = "".join(out)
    quoted_keys = re.sub(
        r'([{\[,]\s*)([A-Za-z_][A-Za-z0-9_]*)\s*:',
        r'\1"\2":',
        no_comments,
    )

    # Convert JS single-quoted strings to JSON strings.
    def _single_to_json(match):
        value = match.group(1)
        value = value.replace("\\'", "'")
        return json.dumps(value, ensure_ascii=False)

    normalized_quotes = re.sub(
        r"'([^'\\]*(?:\\.[^'\\]*)*)'",
        _single_to_json,
        quoted_keys,
    )

    no_trailing_commas = re.sub(r",\s*([}\]])", r"\1", normalized_quotes)
    return no_trailing_commas


def _extract_exports(file_text):
    exports = {}
    for match in re.finditer(r"\bexport\s+const\s+([A-Za-z_][A-Za-z0-9_]*)\s*=", file_text):
        export_name = match.group(1)
        after_equal = match.end()
        tail = file_text[after_equal:]
        tail_stripped = tail.lstrip()
        if not tail_stripped.startswith("{"):
            continue
        first_brace = after_equal + (len(tail) - len(tail_stripped))
        object_text = _extract_braced_object(file_text, first_brace)
        json_text = _js_object_to_json(object_text)
        try:
            exports[export_name] = json.loads(json_text)
        except json.JSONDecodeError as exc:
            raise CommandError(
                f"Failed parsing export '{export_name}'. JSON error: {exc}"
            ) from exc
    return exports


def _pick_lang_map(exports):
    if all(lang in exports for lang in SUPPORTED_LANGS):
        return {lang: exports[lang] for lang in SUPPORTED_LANGS}

    for value in exports.values():
        if isinstance(value, dict) and all(lang in value for lang in SUPPORTED_LANGS):
            return {lang: value[lang] for lang in SUPPORTED_LANGS}

    return None


class Command(BaseCommand):
    help = "Import frontend locale JS files into editorial_system Page content_i18n."

    def add_arguments(self, parser):
        parser.add_argument(
            "--locales-dir",
            required=True,
            help="Absolute path to frontend locales directory.",
        )
        parser.add_argument(
            "--source-lang",
            default="cs",
            help="Source language code in CMS rows (default: cs).",
        )
        parser.add_argument(
            "--overwrite",
            action="store_true",
            help="Overwrite existing translations in content_i18n.",
        )
        parser.add_argument(
            "--if-empty",
            action="store_true",
            help="Run import only when there are no Page records yet.",
        )

    def handle(self, *args, **options):
        locales_dir = Path(options["locales_dir"]).expanduser().resolve()
        source_lang = str(options["source_lang"]).strip().lower()
        overwrite = bool(options["overwrite"])
        only_if_empty = bool(options["if_empty"])

        if only_if_empty and Page.objects.exists():
            self.stdout.write(
                self.style.WARNING("Skipping import because Page table is not empty.")
            )
            return

        if not locales_dir.exists() or not locales_dir.is_dir():
            raise CommandError(f"Invalid locales directory: {locales_dir}")

        namespaces = {}
        for mapping in FILE_MAPPINGS:
            file_path = locales_dir / mapping["file"]
            if not file_path.exists():
                raise CommandError(f"Missing locale file: {file_path}")
            file_text = file_path.read_text(encoding="utf-8")
            exports = _extract_exports(file_text)
            lang_map = _pick_lang_map(exports)
            if not lang_map:
                raise CommandError(f"Could not extract language map from {file_path.name}")
            namespaces[mapping["ns"]] = lang_map

        updated_pages = 0
        for namespace, lang_map in namespaces.items():
            paths = NAMESPACE_TO_PATHS.get(namespace)
            if not paths:
                continue

            source_content = lang_map.get(source_lang)
            if source_content is None:
                self.stdout.write(
                    self.style.WARNING(
                        f"Skipping namespace '{namespace}' (missing source lang '{source_lang}')."
                    )
                )
                continue

            for path in paths:
                page, _ = Page.objects.get_or_create(
                    path=path,
                    lang=source_lang,
                    defaults={"content_json": source_content},
                )

                content_i18n = dict(page.content_i18n or {})
                state_i18n = dict(page.translation_state_i18n or {})

                page.content_json = source_content
                content_i18n[source_lang] = source_content

                for lang, content in lang_map.items():
                    normalized_lang = str(lang).strip().lower()
                    if not overwrite and normalized_lang in content_i18n:
                        continue

                    content_i18n[normalized_lang] = content
                    if normalized_lang != source_lang:
                        state_i18n[normalized_lang] = {
                            "state": TRANSLATION_MANUALLY_REVIEWED,
                        }

                page.content_i18n = content_i18n
                page.translation_state_i18n = state_i18n
                page.save(
                    update_fields=["content_json", "content_i18n", "translation_state_i18n"]
                )
                updated_pages += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Imported frontend translations into {updated_pages} page(s). overwrite={overwrite}"
            )
        )
