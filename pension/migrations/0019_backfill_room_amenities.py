from django.db import migrations

DEFAULT_AMENITIES = [
    {"icon": "bed", "text": ""},
    {"icon": "bathroom", "text": "Koupelna"},
    {"icon": "wifi", "text": "Wi-Fi"},
]


def backfill_room_amenities(apps, schema_editor):
    Room = apps.get_model('pension', 'Room')
    Room.objects.update(amenities=DEFAULT_AMENITIES)


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('pension', '0018_room_amenities'),
    ]

    operations = [
        migrations.RunPython(backfill_room_amenities, noop_reverse),
    ]