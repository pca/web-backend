from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("wca", "0002_alter_person_gender"),
    ]

    operations = [
        migrations.CreateModel(
            name="BoundaryDataset",
            fields=[
                (
                    "version",
                    models.CharField(max_length=80, primary_key=True, serialize=False),
                ),
                ("source_url", models.URLField(max_length=500)),
                ("retrieved_on", models.DateField()),
                ("coordinate_system", models.CharField(default="EPSG:4326", max_length=32)),
                ("license", models.CharField(max_length=240)),
                ("attribution", models.CharField(blank=True, max_length=500)),
                ("processing_notes", models.TextField()),
                ("checksum_sha256", models.CharField(db_index=True, max_length=64)),
                ("feature_count", models.PositiveSmallIntegerField()),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.CreateModel(
            name="CompetitionRegionAssignment",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("region_code", models.CharField(blank=True, db_index=True, max_length=2, null=True)),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("assigned", "Assigned"),
                            ("missing_coordinates", "Missing coordinates"),
                            ("invalid_coordinates", "Invalid coordinates"),
                            ("outside_boundary", "Outside boundary"),
                            ("boundary", "On boundary"),
                            ("overlapping_regions", "Overlapping regions"),
                        ],
                        db_index=True,
                        max_length=32,
                    ),
                ),
                ("classified_latitude", models.IntegerField(blank=True, null=True)),
                ("classified_longitude", models.IntegerField(blank=True, null=True)),
                ("classified_at", models.DateTimeField(auto_now=True)),
                (
                    "boundary_dataset",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="competition_assignments",
                        to="wca.boundarydataset",
                    ),
                ),
                (
                    "competition",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="region_assignment",
                        to="wca.competition",
                    ),
                ),
            ],
        ),
        migrations.AddIndex(
            model_name="competitionregionassignment",
            index=models.Index(
                fields=["boundary_dataset", "status"],
                name="wca_assign_dataset_status_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="competitionregionassignment",
            index=models.Index(
                fields=["boundary_dataset", "region_code"],
                name="wca_assign_dataset_region_idx",
            ),
        ),
    ]
