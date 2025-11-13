from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("devices", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="devicesubmission",
            name="device_type",
            field=models.CharField(
                blank=True,
                help_text="General category such as phone, laptop, or monitor.",
                max_length=120,
            ),
        ),
        migrations.AddField(
            model_name="devicesubmission",
            name="pickup_address",
            field=models.TextField(blank=True),
        ),
    ]
