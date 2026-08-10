# Hromadný import rezervací z Excelu

Návrh formátu `.xlsx` souboru pro hromadné nahrání rezervací (např. migrace historických dat, import z jiného rezervačního systému, hromadné zadání skupinové akce).

## Princip: jeden řádek = jeden pokoj v rezervaci

`Reservation` může mít víc pokojů najednou (`rooms` je M2M, `pension/reservation/models.py:55-59`) a API pro vytváření rezervací (`ReservationCreateSerializer`) očekává u každého pokoje vlastní počet dospělých/dětí (`pension/reservation/serializers.py:56-78`), protože kapacita se kontroluje per-pokoj (`Room.can_fit`, `pension/room/models.py:21-28`).

Aby šlo v Excelu zadat i vícepokojovou rezervaci bez nepřehledného slučování hodnot do jedné buňky, používá se sloupec **`booking_reference`**: řádky se stejnou hodnotou `booking_reference` tvoří dohromady jednu rezervaci (jeden řádek na pokoj). Nejběžnější případ — rezervace na jeden pokoj — je pak prostě skupina o jednom řádku.

## Struktura sloupců

List (sheet) `Rezervace`, první řádek = hlavičky přesně dle názvů níže (anglicky, `snake_case`, bez diakritiky — kvůli mapování na import skript).

| Sloupec | Povinné | Formát / hodnoty | Co tam má být |
|---|---|---|---|
| `booking_reference` | Ano | libovolný text, unikátní v rámci souboru | Spojovací klíč řádků patřících k jedné rezervaci, např. `BK001`. U jednopokojové rezervace stačí unikátní hodnota jen pro ten řádek. |
| `check_in_date` | Ano | `YYYY-MM-DD` (přijímá se i `DD.MM.YYYY`) | Datum příjezdu. Musí být **stejné na všech řádcích** se stejným `booking_reference`. |
| `check_out_date` | Ano | `YYYY-MM-DD` (přijímá se i `DD.MM.YYYY`) | Datum odjezdu, musí být pozdější než `check_in_date`. Stejné pravidlo shody napříč skupinou. |
| `room_name` | Ano | přesný text | Musí přesně odpovídat existujícímu a aktivnímu `Room.name` v databázi (`pension/room/models.py:7`, `is_active=True`). Doporučuji přiložit vedle šablony i aktuální seznam názvů pokojů z DB, ať se lidé nepřeklepnou. |
| `room_num_adults` | Ano | celé číslo ≥ 1 | Počet dospělých v **tomto konkrétním pokoji**. Musí se vejít do `Room.max_adults` a celkové `Room.capacity`. |
| `room_num_children` | Ne (default `0`) | celé číslo ≥ 0 | Počet dětí v tomto pokoji, musí se vejít do `Room.max_children`. |
| `guest_first_name` | Ano | text | Jméno hlavního hosta. Stačí vyplnit na prvním řádku skupiny, ale doporučeno vyplnit na všech řádcích stejně (kontrola shody). |
| `guest_last_name` | Ano | text | Příjmení hlavního hosta. |
| `guest_email` | Ne | e-mail | Spolu se jménem/příjmením slouží k dohledání existujícího hosta (`Guest.objects.filter(first_name, last_name, email)`, stejná logika jako API); pokud host neexistuje, vytvoří se nový. |
| `guest_phone` | Ne | text | Telefon hosta. |
| `guest_country` | Ne | text | Země hosta. |
| `guest_note` | Ne | text | Poznámka u hosta (`Guest.note`), ne u rezervace. |
| `status` | Ne (default `new`) | jedna z hodnot: `new`, `confirmed`, `cancelled`, `payment_pending`, `payed`, `done` | Stav rezervace, viz `ReservationStatus` (`pension/reservation/enums.py`). Pozor: `cancelled`/`done` se nezapočítávají do kontroly překryvu termínů pokoje. |
| `currency` | Ne (default `CZK`) | text, např. `CZK`, `EUR` | Měna ceny. |
| `note` | Ne | text | Poznámka k celé rezervaci (`Reservation.note`), ne k hostovi. Vyplnit stačí jednou ve skupině. |
| `number` | Ne | text, unikátní | Číslo rezervace. Pokud necháte prázdné, vygeneruje se automaticky ve formátu `R-YYYYMMDD-NNNNNN` (`Reservation._generate_number`, `pension/reservation/models.py:63-72`). Pokud vyplníte, musí být v celé DB unikátní. |
| `price` | Ne | číslo | Celková cena za pobyt. Pokud necháte prázdné, dopočítá se automaticky z ceníku pokojů (`price_for_adult`/`price_for_children`) a počtu nocí (`Reservation.calculate_price`, `pension/reservation/models.py:127-145`). |

