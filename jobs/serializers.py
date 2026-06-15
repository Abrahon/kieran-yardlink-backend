from rest_framework import serializers
from jobs.models import Job, JobItem, JobImage, JobReschedule
from rest_framework import generics, permissions, serializers
from rest_framework.response import Response
from jobs.models import Job, JobItem
from landscapers.models import Service, Addon
from profiles.models import ExternalClient
from profiles.models import ExternalClient
from payments.enums import PaymentStatus  
from jobs.models import Job, JobItem, JobImage, JobReschedule
from rest_framework import serializers
from profiles.serializers import ClientProfileSerializer,LandscaperProfileSerializer
from landscapers.serializers import BusinessLandscaperProfileSerializer
from rest_framework import serializers
from profiles.serializers import ExternalClientSerializer, ClientProfileSerializer
from .models import Job
from property.serializers import PropertySerializer
from rest_framework import serializers
from jobs.models import Job, JobImage, JobReschedule
from profiles.serializers import ClientProfileSerializer

from decimal import Decimal, InvalidOperation
from rest_framework import serializers
from profiles.models import ExternalClient
from jobs.models import Job, JobItem

from django.utils import timezone
from rest_framework import serializers




class JobItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = JobItem
        fields = [
            "id", "item_type", "service", "addon", "name", "description",
            "price", "is_completed", "completed_at", "completed_by", "note"
        ]
        read_only_fields = ["completed_at", "completed_by"]



class JobImageSerializer(serializers.ModelSerializer):
    image = serializers.ImageField(required=False, allow_null=True)

    class Meta:
        model = JobImage
        fields = ["id", "job", "image", "image_type", "caption", "uploaded_by"]
        read_only_fields = ["uploaded_by"]

    # def get_image(self, obj):
    #     if obj.image:
    #         return obj.image.url
    #     return None

    def to_representation(self, instance):
        """Return full Cloudinary URL for icon."""
        ret = super().to_representation(instance)
        if instance.image:
            # instance.icon.url is the Cloudinary URL
            ret['image'] = instance.image.url
        else:
            ret['image'] = None
        return ret





from rest_framework import serializers
from django.utils import timezone
from .models import JobReschedule


class JobRescheduleSerializer(serializers.ModelSerializer):

    class Meta:
        model = JobReschedule
        fields = [
            "id",
            "job",
            "old_date",
            "old_time",
            "new_date",
            "new_time",
            "reason",
            "requested_by",
            "status",        
            "created_at",
        ]

        read_only_fields = [
            "requested_by",
            "created_at",
            "old_date",
            "old_time",
            "status",       
        ]


    def validate(self, attrs):

        new_date = attrs.get("new_date")
        new_time = attrs.get("new_time")
        job = attrs.get("job")

        if not new_date:
            raise serializers.ValidationError({
                "new_date": "This field is required."
            })

        if not new_time:
            raise serializers.ValidationError({
                "new_time": "This field is required."
            })

        # -----------------------------
        # 1. block past date
        # -----------------------------
        if new_date < timezone.now().date():
            raise serializers.ValidationError({
                "new_date": "Cannot reschedule to past date."
            })

        # -----------------------------
        # 2. check working hours
        # -----------------------------
        landscaper = job.landscaper

        weekday = new_date.strftime("%A").upper()

        working = WorkingHours.objects.filter(
            landscaper=landscaper,
            day=weekday,
            is_active=True,
            start_time__lte=new_time,
            end_time__gte=new_time
        )

        if not working.exists():
            raise serializers.ValidationError({
                "new_time": "Selected time is outside landscaper working hours."
            })

        # -----------------------------
        # 3. prevent double booking
        # -----------------------------
        conflict = Job.objects.filter(
            landscaper=landscaper,
            scheduled_date=new_date,
            scheduled_time=new_time,
            is_active=True,
            status__in=["upcoming", "in_progress"]
        ).exclude(id=job.id)

        if conflict.exists():
            raise serializers.ValidationError({
                "new_time": "This time slot is already booked."
            })

        return attrs

    



