import datetime
from decimal import Decimal, InvalidOperation

from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction

from pension.reservation.enums import ReservationStatus
from pension.reservation.models import Reservation
from pension.reservation.serializers import ReservationCreateSerializer
from pension.room.models import Room


REQUIRED_COLUMNS = [
    "booking_reference",
    "check_in_date",
    "check_out_date",
    "room_name",
    "room_num_adults",
    "guest_first_name",
    "guest_last_name",
]

OPTIONAL_COLUMNS = [
    "room_num_children",
    "guest_email",
    "guest_phone",
    "guest_country",
    "guest_note",
    "status",
    "currency",
    "note",
    "number",
    "price",
]

ALL_COLUMNS = REQUIRED_COLUMNS + OPTIONAL_COLUMNS

REQUIRED_SHARED_FIELDS = ["check_in_date", "check_out_date", "guest_first_name", "guest_last_name"]
OPTIONAL_SHARED_FIELDS = [
    "guest_email", "guest_phone", "guest_country", "guest_note",
    "status", "currency", "note", "number",
]
SHARED_FIELDS = REQUIRED_SHARED_FIELDS + OPTIONAL_SHARED_FIELDS

VALID_STATUSES = {value for value, _ in ReservationStatus.choices}


class BulkImportError(Exception):
    """Raised for file-level problems (bad format, missing columns) that abort the whole import."""


def parse_date(value):
    if value in (None, ""):
        return None
    if isinstance(value, datetime.datetime):
        return value.date()
    if isinstance(value, datetime.date):
        return value
    if isinstance(value, str):
        text = value.strip()
        for fmt in ("%Y-%m-%d", "%d.%m.%Y"):
            try:
                return datetime.datetime.strptime(text, fmt).date()
            except ValueError:
                continue
    return None


def parse_int(value):
    if value in (None, "") or isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return int(value)
    if isinstance(value, str):
        try:
            return int(value.strip())
        except ValueError:
            return None
    return None


def parse_decimal(value):
    if value in (None, ""):
        return None
    try:
        return Decimal(str(value).strip().replace(",", "."))
    except InvalidOperation:
        return None


def clean_str(value):
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _load_rows(workbook, sheet_name):
    if sheet_name:
        if sheet_name not in workbook.sheetnames:
            raise BulkImportError(f"Sheet '{sheet_name}' not found. Available sheets: {workbook.sheetnames}")
        sheet = workbook[sheet_name]
    else:
        sheet = workbook.active

    rows = list(sheet.iter_rows(values_only=True))
    if not rows:
        raise BulkImportError("The sheet is empty.")
    return rows


def _build_column_index(header_row):
    column_index = {}
    for idx, cell in enumerate(header_row):
        if cell is None:
            continue
        key = str(cell).strip()
        if key in ALL_COLUMNS:
            column_index[key] = idx

    missing_required = [col for col in REQUIRED_COLUMNS if col not in column_index]
    if missing_required:
        raise BulkImportError(f"Missing required columns: {', '.join(missing_required)}")
    return column_index


def _parse_rows_into_groups(rows, column_index):
    def get_cell(row, key):
        idx = column_index.get(key)
        if idx is None or idx >= len(row):
            return None
        return row[idx]

    groups = {}
    row_errors = []

    for row_number, row in enumerate(rows[1:], start=2):
        if row is None or all(cell in (None, "") for cell in row):
            continue

        booking_reference = clean_str(get_cell(row, "booking_reference"))
        if not booking_reference:
            row_errors.append({"row": row_number, "message": "booking_reference is required."})
            continue

        parsed = {
            "check_in_date": parse_date(get_cell(row, "check_in_date")),
            "check_out_date": parse_date(get_cell(row, "check_out_date")),
            "room_name": clean_str(get_cell(row, "room_name")),
            "room_num_adults": parse_int(get_cell(row, "room_num_adults")),
            "room_num_children": parse_int(get_cell(row, "room_num_children")) or 0,
            "guest_first_name": clean_str(get_cell(row, "guest_first_name")),
            "guest_last_name": clean_str(get_cell(row, "guest_last_name")),
            "guest_email": clean_str(get_cell(row, "guest_email")),
            "guest_phone": clean_str(get_cell(row, "guest_phone")),
            "guest_country": clean_str(get_cell(row, "guest_country")),
            "guest_note": clean_str(get_cell(row, "guest_note")),
            "status": (clean_str(get_cell(row, "status")) or "").lower() or None,
            "currency": clean_str(get_cell(row, "currency")),
            "note": clean_str(get_cell(row, "note")),
            "number": clean_str(get_cell(row, "number")),
            "price": parse_decimal(get_cell(row, "price")),
        }
        groups.setdefault(booking_reference, []).append((row_number, parsed))

    return groups, row_errors


def _resolve_shared_values(entries):
    shared_values = {}
    errors = []

    for field in SHARED_FIELDS:
        value = None
        source_row = None
        for row_number, parsed in entries:
            candidate = parsed[field]
            if candidate is None:
                continue
            if value is None:
                value = candidate
                source_row = row_number
            elif candidate != value:
                errors.append(
                    f"Field '{field}' differs between rows "
                    f"(row {source_row}: {value!r} vs row {row_number}: {candidate!r})."
                )
                break
        shared_values[field] = value

    for field in REQUIRED_SHARED_FIELDS:
        if shared_values.get(field) is None:
            errors.append(f"'{field}' is required.")

    return shared_values, errors


