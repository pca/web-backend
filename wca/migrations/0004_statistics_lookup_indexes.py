from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("wca", "0003_competition_region_assignment"),
    ]

    operations = [
        migrations.AddIndex(
            model_name="ranksaverage",
            index=models.Index(
                fields=["event", "country_rank", "person"],
                name="wca_rankavg_event_rank_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="rankssingle",
            index=models.Index(
                fields=["event", "country_rank", "person"],
                name="wca_ranksingle_event_rank_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="result",
            index=models.Index(
                fields=["person", "competition"],
                name="wca_result_person_comp_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="result",
            index=models.Index(
                fields=["competition", "event", "person"],
                name="wca_result_comp_event_person",
            ),
        ),
    ]
