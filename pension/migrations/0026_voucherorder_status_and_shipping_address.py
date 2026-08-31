from django.db import migrations, models

from pension.voucher.enums import VoucherStatus


def forwards_backfill_status(apps, schema_editor):
    VoucherOrder = apps.get_model('pension', 'VoucherOrder')
    VoucherOrder.objects.filter(is_sent=True).update(status=VoucherStatus.SENT)


def backwards_backfill_is_sent(apps, schema_editor):
    VoucherOrder = apps.get_model('pension', 'VoucherOrder')
    VoucherOrder.objects.filter(status=VoucherStatus.SENT).update(is_sent=True)


class Migration(migrations.Migration):

    dependencies = [
        ('pension', '0025_nearbyplace'),
    ]

    operations = [
        migrations.AddField(
            model_name='voucherorder',
            name='status',
            field=models.CharField(
                choices=[
                    ('new', 'New'),
                    ('confirmed', 'Confirmed'),
                    ('sent', 'Sent'),
                    ('cancelled', 'Cancelled'),
                ],
                db_index=True,
                default='new',
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name='voucherorder',
            name='shipping_street',
            field=models.CharField(blank=True, max_length=255),
        ),
        migrations.AddField(
            model_name='voucherorder',
            name='shipping_house_number',
            field=models.CharField(blank=True, max_length=20),
        ),
        migrations.AddField(
            model_name='voucherorder',
            name='shipping_city',
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.AddField(
            model_name='voucherorder',
            name='shipping_postal_code',
            field=models.CharField(blank=True, max_length=20),
        ),
        migrations.AddField(
            model_name='voucherorder',
            name='shipping_country',
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.RunPython(forwards_backfill_status, backwards_backfill_is_sent),
        migrations.RemoveField(
            model_name='voucherorder',
            name='is_sent',
        ),
        migrations.AlterField(
            model_name='voucherorder',
            name='sent_at',
            field=models.DateTimeField(blank=True, help_text="When the voucher order status was set to 'sent'.", null=True),
        ),
    ]