def _build_rooms_payload(entries):
    rooms_payload = []
    errors = []

    for row_number, parsed in entries:
        room_name = parsed["room_name"]
        if not room_name:
            errors.append(f"Row {row_number}: room_name is required.")
            continue

        room = Room.objects.filter(name=room_name, is_active=True).first()
        if room is None:
            errors.append(f"Row {row_number}: room '{room_name}' does not exist or is not active.")
            continue

        num_adults = parsed["room_num_adults"]
        if not num_adults or num_adults < 1:
            errors.append(f"Row {row_number}: room_num_adults must be a positive integer.")
            continue

        rooms_payload.append({
            "id": room.id,
            "num_adults": num_adults,
            "num_children": parsed["room_num_children"] or 0,
        })

    if not rooms_payload and not errors:
        errors.append("No valid rooms found for this booking_reference.")

    return rooms_payload, errors


def _process_group(booking_reference, entries, explicit_numbers_seen, dry_run):
    shared_values, errors = _resolve_shared_values(entries)

    status_value = shared_values.get("status") or ReservationStatus.NEW
    if status_value not in VALID_STATUSES:
        errors.append(f"Invalid status '{status_value}'. Allowed values: {', '.join(sorted(VALID_STATUSES))}.")

    number_value = shared_values.get("number")
    if number_value:
        existing_ref = explicit_numbers_seen.get(number_value)
        if existing_ref and existing_ref != booking_reference:
            errors.append(
                f"Reservation number '{number_value}' is also used by "
                f"booking_reference '{existing_ref}' in this file."
            )
        else:
            explicit_numbers_seen[number_value] = booking_reference
        if Reservation.objects.filter(number=number_value).exists():
            errors.append(f"Reservation number '{number_value}' already exists in the database.")

    price_values = [parsed["price"] for _, parsed in entries if parsed["price"] is not None]
    price_value = price_values[0] if price_values else None

    rooms_payload, room_errors = _build_rooms_payload(entries)
    errors.extend(room_errors)

    if errors:
        return {"booking_reference": booking_reference, "errors": errors}, None

    payload = {
        "check_in_date": shared_values["check_in_date"],
        "check_out_date": shared_values["check_out_date"],
        "note": shared_values.get("note") or "",
        "currency": shared_values.get("currency") or "CZK",
        "primary_guest": {
            "first_name": shared_values["guest_first_name"],
            "last_name": shared_values["guest_last_name"],
            "email": shared_values.get("guest_email"),
            "phone": shared_values.get("guest_phone") or "",
            "country": shared_values.get("guest_country") or "",
            "note": shared_values.get("guest_note") or "",
        },
        "rooms": rooms_payload,
    }

    serializer = ReservationCreateSerializer(data=payload)
    if not serializer.is_valid():
        return {"booking_reference": booking_reference, "errors": [str(serializer.errors)]}, None

    preview = Reservation(
        check_in_date=payload["check_in_date"],
        check_out_date=payload["check_out_date"],
        num_adults=sum(r["num_adults"] for r in rooms_payload),
        num_children=sum(r["num_children"] for r in rooms_payload),
    )
    try:
        preview.validate_rooms([dict(r) for r in rooms_payload])
    except DjangoValidationError as exc:
        return {"booking_reference": booking_reference, "errors": exc.messages}, None

    if dry_run:
        return None, {"booking_reference": booking_reference, "number": None, "room_count": len(rooms_payload)}

    try:
        with transaction.atomic():
            reservation = serializer.save()
            update_fields = []
            if status_value != reservation.status:
                reservation.status = status_value
                update_fields.append("status")
            if number_value:
                reservation.number = number_value
                update_fields.append("number")
            if price_value is not None:
                reservation.price = price_value
                update_fields.append("price")
            if update_fields:
                reservation.save(update_fields=update_fields)
    except Exception as exc:  # noqa: BLE001 - surfaced to the caller as a skipped group
        return {"booking_reference": booking_reference, "errors": [f"Failed to save: {exc}"]}, None

    return None, {"booking_reference": booking_reference, "number": reservation.number, "room_count": len(rooms_payload)}


def import_reservations(workbook, sheet_name=None, dry_run=False):
    """
    workbook: an already-loaded openpyxl Workbook.
    Returns a JSON-serializable summary dict:
        {
            "dry_run": bool,
            "created": [{"booking_reference", "number", "room_count"}],
            "skipped": [{"booking_reference", "errors": [...]}],
            "row_errors": [{"row", "message"}],
        }
    Raises BulkImportError for file-level problems (missing columns, empty sheet).
    """
    rows = _load_rows(workbook, sheet_name)
    column_index = _build_column_index(rows[0])
    groups, row_errors = _parse_rows_into_groups(rows, column_index)

    if not groups and not row_errors:
        raise BulkImportError("No usable rows found in the file.")

    created = []
    skipped = []
    explicit_numbers_seen = {}

    for booking_reference, entries in groups.items():
        skip_result, create_result = _process_group(booking_reference, entries, explicit_numbers_seen, dry_run)
        if skip_result is not None:
            skipped.append(skip_result)
        if create_result is not None:
            created.append(create_result)

    return {
        "dry_run": dry_run,
        "created": created,
        "skipped": skipped,
        "row_errors": row_errors,
    }
