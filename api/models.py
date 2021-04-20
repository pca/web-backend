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
    REGION_1 = "01"
    REGION_2 = "02"
    REGION_3 = "03"
    REGION_4A = "4A"
    REGION_4B = "4B"
    REGION_5 = "05"
    REGION_6 = "06"
    REGION_7 = "07"
    REGION_8 = "08"
    REGION_9 = "09"
    REGION_10 = "10"
    REGION_11 = "11"
    REGION_12 = "12"
    REGION_13 = "13"
    REGION_BARMM = "BARMM"
    REGION_CHOICES = (
        (REGION_NCR, "NCR (Luzon - Metro Manila)"),
        (REGION_CAR, "CAR (Luzon - Cordillera Region)"),
        (REGION_1, "Region I (Luzon - Ilocos Region)"),
        (REGION_2, "Region II (Luzon - Cagayan Valley)"),
        (REGION_3, "Region III (Luzon - Central Luzon)"),
        (REGION_4A, "Region IV-A (Luzon - Calabarzon)"),
        (REGION_4B, "Region IV-B (Luzon - Mimaropa)"),
        (REGION_5, "Region V (Luzon - Bicol Region)"),
        (REGION_6, "Region VI (Visayas - Western Visayas)"),
        (REGION_7, "Region VII (Visayas - Central Visayas)"),
        (REGION_8, "Region VIII (Visayas - Eastern Visayas)"),
        (REGION_9, "Region IX (Mindanao - Zamboanga Peninsula)"),
        (REGION_10, "Region X (Mindanao - Northern Mindanao)"),
        (REGION_11, "Region XI (Mindanao - Davao Region)"),
        (REGION_12, "Region XII (Mindanao - Soccsksargen)"),
        (REGION_13, "Region XIII (Mindanao - Caraga)"),
        (REGION_BARMM, "BARMM (Mindanao - Bangsamoro)"),
    )

    ZONE_LUZON = "luzon"
    ZONE_VISAYAS = "visayas"
    ZONE_MINDANAO = "mindanao"
    ZONE_CHOICES = (
        (ZONE_LUZON, "Luzon"),
        (ZONE_VISAYAS, "Visayas"),
        (ZONE_MINDANAO, "Mindanao"),
    )
    ZONE_REGIONS = {
        ZONE_LUZON: (
            REGION_NCR,
            REGION_CAR,
            REGION_1,
            REGION_2,
            REGION_3,
            REGION_4A,
            REGION_4B,
            REGION_5,
        ),
        ZONE_VISAYAS: (REGION_6, REGION_7, REGION_8),
        ZONE_MINDANAO: (
            REGION_9,
            REGION_10,
            REGION_11,
            REGION_12,
            REGION_13,
            REGION_BARMM,
        ),
    }

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
