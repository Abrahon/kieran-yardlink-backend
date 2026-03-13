from rest_framework import serializers
from jobs.models import Job, JobItem, JobImage, JobReschedule


class JobItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = JobItem
        fields = [
            "id", "item_type", "service", "addon", "name", "description",
            "price", "is_completed", "completed_at", "completed_by", "note"
        ]
        read_only_fields = ["completed_at", "completed_by"]


class JobImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = JobImage
        fields = ["id", "job", "image", "image_type", "caption", "uploaded_by"]
        read_only_fields = ["uploaded_by"]


class JobRescheduleSerializer(serializers.ModelSerializer):
    class Meta:
        model = JobReschedule
        fields = [
            "id", "job", "old_date", "old_time",
            "new_date", "new_time", "reason", "requested_by", "created_at"
        ]
        read_only_fields = ["requested_by", "created_at", "old_date", "old_time"]


class JobSerializer(serializers.ModelSerializer):
    items = JobItemSerializer(many=True, read_only=True)
    images = JobImageSerializer(many=True, read_only=True)
    reschedules = JobRescheduleSerializer(many=True, read_only=True)
    client = serializers.StringRelatedField()
    landscaper = serializers.StringRelatedField()
    job_property = serializers.StringRelatedField()

    class Meta:
        model = Job
        fields = [
            "id", "booking", "client", "landscaper", "job_property",
            "scheduled_date", "scheduled_time", "total_price",
            "note", "status", "is_active", "completed_at",
            "items", "images", "reschedules"
        ]
        read_only_fields = ["total_price", "completed_at", "items", "images", "reschedules"]