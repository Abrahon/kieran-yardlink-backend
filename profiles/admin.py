from django.contrib import admin
from .models import WorkerProfile,AdminProfile  # replace with your app name
from django.utils.html import format_html

@admin.register(WorkerProfile)
class WorkerProfileAdmin(admin.ModelAdmin):
    list_display = ("worker_email", "admin_email", "name", "phone", "image_tag")
    search_fields = ("user__email", "name", "phone")
    readonly_fields = ("image_tag",)

    def worker_email(self, obj):
        return obj.user.email
    worker_email.short_description = "Worker Email"

    def admin_email(self, obj):
        # Assuming you have only one admin or want the first admin
        admin = AdminProfile.objects.first()
        return admin.user.email if admin else "-"
    admin_email.short_description = "Admin Email"

    def image_tag(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="50" height="50" />', obj.image.url)
        return "-"
    image_tag.short_description = "Profile Image"


from django.contrib import admin
from .models import AdminProfile
from django.utils.html import format_html

@admin.register(AdminProfile)
class AdminProfileAdmin(admin.ModelAdmin):
    list_display = ("admin_name", "admin_email", "phone", "image_tag")
    search_fields = ("user__email", "user__name", "phone")
    readonly_fields = ("image_tag",)

    def get_queryset(self, request):
        """
        Only show AdminProfile linked to users with role='admin'
        """
        qs = super().get_queryset(request)
        return qs.filter(user__role="admin")

    def admin_name(self, obj):
        return obj.user.name
    admin_name.short_description = "Admin Name"

    def admin_email(self, obj):
        return obj.user.email
    admin_email.short_description = "Admin Email"

    def image_tag(self, obj):
        """
        Render profile image in admin list view
        """
        if obj.image:
            return format_html('<img src="{}" width="50" height="50" style="object-fit: cover; border-radius:50%;" />', obj.image.url)
        return "-"
    image_tag.short_description = "Profile Image"


