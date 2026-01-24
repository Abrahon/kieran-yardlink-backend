from rest_framework import serializers
from .models import Job
from cloudinary.uploader import upload

class JobSerializer(serializers.ModelSerializer):
    images = serializers.ListField(
        child=serializers.URLField(),
        required=False
    )

    class Meta:
        model = Job
        fields = [
            "id",
            "landscaper",
            "client",
            "property",
            "date",
            "start_time",
            "end_time",
            "status",
            "final_price",
            "is_reduced",
            "images",  # Single field for both upload & response
            "notes",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def to_internal_value(self, data):
        """
        If images are files (not URLs), upload them to Cloudinary
        and replace with URLs in the data before validation.
        """
        images = data.get("images", [])
        uploaded_urls = []

        # Check if any items are file objects
        for img in images:
            if hasattr(img, "read"):  # It's a file
                result = upload(img, folder="job_images")
                uploaded_urls.append(result["secure_url"])
            else:
                uploaded_urls.append(img)  # Already a URL

        data["images"] = uploaded_urls
        return super().to_internal_value(data)
