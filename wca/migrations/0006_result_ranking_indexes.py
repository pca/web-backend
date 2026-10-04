from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("wca", "0005_wca_v2_export_fields"),
    ]

    operations = [
        migrations.AddIndex(
            model_name="result",
            index=models.Index(
                fields=["person", "event", "country", "best", "id"],
                name="wca_res_person_evt_best_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="result",
            index=models.Index(
                fields=["event", "country", "best", "person"],
                name="wca_res_evt_ctry_best_person",
            ),
        ),
        migrations.AddIndex(
            model_name="result",
            index=models.Index(
                fields=["person", "event", "country", "average", "id"],
                name="wca_res_person_evt_avg_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="result",
            index=models.Index(
                fields=["event", "country", "average", "person"],
                name="wca_res_evt_ctry_avg_person",
            ),
        ),
    ]
