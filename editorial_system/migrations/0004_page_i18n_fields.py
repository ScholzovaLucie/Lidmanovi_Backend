from django.db import migrations, models


def initialize_page_i18n(apps, schema_editor):
    Page = apps.get_model("editorial_system", "Page")
    for page in Page.objects.all().iterator():
        translations = dict(page.content_i18n or {})
        source_lang = (page.lang or "cs").strip().lower()
        if page.content_json is not None and source_lang not in translations:
            translations[source_lang] = page.content_json
            page.content_i18n = translations
            page.save(update_fields=["content_i18n"])


class Migration(migrations.Migration):

    dependencies = [
        ("editorial_system", "0003_page_path_lang"),
    ]

    operations = [
        migrations.AddField(
            model_name="page",
            name="content_i18n",
            field=models.JSONField(blank=True, default=dict),
        ),
        migrations.AddField(
            model_name="page",
            name="translation_state_i18n",
            field=models.JSONField(blank=True, default=dict),
        ),
        migrations.RunPython(initialize_page_i18n, migrations.RunPython.noop),
    ]
