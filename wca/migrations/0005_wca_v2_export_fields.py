from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("wca", "0004_statistics_lookup_indexes"),
    ]

    operations = [
        migrations.AlterField(
            model_name="continent",
            name="latitude",
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name="continent",
            name="longitude",
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name="continent",
            name="zoom",
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="result",
            name="wca_result_id",
            field=models.PositiveBigIntegerField(blank=True, null=True, unique=True),
        ),
    ]
