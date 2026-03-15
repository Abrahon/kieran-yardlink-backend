from rest_framework import serializers
from jobs.models import Job, JobItem, JobImage, JobReschedule
from rest_framework import generics, permissions, serializers
from rest_framework.response import Response
from jobs.models import Job, JobItem
from landscapers.models import Service, Addon

class JobItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = JobItem
        fields = [
            "id", "item_type", "service", "addon", "name", "description",
            "price", "is_completed", "completed_at", "completed_by", "note"
        ]
        read_only_fields = ["completed_at", "completed_by"]




class AddJobItemsSerializer(serializers.Serializer):
    job_id = serializers.IntegerField()
    items = serializers.ListField(child=serializers.DictField(), allow_empty=False)

    def validate(self, attrs):
        request = self.context["request"]
        landscaper = getattr(request.user, "landscaper_profile", None)
        if not landscaper:
            raise serializers.ValidationError("Landscaper profile not found.")

        try:
            job = Job.objects.get(id=attrs["job_id"], landscaper=landscaper)
        except Job.DoesNotExist:
            raise serializers.ValidationError("Job not found.")

        attrs["job"] = job
        return attrs

    def create(self, validated_data):
        job = validated_data["job"]
        items_data = validated_data["items"]
        created_items = []

        for idx, item in enumerate(items_data):
            item_type = item.get("item_type")
            service_id = item.get("service")
            addon_id = item.get("addon")
            name = item.get("name")
            description = item.get("description", "")
            price = item.get("price", "0.00")

            service = Service.objects.filter(id=service_id).first() if service_id else None
            addon = Addon.objects.filter(id=addon_id).first() if addon_id else None

            if item_type == JobItem.ItemType.STANDARD_SERVICE and service:
                name = service.name
                description = service.description
                price = service.base_price or 0

            if item_type == JobItem.ItemType.ADDON and addon:
                name = addon.name
                description = addon.description
                price = addon.price or 0

            job_item = JobItem.objects.create(
                job=job,
                item_type=item_type,
                service=service,
                addon=addon,
                name=name,
                description=description,
                price=price,
                sort_order=idx
            )
            created_items.append(job_item)

        job.recalculate_total_price()
        job.update_status_from_items()

        return {"job": job, "items": created_items}


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
