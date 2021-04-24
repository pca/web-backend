from dj_rest_auth.registration.serializers import SocialLoginSerializer
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from . import app_settings
from .models import RegionUpdateRequest

User = get_user_model()


class WCALoginSerializer(SocialLoginSerializer):
    code = serializers.CharField()
    callback_url = serializers.CharField(required=False, allow_null=True)
    access_token = None
    id_token = None

    def validate_callback_url(self, url):
        if url not in app_settings.WCA_ALLOWED_CALLBACK_URLS:
            raise serializers.ValidationError(_("Url is not allowed"))
        return url


class RegionSerializer(serializers.Serializer):
    id = serializers.CharField()
    name = serializers.CharField()


class ZoneSerializer(serializers.Serializer):
    id = serializers.CharField()
    name = serializers.CharField()


class UserDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            "first_name",
            "last_name",
            "wca_id",
            "region",
            "region_updated_at",
            "created_at",
        )


class RegionUpdateRequestSerializer(serializers.ModelSerializer):
    status = serializers.SerializerMethodField()

    class Meta:
        model = RegionUpdateRequest
        fields = ("region", "status", "created_at")
        read_only_fields = ("status", "created_at")

    def get_status(self, obj):
        return obj.get_status_display()


class NewsSerializer(serializers.Serializer):
    from_name = serializers.CharField()
    message = serializers.CharField(required=False, allow_blank=True)
    image = serializers.URLField(required=False, allow_blank=True)
    permalink = serializers.URLField()
    created_at = serializers.DateTimeField()
