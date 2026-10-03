from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("wca", "0004_statistics_lookup_indexes"),
        ("api", "0004_add_region_xviii"),
    ]

    operations = [
        migrations.CreateModel(
            name="StatisticsSnapshot",
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
                ("export_version", models.CharField(max_length=120)),
                ("export_checksum", models.CharField(max_length=64)),
                ("latest_year", models.PositiveSmallIntegerField()),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("building", "Building"),
                            ("ready", "Ready"),
                            ("failed", "Failed"),
                        ],
                        default="building",
                        max_length=16,
                    ),
                ),
                ("is_active", models.BooleanField(db_index=True, default=False)),
                ("coverage", models.JSONField(default=dict)),
                ("error_message", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("completed_at", models.DateTimeField(blank=True, null=True)),
                ("activated_at", models.DateTimeField(blank=True, null=True)),
                (
                    "boundary_dataset",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="statistics_snapshots",
                        to="wca.boundarydataset",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="RegionalStrengthRecord",
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
                (
                    "rank_type",
                    models.CharField(
                        choices=[("single", "Single"), ("average", "Average")],
                        max_length=8,
                    ),
                ),
                ("region_code", models.CharField(max_length=5)),
                ("score", models.PositiveIntegerField()),
                ("placement", models.PositiveSmallIntegerField()),
                ("contributor_count", models.PositiveSmallIntegerField()),
                ("slots", models.JSONField()),
                ("content_hash", models.CharField(max_length=64)),
                (
                    "event",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        to="wca.event",
                    ),
                ),
                (
                    "snapshot",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="regional_strength_records",
                        to="api.statisticssnapshot",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="GrowthAnnualRecord",
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
                (
                    "metric",
                    models.CharField(
                        choices=[
                            ("new_attendees", "New attendees"),
                            ("attendances", "Competition attendances"),
                            ("active_competitors", "Active competitors"),
                            ("popular_events", "Popular events"),
                        ],
                        max_length=24,
                    ),
                ),
                ("year", models.PositiveSmallIntegerField()),
                (
                    "region_code",
                    models.CharField(
                        blank=True,
                        help_text="Empty means the nationwide scope.",
                        max_length=5,
                    ),
                ),
                (
                    "event_id",
                    models.CharField(
                        blank=True,
                        help_text="Set only for popular-event rows.",
                        max_length=6,
                    ),
                ),
                ("value", models.PositiveIntegerField()),
                ("unique_competitors", models.PositiveIntegerField(blank=True, null=True)),
                ("content_hash", models.CharField(max_length=64)),
                (
                    "snapshot",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="growth_records",
                        to="api.statisticssnapshot",
                    ),
                ),
            ],
        ),
        migrations.AddConstraint(
            model_name="statisticssnapshot",
            constraint=models.UniqueConstraint(
                fields=("export_checksum", "boundary_dataset"),
                name="api_stats_snapshot_input_uniq",
            ),
        ),
        migrations.AddConstraint(
            model_name="statisticssnapshot",
            constraint=models.UniqueConstraint(
                condition=models.Q(is_active=True),
                fields=("is_active",),
                name="api_one_active_stats_snapshot",
            ),
        ),
        migrations.AddConstraint(
            model_name="regionalstrengthrecord",
            constraint=models.UniqueConstraint(
                fields=("snapshot", "event", "rank_type", "region_code"),
                name="api_regional_strength_row_uniq",
            ),
        ),
        migrations.AddIndex(
            model_name="regionalstrengthrecord",
            index=models.Index(
                fields=["snapshot", "event", "rank_type", "placement"],
                name="api_strength_event_lookup_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="regionalstrengthrecord",
            index=models.Index(
                fields=["snapshot", "region_code", "rank_type", "placement"],
                name="api_strength_region_lookup_idx",
            ),
        ),
        migrations.AddConstraint(
            model_name="growthannualrecord",
            constraint=models.UniqueConstraint(
                fields=("snapshot", "metric", "year", "region_code", "event_id"),
                name="api_growth_annual_row_uniq",
            ),
        ),
        migrations.AddIndex(
            model_name="growthannualrecord",
            index=models.Index(
                fields=["snapshot", "metric", "region_code", "year"],
                name="api_growth_metric_lookup_idx",
            ),
        ),
    ]
