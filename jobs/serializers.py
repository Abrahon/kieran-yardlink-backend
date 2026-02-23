# from rest_framework import serializers
# from django.shortcuts import get_object_or_404
# from cloudinary.uploader import upload
# from .models import Job
# from accounts.models import User
# from property.models import Property

# class PropertySerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Property
#         fields = ["id", "address", "latitude", "longitude", "property_size", "grass_types"]

# class UserMinimalSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = User
#         fields = ["id", "name", "email"]

# class JobSerializer(serializers.ModelSerializer):
#     landscaper = UserMinimalSerializer(read_only=True)
#     client = UserMinimalSerializer(read_only=True)
#     property = PropertySerializer(read_only=True)

#     landscaper_id = serializers.IntegerField(write_only=True, required=False)
#     client_id = serializers.IntegerField(write_only=True, required=False)
#     property_id = serializers.IntegerField(write_only=True)

#     # Accept multiple file uploads
#     images = serializers.ListField(
#         child=serializers.FileField(),
#         write_only=True,
#         required=False,
#         allow_empty=True
#     )

#     # Show uploaded image URLs
#     existing_images = serializers.ListField(
#         child=serializers.URLField(),
#         read_only=True,
#         source="images"
#     )

#     class Meta:
#         model = Job
#         fields = [
#             "id", "landscaper", "client", "property",
#             "landscaper_id", "client_id", "property_id",
#             "date", "start_time", "end_time",
#             "status", "final_price", "is_reduced",
#             "images", "existing_images", "notes",
#             "created_at", "updated_at"
#         ]
#         read_only_fields = ["created_at", "updated_at", "existing_images"]

#     def _upload_files(self, files, instance=None):
#         urls = instance.images if instance else []
#         for f in files:
#             result = upload(f, folder="job_images")
#             urls.append(result["secure_url"])
#         return urls

#     def create(self, validated_data):
#         request = self.context.get("request")
#         client = request.user

#         landscaper_id = validated_data.pop("landscaper_id", None)
#         landscaper = get_object_or_404(User, id=landscaper_id, role="landscaper") if landscaper_id else None

#         property_id = validated_data.pop("property_id")
#         property_obj = get_object_or_404(Property, id=property_id)

#         files = validated_data.pop("images", [])

#         job = Job.objects.create(
#             landscaper=landscaper,
#             client=client,
#             property=property_obj,
#             **validated_data
#         )

#         if files:
#             job.images = self._upload_files(files)
#             job.save()

#         return job

#     def update(self, instance, validated_data):
#         # Extract files separately (DRF sends them in context['request'].FILES)
#         request = self.context.get("request")
#         files = request.FILES.getlist("images")  # ✅ This is key

#         # Update other fields
#         for attr, value in validated_data.items():
#             setattr(instance, attr, value)

#         # Append new images
#         if files:
#             instance.images += self._upload_files(files, instance=instance)

#         instance.save()
#         return instance
from rest_framework import serializers
from django.shortcuts import get_object_or_404
from cloudinary.uploader import upload
from .models import Job
from accounts.models import User
from property.models import Property

# -------------------------
# Minimal User Serializer
# -------------------------
class UserMinimalSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "name", "email"]

# -------------------------
# Property Serializer
# -------------------------
class PropertySerializer(serializers.ModelSerializer):
    class Meta:
        model = Property
        fields = ["id", "address", "latitude", "longitude", "property_size", "grass_types"]

# -------------------------
# Job Serializer
# -------------------------
class JobSerializer(serializers.ModelSerializer):
    landscaper = UserMinimalSerializer(read_only=True)
    client = UserMinimalSerializer(read_only=True)
    property = PropertySerializer(read_only=True)

    landscaper_id = serializers.IntegerField(write_only=True, required=False)
    client_id = serializers.IntegerField(write_only=True, required=False)
    property_id = serializers.IntegerField(write_only=True)

    # Accept file uploads
    images = serializers.ListField(
        child=serializers.FileField(),
        write_only=True,
        required=False
    )

    # Show uploaded image URLs
    existing_images = serializers.ListField(
        child=serializers.URLField(),
        read_only=True,
        source="images"
    )

    class Meta:
        model = Job
        fields = [
            "id", "landscaper", "client", "property",
            "landscaper_id", "client_id", "property_id",
            "date", "start_time", "end_time",
            "status", "final_price", "is_reduced",
            "images", "existing_images", "notes",
            "created_at", "updated_at"
        ]
        read_only_fields = ["created_at", "updated_at"]

    # -------------------------
    # Upload images to Cloudinary
    # -------------------------
    def _upload_files(self, files, instance=None):
        urls = instance.images if instance else []
        for f in files:
            result = upload(f, folder="job_images")
            urls.append(result["secure_url"])
        return urls

    # -------------------------
    # Create job
    # -------------------------
    def create(self, validated_data):
        request = self.context.get("request")
        client = request.user

        landscaper_id = validated_data.pop("landscaper_id", None)
        landscaper = None
        if landscaper_id:
            landscaper = get_object_or_404(User, id=landscaper_id, role="landscaper")

        property_id = validated_data.pop("property_id")
        property_obj = get_object_or_404(Property, id=property_id)

        files = validated_data.pop("images", [])

        job = Job.objects.create(
            landscaper=landscaper,
            client=client,
            property=property_obj,
            **validated_data
        )

        if files:
            job.images = self._upload_files(files)
            job.save()

        return job

    # -------------------------
    # Update job
    # -------------------------
    def update(self, instance, validated_data):
        files = validated_data.pop("images", [])

        # Update fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        # Append new images if any
        if files:
            instance.images += self._upload_files(files, instance=instance)

        instance.save()
        return instance
