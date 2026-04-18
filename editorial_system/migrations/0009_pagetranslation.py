from django.db import migrations, models
import django.db.models.deletion


def migrate_i18n_to_pagetranslation(apps, schema_editor):
    Page = apps.get_model("editorial_system", "Page")
    PageTranslation = apps.get_model("editorial_system", "PageTranslation")

    to_create = []
    for page in Page.objects.all().iterator():
        content_i18n = page.content_i18n or {}
        state_i18n = page.translation_state_i18n or {}
        source_lang = (page.lang or "cs").strip().lower()

        for lang, content in content_i18n.items():
            normalized_lang = lang.strip().lower()
            if normalized_lang == source_lang or not content:
                continue
            state_data = state_i18n.get(lang, {})
            state = state_data.get("state", "") if isinstance(state_data, dict) else ""
            to_create.append(PageTranslation(
                page=page,
                lang=normalized_lang,
                content_json=content,
                state=state,
            ))

    if to_create:
        PageTranslation.objects.bulk_create(to_create, ignore_conflicts=True)


class Migration(migrations.Migration):

    dependencies = [
        ("editorial_system", "0008_photo_imagefield"),
    ]

    operations = [
        migrations.CreateModel(
            name="PageTranslation",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("lang", models.CharField(db_index=True, max_length=16)),
                ("content_json", models.JSONField()),
                ("state", models.CharField(blank=True, default="", max_length=64)),
                (
                    "page",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="translations",
                        to="editorial_system.page",
                    ),
                ),
            ],
        ),
        migrations.AddConstraint(
            model_name="pagetranslation",
            constraint=models.UniqueConstraint(
                fields=["page", "lang"],
                name="editorial_pagetranslation_page_lang_unique",
            ),
        ),
        migrations.RunPython(migrate_i18n_to_pagetranslation, migrations.RunPython.noop),
        migrations.RemoveField(model_name="page", name="content_i18n"),
        migrations.RemoveField(model_name="page", name="translation_state_i18n"),
    ]