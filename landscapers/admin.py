from django.contrib import admin

# Register your models here.
# admin.py

from django.contrib import admin
from .models import LandscaperProfile


@admin.register(LandscaperProfile)
class LandscaperProfileAdmin(admin.ModelAdmin):
    list_display = (
        "business_name",
        "user",
        "business_email",
        "business_phone",
        "is_profile_completed",
        "latitude",
        "longitude",
        "created_at",
    )
    list_filter = ("is_profile_completed", "created_at")
    search_fields = ("business_name", "business_email", "business_phone", "user__email")
    readonly_fields = ("created_at",)
