from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from pca import models

admin.site.register(models.User, UserAdmin)
admin.site.register(models.PCAProfile)
admin.site.register(models.WCAProfile)
admin.site.register(models.DatabaseConfig)
