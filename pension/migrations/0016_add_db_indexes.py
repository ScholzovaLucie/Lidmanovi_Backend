from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("pension", "0015_reservation_created_at"),
    ]

    operations = [
        migrations.AlterField(
            model_name="reservation",
            name="check_in_date",
            field=models.DateField(db_index=True),
        ),
        migrations.AlterField(
            model_name="reservation",
            name="check_out_date",
            field=models.DateField(db_index=True),
        ),
        migrations.AlterField(
            model_name="reservation",
            name="status",
            field=models.CharField(
                choices=[
                    ("new", "New"),
                    ("confirmed", "Confirmed"),
                    ("cancelled", "Cancelled"),
                    ("payment_pending", "Payment pending"),
                    ("payed", "Payed"),
                    ("done", "Done"),
                ],
                db_index=True,
                default="new",
                max_length=20,
            ),
        ),
        migrations.AlterField(
            model_name="guest",
            name="email",
            field=models.EmailField(blank=True, db_index=True, max_length=254, null=True),
        ),
    ]
