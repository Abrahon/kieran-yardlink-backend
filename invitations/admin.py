from django.contrib import admin
from .models import TeamInvitation

@admin.register(TeamInvitation)
class TeamInvitationAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "email",
        "inviter",
        "landscaper",
        "status",
        "created_at",
        "expires_at",
        "accepted_at",
    )
    list_filter = ("status", "created_at", "expires_at")
    search_fields = ("email", "inviter__email", "landscaper__user__email")
    readonly_fields = ("token", "created_at", "accepted_at")
    ordering = ("-created_at",)
    date_hierarchy = "created_at"

    fieldsets = (
        ("Invitation Info", {
            "fields": ("email", "inviter", "landscaper", "status", "token")
        }),
        ("Timestamps", {
            "fields": ("created_at", "expires_at", "accepted_at")
        }),
    )

    def get_queryset(self, request):
        """Show only invitations that have been accepted."""
        qs = super().get_queryset(request)
        return qs.filter(status="accepted")
