from django.core.management.base import BaseCommand, CommandError

from pension.reservation.bulk_import import BulkImportError, import_reservations


class Command(BaseCommand):
    help = (
        "Bulk import reservations from an .xlsx file. "
        "See docs/reservation_bulk_import.md for the expected column format."
    )

    def add_arguments(self, parser):
        parser.add_argument("file_path", help="Path to the .xlsx file to import.")
        parser.add_argument("--sheet", default=None, help="Sheet name to read (default: active sheet).")
        parser.add_argument("--dry-run", action="store_true", help="Validate only, write nothing to the database.")

    def handle(self, *args, **options):
        try:
            import openpyxl
        except ImportError as exc:
            raise CommandError(
                "openpyxl is required for this command. Install it with 'pip install openpyxl'."
            ) from exc

        file_path = options["file_path"]
        dry_run = options["dry_run"]

        try:
            workbook = openpyxl.load_workbook(file_path, data_only=True)
        except FileNotFoundError as exc:
            raise CommandError(f"File '{file_path}' does not exist.") from exc
        except Exception as exc:
            raise CommandError(f"Could not open '{file_path}': {exc}") from exc

        try:
            result = import_reservations(workbook, sheet_name=options["sheet"], dry_run=dry_run)
        except BulkImportError as exc:
            raise CommandError(str(exc)) from exc

        for row_error in result["row_errors"]:
            self.stdout.write(self.style.ERROR(f"Row {row_error['row']}: {row_error['message']}"))

        for skipped in result["skipped"]:
            for message in skipped["errors"]:
                self.stdout.write(self.style.ERROR(f"[{skipped['booking_reference']}] {message}"))

        for created in result["created"]:
            if dry_run:
                self.stdout.write(
                    self.style.SUCCESS(f"[{created['booking_reference']}] OK ({created['room_count']} room(s))")
                )
            else:
                self.stdout.write(
                    self.style.SUCCESS(f"[{created['booking_reference']}] Created reservation {created['number']}")
                )

        mode = "DRY RUN" if dry_run else "DONE"
        self.stdout.write(
            self.style.SUCCESS(
                f"{mode}: created={len(result['created'])}, skipped={len(result['skipped'])}, "
                f"row_errors={len(result['row_errors'])}"
            )
        )
