from django.db import migrations, models
from django.utils import timezone


class Migration(migrations.Migration):

    dependencies = [
        ("pension", "0014_alter_reservation_rooms"),
    ]

    operations = [
        migrations.AddField(
            model_name="reservation",
            name="created_at",
            field=models.DateTimeField(auto_now_add=True, default=timezone.now),
            preserve_default=False,
        ),
    ]
