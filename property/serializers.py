from rest_framework import serializers
from .models import Property

class PropertySerializer(serializers.ModelSerializer):
    # First image for quick display
    image = serializers.SerializerMethodField()
    # Full list of images
    images = serializers.ListField(child=serializers.CharField(), read_only=True)

    class Meta:
        model = Property
        fields = [
            "id",
            "address",
            "latitude",
            "longitude",
            "property_size",
            "cut_height_inches",
            "grass_types",
            "notes",
            "is_active", 
            "image",   # first image
            "images",  # full array
            "created_at",
        ]

    def get_image(self, obj):
        if isinstance(obj.images, list) and obj.images:
            return obj.images[0]  # first image only
        return None
