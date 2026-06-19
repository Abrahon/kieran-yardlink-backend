from django.contrib import admin
from .models import Job, JobItem, JobImage, JobReschedule


# =========================
# JOB ITEM INLINE
# =========================
class JobItemInline(admin.TabularInline):
    model = JobItem
    extra = 0
    readonly_fields = ("completed_at", "completed_by")
    fields = (
        "item_type",
        "service",
        "addon",
        "name",
        "price",
        "is_completed",
        "completed_at",
        "completed_by",
    )


# =========================
# JOB IMAGE INLINE
# =========================
class JobImageInline(admin.TabularInline):
    model = JobImage
    extra = 0
    readonly_fields = ("created_at",)
    fields = (
        "image",
        "image_type",
        "caption",
        "uploaded_by",
        "created_at",
    )


# =========================
# JOB RESCHEDULE INLINE
# =========================
class JobRescheduleInline(admin.TabularInline):
    model = JobReschedule
    extra = 0
    readonly_fields = ("created_at",)
    fields = (
        "old_date",
        "old_time",
        "new_date",
        "new_time",
        "reason",
        "status",
        "requested_by",
        "created_at",
    )


# =========================
# JOB ADMIN
# =========================
@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "client_name",
        "landscaper",
        "scheduled_date",
        "scheduled_time",
        "status",
        "payment_status",
        "total_price",
        "is_active",
    )

    list_filter = (
        "status",
        "is_active",
        "payment_status",
        "scheduled_date",
        "landscaper",
    )

    search_fields = (
        "id",
        "client__user__email",
        "external_client__email",
        "landscaper__business_name",
    )

    readonly_fields = (
        "created_at",
        "updated_at",
        "completed_at",
        "total_price",
    )

    inlines = [JobItemInline, JobImageInline, JobRescheduleInline]

    ordering = ("-created_at",)

    # =========================
    # CUSTOM ACTION
    # =========================
    actions = ["delete_upcoming_jobs"]

    def delete_upcoming_jobs(self, request, queryset):
        upcoming_qs = queryset.filter(status="upcoming")
        count = upcoming_qs.count()
        upcoming_qs.delete()

        self.message_user(
            request,
            f"{count} upcoming jobs deleted successfully."
        )

    delete_upcoming_jobs.short_description = "Delete selected UPCOMING jobs only"


# =========================
# JOB ITEM ADMIN
# =========================
@admin.register(JobItem)
class JobItemAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "job",
        "name",
        "item_type",
        "price",
        "is_completed",
        "completed_at",
    )

    list_filter = (
        "item_type",
        "is_completed",
    )

    search_fields = (
        "name",
        "job__id",
    )

    readonly_fields = (
        "completed_at",
        "completed_by",
    )


# =========================
# JOB IMAGE ADMIN
# =========================
@admin.register(JobImage)
class JobImageAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "job",
        "image_type",
        "uploaded_by",
        "created_at",
    )

    list_filter = (
        "image_type",
        "created_at",
    )

    search_fields = (
        "job__id",
        "caption",
    )

    readonly_fields = ("created_at",)


# =========================
# JOB RESCHEDULE ADMIN
# =========================
@admin.register(JobReschedule)
class JobRescheduleAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "job",
        "old_date",
        "new_date",
        "old_time",
        "new_time",
        "status",
        "requested_by",
        "created_at",
    )

    list_filter = (
        "status",
        "new_date",
        "created_at",
    )

    search_fields = (
        "job__id",
        "reason",
        "requested_by__email",
    )

    readonly_fields = ("created_at",)

    ordering = ("-created_at",)