## Validace při importu (odpovídá logice `ReservationCreateSerializer`/`Reservation.validate_rooms`)

- `check_out_date` musí být později než `check_in_date`.
- V rámci jedné `booking_reference` skupiny nesmí být dvakrát stejný `room_name`.
- Součet kapacit vybraných pokojů musí pokrýt celkový počet osob v rezervaci.
- Pro každý pokoj se kontroluje překryv s existujícími rezervacemi ve stavu `new`/`confirmed`/`payment_pending`/`payed` na stejné datumy — pokud koliduje, řádek/skupina se odmítne.
- `room_name` musí existovat a být `is_active=True`.
- Pole, která mají být shodná napříč skupinou (`check_in_date`, `check_out_date`, `guest_*`, `status`, `currency`, `note`, `number`), se kontrolují na shodu — při rozporu se celá skupina odmítne s chybou (ne tichým přepsáním).

## Chování při chybách

Doporučený přístup (stejný vzor jako existující importní management commandy, např. `editorial_system/management/commands/import_frontend_translations.py` a `pension/management/commands/translate_rooms.py`):

1. **`--dry-run` režim** — projede celý soubor, nic neuloží, vypíše seznam chyb po řádcích/skupinách (číslo řádku v Excelu, `booking_reference`, popis chyby).
2. **Ostrý import** — buď běží transakčně přes celý soubor (jedna chyba = nic se neuloží), nebo po skupinách (jedna vadná rezervace se přeskočí, zbytek se naimportuje) — s výstupním reportem, kolik rezervací se vytvořilo a které řádky selhaly a proč.

## Ukázková data

| booking_reference | check_in_date | check_out_date | room_name | room_num_adults | room_num_children | guest_first_name | guest_last_name | guest_email | status | note |
|---|---|---|---|---|---|---|---|---|---|---|
| BK001 | 2026-09-10 | 2026-09-13 | Pokoj 1 | 2 | 0 | Jana | Nováková | jana@example.com | confirmed | Příjezd večer |
| BK002 | 2026-09-15 | 2026-09-18 | Pokoj 3 | 2 | 1 | Petr | Svoboda | | new | |
| BK002 | 2026-09-15 | 2026-09-18 | Pokoj 4 | 2 | 0 | Petr | Svoboda | | new | |

(`BK002` je jedna rezervace na dva pokoje — oba řádky mají stejné datumy, hosta i poznámku.)

## Implementace

Sdílená parsovací/validační logika je v `pension/reservation/bulk_import.py` (funkce `import_reservations`) — používá ji jak API endpoint, tak management command, takže se pravidla nikde neduplikují a chovají se stejně.

### API endpoint (pro frontend)

`POST /pension/admin/reservations/bulk-import/` — vyžaduje staff/admin přihlášení (`IsAdminUser`, stejně jako zbytek `PrivateReservationViewSet`, `pension/reservation/views.py`).

Request: `multipart/form-data`

| Pole | Povinné | Popis |
|---|---|---|
| `file` | Ano | `.xlsx` soubor dle formátu výše. |
| `sheet` | Ne | Název listu, pokud není v aktivním (prvním) listu. |
| `dry_run` | Ne | `true`/`1` — jen zvaliduje, nic neuloží. |

Response `200 OK`:

```json
{
  "dry_run": false,
  "created": [
    {"booking_reference": "BK001", "number": "R-20260910-123456", "room_count": 1}
  ],
  "skipped": [
    {"booking_reference": "BK002", "errors": ["Row 5: room 'Pokoj 9' does not exist or is not active."]}
  ],
  "row_errors": [
    {"row": 8, "message": "booking_reference is required."}
  ]
}
```

Response `400 Bad Request` — chybí soubor, soubor nejde přečíst, nebo v hlavičce chybí povinný sloupec (`{"file": ["Missing required columns: room_name"]}`).

Import zpracovává jednotlivé `booking_reference` skupiny nezávisle (vlastní DB transakce na skupinu) — jedna vadná rezervace se přeskočí a zapíše do `skipped`, zbytek souboru se naimportuje normálně.

### Management command (pro server/migraci dat)

```bash
python manage.py import_reservations soubor.xlsx [--dry-run] [--sheet "Rezervace"]
```

Vypisuje řádkové/skupinové chyby a na konci souhrn `created=X, skipped=Y, row_errors=Z`.

### Závislost

Parsování `.xlsx` zajišťuje `openpyxl` (přidáno do `requirements.txt`).
