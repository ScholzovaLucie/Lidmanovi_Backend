from django.db import migrations, models


def populate_page_path(apps, schema_editor):
    Page = apps.get_model("editorial_system", "Page")
    for page in Page.objects.filter(path__isnull=True).iterator():
        page.path = f"/page-{page.id}"
        if not page.lang:
            page.lang = "cs"
        page.save(update_fields=["path", "lang"])


class Migration(migrations.Migration):

    dependencies = [
        ("editorial_system", "0002_add_title_i18n_fields"),
    ]

    operations = [
        migrations.AddField(
            model_name="page",
            name="lang",
            field=models.CharField(db_index=True, default="cs", max_length=16),
        ),
        migrations.AddField(
            model_name="page",
            name="path",
            field=models.CharField(blank=True, db_index=True, max_length=255, null=True),
        ),
        migrations.RunPython(populate_page_path, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="page",
            name="path",
            field=models.CharField(db_index=True, max_length=255),
        ),
        migrations.AddConstraint(
            model_name="page",
            constraint=models.UniqueConstraint(
                fields=("path", "lang"),
                name="editorial_page_path_lang_unique",
            ),
        ),
    ]
