from rest_framework import serializers
from .models import Property
from .enums import GrassTypeChoices
from rest_framework import serializers
from .models import PropertyPhot

class PropertySerializer(serializers.ModelSerializer):
    grass_types = serializers.ListField(
        child=serializers.ChoiceField(choices=GrassTypeChoices.choices)
    )

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
        ]


o



class PropertyPhotoSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = PropertyPhoto
        fields = ["id", "image_url", "uploaded_at"]

    # def get_image_url(self, obj):
    #     return obj.image.url


    def get_image_url(self, obj):
        if not obj.image:
            return None
        return obj.image.url
