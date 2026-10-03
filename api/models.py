from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
from django_lifecycle import LifecycleModel, hook, AFTER_UPDATE

from . import regions


class BaseModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class User(AbstractUser):
    REGION_NCR = regions.REGION_NCR
    REGION_CAR = regions.REGION_CAR
    REGION_1 = regions.REGION_1
    REGION_2 = regions.REGION_2
    REGION_3 = regions.REGION_3
    REGION_4A = regions.REGION_4A
    REGION_4B = regions.REGION_4B
    REGION_5 = regions.REGION_5
    REGION_6 = regions.REGION_6
    REGION_7 = regions.REGION_7
    REGION_8 = regions.REGION_8
    REGION_9 = regions.REGION_9
    REGION_10 = regions.REGION_10
    REGION_11 = regions.REGION_11
    REGION_12 = regions.REGION_12
    REGION_13 = regions.REGION_13
    REGION_18 = regions.REGION_18
    REGION_BARMM = regions.REGION_BARMM
    REGION_CHOICES = regions.REGION_CHOICES

    ZONE_LUZON = regions.ZONE_LUZON
    ZONE_VISAYAS = regions.ZONE_VISAYAS
    ZONE_MINDANAO = regions.ZONE_MINDANAO
    ZONE_CHOICES = regions.ZONE_CHOICES
    ZONE_REGIONS = regions.ZONE_REGIONS

    wca_id = models.CharField(max_length=64, db_index=True, null=True, blank=True)
    region = models.CharField(
        max_length=255, choices=REGION_CHOICES, null=True, blank=True
    )
    region_updated_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        if self.wca_id:
            return f"{self.wca_id} - {self.get_full_name()}"
        return self.get_full_name()


class RegionUpdateRequest(LifecycleModel):
    STATUS_PENDING = "p"
    STATUS_APPROVED = "a"
    STATUS_DENIED = "d"
    STATUS_CHOICES = (
        (STATUS_PENDING, "Pending"),
        (STATUS_APPROVED, "Approved"),
        (STATUS_DENIED, "Denied"),
    )

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="region_update_requests"
    )
    region = models.CharField(max_length=64, choices=User.REGION_CHOICES)
    status = models.CharField(
        max_length=8, choices=STATUS_CHOICES, default=STATUS_PENDING
    )
    staff_notes = models.TextField(
        blank=True, help_text="Only visible to staff and admins"
    )

    created_at = models.DateTimeField(db_index=True, auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user} - {self.get_region_display()}"

    @hook(AFTER_UPDATE, when="status", was=STATUS_PENDING, is_now=STATUS_APPROVED)
    def on_approve(self):
        self.user.region = self.region
        self.user.region_updated_at = timezone.now()
        self.user.save()


class StatisticsSnapshot(models.Model):
    STATUS_BUILDING = "building"
    STATUS_READY = "ready"
    STATUS_FAILED = "failed"
    STATUS_CHOICES = (
        (STATUS_BUILDING, "Building"),
        (STATUS_READY, "Ready"),
        (STATUS_FAILED, "Failed"),
    )

    export_version = models.CharField(max_length=120)
    export_checksum = models.CharField(max_length=64)
    boundary_dataset = models.ForeignKey(
        "wca.BoundaryDataset",
        related_name="statistics_snapshots",
        on_delete=models.PROTECT,
    )
    latest_year = models.PositiveSmallIntegerField()
    status = models.CharField(
        max_length=16, choices=STATUS_CHOICES, default=STATUS_BUILDING
    )
    is_active = models.BooleanField(default=False, db_index=True)
    coverage = models.JSONField(default=dict)
    error_message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(blank=True, null=True)
    activated_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("export_checksum", "boundary_dataset"),
                name="api_stats_snapshot_input_uniq",
            ),
            models.UniqueConstraint(
                fields=("is_active",),
                condition=models.Q(is_active=True),
                name="api_one_active_stats_snapshot",
            ),
        ]


class RegionalStrengthRecord(models.Model):
    RANK_SINGLE = "single"
    RANK_AVERAGE = "average"
    RANK_TYPE_CHOICES = (
        (RANK_SINGLE, "Single"),
        (RANK_AVERAGE, "Average"),
    )

    snapshot = models.ForeignKey(
        StatisticsSnapshot,
        related_name="regional_strength_records",
        on_delete=models.CASCADE,
    )
    event = models.ForeignKey("wca.Event", on_delete=models.PROTECT)
    rank_type = models.CharField(max_length=8, choices=RANK_TYPE_CHOICES)
    region_code = models.CharField(max_length=5)
    score = models.PositiveIntegerField()
    placement = models.PositiveSmallIntegerField()
    contributor_count = models.PositiveSmallIntegerField()
    slots = models.JSONField()
    content_hash = models.CharField(max_length=64)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("snapshot", "event", "rank_type", "region_code"),
                name="api_regional_strength_row_uniq",
            )
        ]
        indexes = [
            models.Index(
                fields=("snapshot", "event", "rank_type", "placement"),
                name="api_strength_event_lookup_idx",
            ),
            models.Index(
                fields=("snapshot", "region_code", "rank_type", "placement"),
                name="api_strength_region_lookup_idx",
            ),
        ]


class GrowthAnnualRecord(models.Model):
    METRIC_NEW_ATTENDEES = "new_attendees"
    METRIC_ATTENDANCES = "attendances"
    METRIC_ACTIVE_COMPETITORS = "active_competitors"
    METRIC_POPULAR_EVENTS = "popular_events"
    METRIC_CHOICES = (
        (METRIC_NEW_ATTENDEES, "New attendees"),
        (METRIC_ATTENDANCES, "Competition attendances"),
        (METRIC_ACTIVE_COMPETITORS, "Active competitors"),
        (METRIC_POPULAR_EVENTS, "Popular events"),
    )

    snapshot = models.ForeignKey(
        StatisticsSnapshot,
        related_name="growth_records",
        on_delete=models.CASCADE,
    )
    metric = models.CharField(max_length=24, choices=METRIC_CHOICES)
    year = models.PositiveSmallIntegerField()
    region_code = models.CharField(
        max_length=5,
        blank=True,
        help_text="Empty means the nationwide scope.",
    )
    event_id = models.CharField(
        max_length=6,
        blank=True,
        help_text="Set only for popular-event rows.",
    )
    value = models.PositiveIntegerField()
    unique_competitors = models.PositiveIntegerField(blank=True, null=True)
    content_hash = models.CharField(max_length=64)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("snapshot", "metric", "year", "region_code", "event_id"),
                name="api_growth_annual_row_uniq",
            )
        ]
        indexes = [
            models.Index(
                fields=("snapshot", "metric", "region_code", "year"),
                name="api_growth_metric_lookup_idx",
            )
        ]
