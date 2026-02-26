from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('editorial_system', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='iframeembed',
            name='title_i18n',
            field=models.JSONField(blank=True, default=dict),
        ),
        migrations.AddField(
            model_name='infobox',
            name='title_i18n',
            field=models.JSONField(blank=True, default=dict),
        ),
    ]
