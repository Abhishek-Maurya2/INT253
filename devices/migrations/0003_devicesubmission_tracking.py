from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("devices", "0002_add_device_type_pickup_address"),
    ]

    operations = [
        migrations.AddField(
            model_name="devicesubmission",
            name="catalog_entry_created",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="devicesubmission",
            name="credits_awarded",
            field=models.BooleanField(default=False),
        ),
    ]
