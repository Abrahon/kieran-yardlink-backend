from django.contrib import admin
from .models import NotificationSettings, Notification, Device


# =====================================================
# Notification Settings
# =====================================================
@admin.register(NotificationSettings)
class NotificationSettingsAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "job_alert",
        "payment_alert",
        "weather_alert",
        "updated_at",
    )

    list_filter = (
        "job_alert",
        "payment_alert",
        "weather_alert",
        "updated_at",
    )

    search_fields = (
        "user__name",
        "user__email",
    )

    readonly_fields = (
        "updated_at",
    )

    ordering = ("-updated_at",)


# =====================================================
# Notifications
# =====================================================
@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "notification_type",
        "title",
        "is_read",
        "created_at",
    )

    list_filter = (
        "notification_type",
        "is_read",
        "created_at",
    )

    search_fields = (
        "user__name",
        "user__email",
        "title",
        "message",
    )

    readonly_fields = (
        "created_at",
    )

    ordering = ("-created_at",)

    fieldsets = (
        (
            "Notification Info",
            {
                "fields": (
                    "user",
                    "notification_type",
                    "title",
                    "message",
                )
            },
        ),
        (
            "Status",
            {
                "fields": (
                    "is_read",
                )
            },
        ),
        (
            "Audit",
            {
                "fields": (
                    "created_at",
                )
            },
        ),
    )

    actions = ["mark_as_read"]

    @admin.action(description="Mark selected notifications as read")
    def mark_as_read(self, request, queryset):
        queryset.update(is_read=True)


# =====================================================
# Devices
# =====================================================
@admin.register(Device)
class DeviceAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "short_token",
        "is_active",
        "created_at",
    )

    list_filter = (
        "is_active",
        "created_at",
    )

    search_fields = (
        "user__name",
        "user__email",
        "token",
    )

    readonly_fields = (
        "created_at",
    )

    ordering = ("-created_at",)

    fieldsets = (
        (
            "Device Information",
            {
                "fields": (
                    "user",
                    "token",
                    "is_active",
                )
            },
        ),
        (
            "Audit",
            {
                "fields": (
                    "created_at",
                )
            },
        ),
    )

    @admin.display(description="Device Token")
    def short_token(self, obj):
        return f"{obj.token[:25]}..."