from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from web.models import User, PCAProfile, WCAProfile, DatabaseConfig

admin.site.register(User, UserAdmin)
admin.site.register(PCAProfile)
admin.site.register(WCAProfile)
admin.site.register(DatabaseConfig)
