from django.contrib import admin
from .models import BusinessProfile, ClientCustomService


# =====================================================
# Business Profile Admin
# =====================================================
@admin.register(BusinessProfile)
class BusinessProfileAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "business_name",
        "user",
        "business_email",
        "business_phone",
        "service_radius_km",
        "quickbooks_connected",
        "is_profile_completed",
        "created_at",
    )

    list_filter = (
        "quickbooks_connected",
        "is_profile_completed",
        "created_at",
    )

    search_fields = (
        "business_name",
        "business_email",
        "business_phone",
        "user__email",
        "user__name",
    )

    readonly_fields = (
        "created_at",
        "updated_at",
    )

    ordering = ("-created_at",)

    fieldsets = (
        (
            "User Information",
            {
                "fields": (
                    "user",
                )
            },
        ),
        (
            "Business Details",
            {
                "fields": (
                    "business_name",
                    "business_email",
                    "business_phone",
                    "tagline",
                    "description",
                )
            },
        ),
        (
            "Location",
            {
                "fields": (
                    "latitude",
                    "longitude",
                    "service_radius_km",
                )
            },
        ),
        (
            "Media & Documents",
            {
                "fields": (
                    "profile_image",
                    "insurance_doc",
                    "license_doc",
                )
            },
        ),
        (
            "Integrations",
            {
                "fields": (
                    "quickbooks_connected",
                )
            },
        ),
        (
            "Profile Status",
            {
                "fields": (
                    "is_profile_completed",
                )
            },
        ),
        (
            "Timestamps",
            {
                "fields": (
                    "created_at",
                    "updated_at",
                )
            },
        ),
    )


# =====================================================
# Client Custom Service Admin
# =====================================================
@admin.register(ClientCustomService)
class ClientCustomServiceAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "name",
        "client",
        "landscaper",
        "property",
        "price",
        "status",
        "is_active",
        "service_type",
        "preferred_date",
        "created_at",
    )

    list_filter = (
        "status",
        "is_active",
        "recurring_type",
        "created_at",
        "updated_at",
    )

    search_fields = (
        "name",
        "description",
        "note",
    )

    readonly_fields = (
        "created_at",
        "updated_at",
    )

    ordering = ("-created_at",)

    fieldsets = (
        (
            "Basic Information",
            {
                "fields": (
                    "client",
                    "landscaper",
                    "property",
                    "booking",
                    "name",
                    "description",
                    "note",
                )
            },
        ),
        (
            "Pricing",
            {
                "fields": (
                    "price",
                )
            },
        ),
        (
            "Schedule",
            {
                "fields": (
                    "preferred_date",
                    "preferred_time",
                )
            },
        ),
        (
            "Recurring Settings",
            {
                "fields": (
                    "recurring_type",
                    "recurring_day_of_week",
                )
            },
        ),
        (
            "Status",
            {
                "fields": (
                    "status",
                    "is_active",
                )
            },
        ),
        (
            "Audit",
            {
                "fields": (
                    "created_at",
                    "updated_at",
                )
            },
        ),
    )

    @admin.display(description="Service Type")
    def service_type(self, obj):
        return "Recurring" if obj.recurring_type else "One-Time"