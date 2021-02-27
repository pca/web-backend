from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
from django_lifecycle import LifecycleModel, hook, AFTER_UPDATE


class BaseModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class User(AbstractUser):
    REGION_NCR = "NCR"
    REGION_CAR = "CAR"
    REGION_1 = "Region I"
    REGION_2 = "Region II"
    REGION_3 = "Region III"
    REGION_4A = "Region IV-A"
    REGION_4B = "Region IV-B"
    REGION_5 = "Region V"
    REGION_6 = "Region VI"
    REGION_7 = "Region VII"
    REGION_8 = "Region VIII"
    REGION_9 = "Region IX"
    REGION_10 = "Region X"
    REGION_11 = "Region XI"
    REGION_12 = "Region XII"
    REGION_13 = "Region XIII"
    REGION_BARMM = "BARMM"
    REGION_CHOICES = (
        ("NCR", REGION_NCR),
        ("CAR", REGION_CAR),
        ("01", REGION_1),
        ("02", REGION_2),
        ("03", REGION_3),
        ("4A", REGION_4A),
        ("4B", REGION_4B),
        ("05", REGION_5),
        ("06", REGION_6),
        ("07", REGION_7),
        ("08", REGION_8),
        ("09", REGION_9),
        ("10", REGION_10),
        ("11", REGION_11),
        ("12", REGION_12),
        ("13", REGION_13),
        ("BARMM", REGION_BARMM),
    )

    wca_id = models.CharField(max_length=64, db_index=True, null=True, blank=True)
    region = models.CharField(
        max_length=255, choices=REGION_CHOICES, null=True, blank=True
    )
    region_updated_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


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

    @hook(AFTER_UPDATE, when="status", was=STATUS_PENDING, is_now=STATUS_APPROVED)
    def on_approve(self):
        self.user.region = self.region
        self.user.region_updated_at = timezone.now()
        self.user.save()
