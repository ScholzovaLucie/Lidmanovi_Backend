from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from editorial_system.photo.models import Photo


DEFAULT_MEDIA_PHOTOS_DIR = Path(settings.MEDIA_ROOT) / "editorial" / "photos"
SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif", ".svg"}


class Command(BaseCommand):
    help = "Create missing editorial photo records from files already present in MEDIA_ROOT."

    def add_arguments(self, parser):
        parser.add_argument(
            "--photos-dir",
            default=str(DEFAULT_MEDIA_PHOTOS_DIR),
            help=f"Directory with stored photos (default: {DEFAULT_MEDIA_PHOTOS_DIR})",
        )
        parser.add_argument(
            "--if-empty",
            action="store_true",
            help="Run only when there are no photo records in the database yet.",
        )

    def handle(self, *args, **options):
        photos_dir = Path(options["photos_dir"]).expanduser()
        if_empty = options["if_empty"]

        if if_empty and Photo.objects.exists():
            self.stdout.write(self.style.WARNING("Photo table is not empty. Skipping sync."))
            return

        if not photos_dir.exists():
            self.stdout.write(self.style.WARNING(f"Photos directory '{photos_dir}' does not exist. Skipping sync."))
            return

        if not photos_dir.is_dir():
            raise CommandError(f"Photos path '{photos_dir}' is not a directory.")

        media_root = Path(settings.MEDIA_ROOT).expanduser().resolve()
        try:
            photos_dir.resolve().relative_to(media_root)
        except ValueError as exc:
            raise CommandError("Photos directory must be inside MEDIA_ROOT.") from exc

        created_count = 0
        updated_count = 0
        skipped_count = 0

        for file_path in sorted(photos_dir.rglob("*")):
            if not file_path.is_file():
                continue
            if file_path.suffix.lower() not in SUPPORTED_EXTENSIONS:
                skipped_count += 1
                continue

            relative_path = file_path.resolve().relative_to(media_root).as_posix()
            category = file_path.parent.name.strip().lower() or "uncategorized"

            photo, created = Photo.objects.get_or_create(
                image=relative_path,
                defaults={"category": category},
            )

            if created:
                created_count += 1
                continue

            if photo.category != category:
                photo.category = category
                photo.save(update_fields=["category"])
                updated_count += 1
            else:
                skipped_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"DONE: created={created_count}, updated={updated_count}, skipped={skipped_count}"
            )
        )
