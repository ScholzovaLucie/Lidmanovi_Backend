from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pension', '0026_voucherorder_status_and_shipping_address'),
    ]

    operations = [
        migrations.AddField(
            model_name='voucheramount',
            name='deleted_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
