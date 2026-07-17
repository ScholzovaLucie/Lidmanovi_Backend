from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('editorial_system', '0009_pagetranslation'),
    ]

    operations = [
        migrations.CreateModel(
            name='PhotoPlacement',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('location', models.CharField(db_index=True, max_length=100)),
                ('order', models.PositiveIntegerField(default=0)),
                ('photo', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='placements', to='editorial_system.photo')),
            ],
            options={
                'ordering': ['location', 'order'],
                'unique_together': {('photo', 'location')},
            },
        ),
    ]