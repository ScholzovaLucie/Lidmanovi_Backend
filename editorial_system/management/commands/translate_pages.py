from django.core.management.base import BaseCommand

from editorial_system.page.models import Page
from editorial_system.page.services import run_page_translation_job


class Command(BaseCommand):
    help = "Backfill translations for editorial pages into content_i18n."

    def add_arguments(self, parser):
        parser.add_argument(
            "--path",
            default=None,
            help="Optional exact page path filter (for example /kontakt).",
        )
        parser.add_argument(
            "--source-lang",
            default=None,
            help="Optional source lang filter (for example cs).",
        )
        parser.add_argument(
            "--target-langs",
            nargs="+",
            default=["en", "de", "pl"],
            help="Target language list (default: en de pl).",
        )
        parser.add_argument(
            "--overwrite",
            action="store_true",
            help="Overwrite existing auto-generated translations.",
        )

    def handle(self, *args, **options):
        path = options["path"]
        source_lang = options["source_lang"]
        target_langs = options["target_langs"]
        overwrite = options["overwrite"]

        queryset = Page.objects.all().order_by("id")
        if path:
            queryset = queryset.filter(path=path.strip())
        if source_lang:
            queryset = queryset.filter(lang=source_lang.strip().lower())

        processed = 0
        for page in queryset.iterator():
            run_page_translation_job(
                page=page,
                overwrite=overwrite,
                target_langs=target_langs,
            )
            processed += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Processed {processed} page(s). target_langs={target_langs}, overwrite={overwrite}"
            )
        )
