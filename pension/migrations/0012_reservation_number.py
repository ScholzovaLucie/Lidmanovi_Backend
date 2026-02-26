from django.db import migrations, models


def populate_reservation_numbers(apps, schema_editor):
    Reservation = apps.get_model("pension", "Reservation")
    for reservation in Reservation.objects.filter(number__isnull=True).iterator():
        reservation.number = f"R-LEG-{str(reservation.pk)[-12:]}"
        reservation.save(update_fields=["number"])


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):
    dependencies = [
        ("pension", "0011_remove_reservation_check_reservation_dates"),
    ]

    operations = [
        migrations.AddField(
            model_name="reservation",
            name="number",
            field=models.CharField(blank=True, max_length=20, null=True, unique=True),
        ),
        migrations.RunPython(populate_reservation_numbers, noop_reverse),
        migrations.AlterField(
            model_name="reservation",
            name="number",
            field=models.CharField(max_length=20, unique=True),
        ),
    ]