class JobSerializer(serializers.ModelSerializer):
    total_price = serializers.SerializerMethodField()
    booking_price = serializers.SerializerMethodField()
    items = serializers.SerializerMethodField()
    images = serializers.SerializerMethodField()
    reschedules = serializers.SerializerMethodField()
    client = ClientProfileSerializer(read_only=True)
    landscaper_info = serializers.SerializerMethodField()
    client = serializers.SerializerMethodField()
    # CHANGED: removed StringRelatedField so we can control output
    job_property = PropertySerializer(read_only=True)

    external_client = ExternalClientSerializer(read_only=True)

    class Meta:
        model = Job
        fields = [
            "id",
            "booking",
            "client",
            "external_client",
            "landscaper_info",
            "job_property",
            "scheduled_date",
            "scheduled_time",
            "booking_price",
            "total_price",
            "note",
            "status",
            "is_active",
            "completed_at",
            "items",
            "images",
            "reschedules",
        ]

    def get_booking_price(self, obj):
        if obj.booking and obj.booking.price is not None:
            return str(obj.booking.price)
        return "0.00"

    def get_total_price(self, obj):
        if obj.total_price is None or obj.total_price == 0:
            if obj.booking and obj.booking.price is not None:
                return str(obj.booking.price)
            return "0.00"
        return str(obj.total_price)

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

    # =====================================
    # FIX: ONLY SHOW SELECTED PROPERTY
    # =====================================
    def get_client(self, obj):

        # =========================
        # NORMAL CLIENT JOB
        # =========================
        if obj.client and obj.client.user:
            user = obj.client.user

            return {
                "type": "client",
                "id": obj.client.id,
                "user_id": user.id,
                "email": user.email,

                "name": getattr(user, "get_full_name", lambda: None)() or getattr(user, "name", None),
                "phone": getattr(user, "phone", None),
                "latitude": getattr(user, "latitude", None),
                "longitude": getattr(user, "longitude", None),
                "address": getattr(user, "address", None),

                "image": (
                    obj.client.image.url
                    if getattr(obj.client, "image", None)
                    else None
                ),
            }

        # =========================
        # MANUAL JOB (external client)
        # =========================
        if obj.external_client:
            return {
                "type": "external_client",
                "id": obj.external_client.id,
                "name": obj.external_client.name,
                "email": obj.external_client.email,
                "phone": obj.external_client.phone,
                "latitude": getattr(obj.external_client, "latitude", None),
                "longitude": getattr(obj.external_client, "longitude", None),
                "address": getattr(obj.external_client, "address", None),
                "image": None,
            }

        return None



    def get_items(self, obj):
        return JobItemSerializer(obj.items.all(), many=True).data

    def get_images(self, obj):
        return JobImageSerializer(obj.images.all(), many=True).data

    def get_reschedules(self, obj):
        return JobRescheduleSerializer(obj.reschedules.all(), many=True).data





# completd job serializers
class CompletedJobSerializer(serializers.ModelSerializer):
    booking_price = serializers.SerializerMethodField()
    client = ClientProfileSerializer(read_only=True)
    external_client = serializers.SerializerMethodField() 
    landscaper_info = serializers.SerializerMethodField()
    job_property = serializers.StringRelatedField()

    completed_items_list = serializers.SerializerMethodField()
    before_images = serializers.SerializerMethodField()
    after_images = serializers.SerializerMethodField()
    images = serializers.SerializerMethodField()

    class Meta:
        model = Job
        fields = [
            "id",
            "booking",
            "client",
            "external_client", 
            "landscaper_info",
            "job_property",
            "scheduled_date",
            "scheduled_time",
            "booking_price",
            "total_price",
            "payment_status",
            "note",
            "status",
            "is_active",
            "completed_at",
            "completed_items_list",
            "before_images",
            "after_images",
            "images",
        ]

    def get_booking_price(self, obj):
        if obj.booking and obj.booking.price is not None:
            return str(obj.booking.price)
        return "0.00"

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
    
    def get_external_client(self, obj):
        if not getattr(obj, "external_client", None):
            return None

        return {
            "id": obj.external_client.id,
            "name": obj.external_client.name,
            "email": obj.external_client.email,
            "phone": obj.external_client.phone,
            "company_name": obj.external_client.company_name,
            "address": obj.external_client.address,
        }
    
    def get_completed_items_list(self, obj):
        completed_items = obj.items.filter(is_completed=True).order_by("sort_order", "id")
        return JobItemSerializer(completed_items, many=True).data

    def get_before_images(self, obj):
        before = obj.images.filter(image_type=JobImage.ImageType.BEFORE)
        return JobImageSerializer(before, many=True).data

    def get_after_images(self, obj):
        after = obj.images.filter(image_type=JobImage.ImageType.AFTER)
        return JobImageSerializer(after, many=True).data

    def get_images(self, obj):
        return JobImageSerializer(obj.images.all(), many=True).data






