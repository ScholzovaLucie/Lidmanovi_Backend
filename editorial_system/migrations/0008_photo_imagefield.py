import editorial_system.photo.models
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("editorial_system", "0007_photo"),
    ]

    operations = [
        migrations.AlterField(
            model_name="photo",
            name="image",
            field=models.ImageField(upload_to=editorial_system.photo.models.photo_upload_to),
        ),
    ]
