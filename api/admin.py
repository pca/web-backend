from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _

from .models import RegionUpdateRequest

User = get_user_model()
admin.site.site_url = None


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    fieldsets = (
        (None, {"fields": ("username", "password")}),
        (
            _("Personal info"),
            {"fields": ("first_name", "last_name", "email", "region", "wca_id")},
        ),
        (
            _("Permissions"),
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                ),
            },
        ),
        (_("Important dates"), {"fields": ("last_login", "date_joined")}),
    )
    list_display = ("wca_id_or_username", "first_name", "last_name", "is_staff")

    @admin.display(description="WCA ID / Username")
    def wca_id_or_username(self, obj):
        return obj.wca_id or obj.username


@admin.register(RegionUpdateRequest)
class RegionUpdateRequestAdmin(admin.ModelAdmin):
    list_display = (
        "wca_id",
        "first_name",
        "last_name",
        "region",
        "status",
        "created_at",
    )
    list_editable = ("status",)
    list_filter = ("status",)
    readonly_fields = ("user",)

    def first_name(self, obj):
        return obj.user.first_name

    def last_name(self, obj):
        return obj.user.last_name

    def wca_id(self, obj):
        return obj.user.wca_id