class ManualOneTimeJobCreateSerializer(serializers.Serializer):
    external_client_id = serializers.IntegerField()
    scheduled_date = serializers.DateField()
    scheduled_time = serializers.TimeField()
    note = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    items = serializers.ListField(child=serializers.DictField(), allow_empty=False)

    def validate(self, attrs):
        request = self.context["request"]
        landscaper = getattr(request.user, "landscaper_profile", None)
        if not landscaper:
            raise serializers.ValidationError("Landscaper profile not found.")

        try:
            external_client = ExternalClient.objects.get(
                id=attrs["external_client_id"],
                landscaper=landscaper,
                is_active=True,
            )
        except ExternalClient.DoesNotExist:
            raise serializers.ValidationError("External client not found.")

        items = attrs.get("items", [])
        if not items:
            raise serializers.ValidationError("At least one item is required.")

        for index, item in enumerate(items):
            name = item.get("name")
            price = item.get("price")

            if not name:
                raise serializers.ValidationError({
                    "items": {
                        index: "Each item must have a name."
                    }
                })

            if price in [None, ""]:
                raise serializers.ValidationError({
                    "items": {
                        index: "Each item must have a price."
                    }
                })

            try:
                price_decimal = Decimal(str(price).strip())
            except (InvalidOperation, ValueError, TypeError):
                raise serializers.ValidationError({
                    "items": {
                        index: "Invalid price format."
                    }
                })

            if price_decimal < 0:
                raise serializers.ValidationError({
                    "items": {
                        index: "Price cannot be negative."
                    }
                })

        attrs["external_client"] = external_client
        attrs["landscaper"] = landscaper
        return attrs

    def create(self, validated_data):
        external_client = validated_data["external_client"]
        landscaper = validated_data["landscaper"]
        items_data = validated_data["items"]

        job = Job.objects.create(
            external_client=external_client,
            client=None,
            booking=None,
            landscaper=landscaper,
            scheduled_date=validated_data["scheduled_date"],
            scheduled_time=validated_data["scheduled_time"],
            note=validated_data.get("note"),
            status=Job.Status.UPCOMING,
            is_active=True,
            total_price=Decimal("0.00"),  # temporary
        )

        total = Decimal("0.00")   # 🔥 FIX ADDED

        for idx, item in enumerate(items_data):
            price = Decimal(str(item.get("price")).strip())

            JobItem.objects.create(
                job=job,
                item_type=JobItem.ItemType.CUSTOM,
                name=item.get("name"),
                description=item.get("description", ""),
                price=price,
                sort_order=idx,
            )

            total += price   # 🔥 FIX ADDED

        # 🔥 FIX: UPDATE JOB TOTAL PRICE
        job.total_price = total
        job.save(update_fields=["total_price"])

        return job




class JobItemClientSerializer(serializers.ModelSerializer):
    class Meta:
        model = JobItem
        fields = [
            "id",
            "item_type",
            "name",
            "description",
            "price",
            "is_completed",
            "completed_at",
        ]





class ClientJobDetailSerializer(serializers.ModelSerializer):
    completed_items = serializers.SerializerMethodField()
    before_images = serializers.SerializerMethodField()
    after_images = serializers.SerializerMethodField()
    landscaper_name = serializers.SerializerMethodField() 
    stripe_pay_url = serializers.SerializerMethodField() 
    payment_status = serializers.SerializerMethodField()  

    class Meta:
        model = Job
        fields = [
            "id",
            "client_name",
            "landscaper_name", 
            "scheduled_date",
            "scheduled_time",
            "status",
            "payment_status",
            "total_price",
            "note",
            "stripe_pay_url",

            # custom
            "completed_items",
            "before_images",
            "after_images",
        ]

    def get_completed_items(self, obj):
        items = obj.items.filter(is_completed=True)
        return JobItemClientSerializer(items, many=True).data
    

    def get_payment_status(self, obj):
        return obj.payment_status

    def get_before_images(self, obj):
        images = obj.images.filter(image_type="before")
        return JobImageSerializer(images, many=True).data

    def get_after_images(self, obj):
        images = obj.images.filter(image_type="after")
        return JobImageSerializer(images, many=True).data

    # ✅ NEW METHOD
    def get_landscaper_name(self, obj):
        landscaper = obj.landscaper
        if not landscaper:
            return None
        

        
    def get_stripe_pay_url(self, obj):
        invoice = getattr(obj, "invoice", None)

        if not invoice:
            return None

        if invoice.status == "paid":
            return None

        return {
            "invoice_id": invoice.id,
            "amount": str(invoice.total),
            "can_pay": True,
            "url": invoice.stripe_checkout_url  # ✅ ADD THIS
        }
    
    def get_landscaper_name(self, obj):
        user = getattr(obj.landscaper, "user", None)

        if not user:
            return None

        # Best option (Django built-in)
        name = user.get_full_name()

        if name:
            return name

        # fallback if full_name is empty
        if user.first_name or user.last_name:
            return f"{user.first_name} {user.last_name}".strip()

        # last fallback (optional)
        return user.username
    


class ProblemJobSerializer(serializers.ModelSerializer):

    property_address = serializers.SerializerMethodField()

    class Meta:
        model = Job
        fields = [
            "id",
            "status",
            "note",
            "property_address",
            "scheduled_date",
            "scheduled_time",
        ]

    def get_property_address(self, obj):

        # 1️⃣ direct job property (highest priority)
        if obj.job_property and obj.job_property.address:
            return obj.job_property.address

        # 2️⃣ fallback to booking property
        if obj.booking and obj.booking.property:
            return obj.booking.property.address

        return None