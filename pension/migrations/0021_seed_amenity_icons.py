from django.db import migrations

DEFAULTS = [
    {"key": "bed", "label": "Lůžka / kapacita", "order": 0},
    {"key": "bathroom", "label": "Koupelna", "order": 1},
    {"key": "wifi", "label": "Wi-Fi", "order": 2},
    {"key": "tv", "label": "Televize", "order": 3},
    {"key": "dog", "label": "Pes / mazlíčci", "order": 4},
]


def seed_amenity_icons(apps, schema_editor):
    AmenityIcon = apps.get_model('pension', 'AmenityIcon')
    for entry in DEFAULTS:
        AmenityIcon.objects.get_or_create(key=entry["key"], defaults=entry)


def remove_default_amenity_icons(apps, schema_editor):
    AmenityIcon = apps.get_model('pension', 'AmenityIcon')
    AmenityIcon.objects.filter(key__in=[entry["key"] for entry in DEFAULTS]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('pension', '0020_amenityicon'),
    ]

    operations = [
        migrations.RunPython(seed_amenity_icons, remove_default_amenity_icons),
    ]
