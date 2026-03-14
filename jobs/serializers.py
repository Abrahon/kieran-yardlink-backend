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


from jobs.models import Job, JobItem, JobImage, JobReschedule
from rest_framework import serializers
from profiles.serializers import ClientProfileSerializer,LandscaperProfileSerializer
from landscapers.serializers import BusinessLandscaperProfileSerializer


class JobSerializer(serializers.ModelSerializer):
    items = serializers.SerializerMethodField()
    images = serializers.SerializerMethodField()
    reschedules = serializers.SerializerMethodField()
    client = ClientProfileSerializer(read_only=True)
    landscaper_info = serializers.SerializerMethodField()
    job_property = serializers.StringRelatedField()
    # debug_booking_price = serializers.SerializerMethodField()

    class Meta:
        model = Job
        fields = [
            "id",
            "booking",
            "client",
            "landscaper_info",
            "job_property",
            "scheduled_date",
            "scheduled_time",
            "total_price",
            # "debug_booking_price",
            "note",
            "status",
            "is_active",
            "completed_at",
            "items",
            "images",
            "reschedules",
        ]

    # def get_debug_booking_price(self, obj):
    #     return str(obj.booking.price) if obj.booking and obj.booking.price is not None else None

    def get_landscaper_info(self, obj):
        business = obj.landscaper

        if not business:
            return None

        user = business.user
        personal = getattr(user, "landscaperprofilies", None)

        return {
            "id": business.id,
            "name": personal.name if personal else None,
            "phone": personal.phone if personal else None,
            "image": personal.image.url if personal and personal.image else None,
            "business_name": business.business_name,
            "business_email": business.business_email,
            "business_phone": business.business_phone,
        }

    def get_items(self, obj):
        return JobItemSerializer(obj.items.all(), many=True).data

    def get_images(self, obj):
        return JobImageSerializer(obj.images.all(), many=True).data

    def get_reschedules(self, obj):
        return JobRescheduleSerializer(obj.reschedules.all(), many=True).data
