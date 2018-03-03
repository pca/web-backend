from django.contrib.auth.models import AbstractUser
from django.db import models

from web.constants import REGION_CHOICES, CITY_PROVINCE_CHOICES


class User(AbstractUser):
    has_default_password = models.BooleanField(default=True)


class WCAProfile(models.Model):
    def __str__(self):
        return self.wca_id or self.name

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    wca_pk = models.IntegerField()
    wca_id = models.CharField(max_length=30, null=True, blank=True, unique=True)
    name = models.CharField(max_length=70)
    gender = models.CharField(max_length=10)
    country_iso2 = models.CharField(max_length=10)
    delegate_status = models.CharField(max_length=30, null=True, blank=True)
    avatar_url = models.CharField(max_length=255)
    avatar_thumb_url = models.CharField(max_length=255)
    is_default_avatar = models.BooleanField()
    wca_created_at = models.CharField(max_length=500)
    wca_updated_at = models.CharField(max_length=500)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class PCAProfile(models.Model):
    def __str__(self):
        return str(self.user)

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    region = models.CharField(max_length=255, choices=REGION_CHOICES, null=True, blank=True)
    city_province = models.CharField(max_length=255, choices=CITY_PROVINCE_CHOICES, null=True, blank=True, verbose_name='City/Province')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class DatabaseConfig(models.Model):
    """A singleton database config record for switching from
    wca1 to wca2 databases.
    """
    active_database = models.CharField(max_length=100)
    inactive_database = models.CharField(max_length=100)

    def __str__(self):
        return self.active_database

    @classmethod
    def db(self):
        config = self.objects.first()
        return config.active_database
