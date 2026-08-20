from django.db import migrations, models


def seed_language_switcher(apps, schema_editor):
    AppSetting = apps.get_model("pension", "AppSetting")
    AppSetting.objects.get_or_create(
        key="languageSwitcher.enabled",
        defaults={"value": True},
    )


class Migration(migrations.Migration):
    dependencies = [("pension", "0022_remove_room_max_adults_max_children")]

    operations = [
        migrations.CreateModel(
            name="AppSetting",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("key", models.CharField(max_length=255, unique=True)),
                ("value", models.JSONField(null=True)),
            ],
            options={"ordering": ["key"]},
        ),
        migrations.RunPython(seed_language_switcher, migrations.RunPython.noop),
    ]
