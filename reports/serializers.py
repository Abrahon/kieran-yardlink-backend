from rest_framework import serializers
from accounts.models import User
from reports.models import AdminInternalNote


class AdminInternalNoteSerializer(serializers.ModelSerializer):
    user_id = serializers.IntegerField(source="user.id", read_only=True)
    name = serializers.CharField(source="user.name", read_only=True)
    email = serializers.EmailField(source="user.email", read_only=True)
    created_by = serializers.SerializerMethodField()

    class Meta:
        model = AdminInternalNote
        fields = [
            "id",
            "user_id",
            "name",
            "email",
            "note",
            "is_active",
            "created_at",
            "updated_at",
            "created_by",
        ]
        read_only_fields = [
            "id",
            "user_id",
            "name",
            "email",
            "created_at",
            "updated_at",
            "created_by",
        ]

    def get_created_by(self, obj):
        if obj.created_by:
            return {
                "id": obj.created_by.id,
                "name": getattr(obj.created_by, "name", ""),
                "email": getattr(obj.created_by, "email", ""),
            }
        return None