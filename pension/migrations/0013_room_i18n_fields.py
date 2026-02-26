from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pension', '0012_reservation_number'),
    ]

    operations = [
        migrations.AddField(
            model_name='room',
            name='description_i18n',
            field=models.JSONField(blank=True, default=dict),
        ),
        migrations.AddField(
            model_name='room',
            name='name_i18n',
            field=models.JSONField(blank=True, default=dict),
        ),
    ]
