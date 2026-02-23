# chat/serializers.py
from django.conf import settings
from rest_framework import serializers
from .models import Message, ChatThread
from django.core.files.uploadedfile import UploadedFile
import imghdr
import os

ALLOWED_EXTENSIONS = getattr(settings, "CHAT_ALLOWED_FILE_EXTENSIONS", ['.jpg', '.jpeg', '.png', '.gif', '.pdf', '.docx', '.xlsx'])
MAX_UPLOAD_SIZE = getattr(settings, "CHAT_MAX_UPLOAD_SIZE", 8 * 1024 * 1024) 



def get_extension(filename: str) -> str:
    return os.path.splitext(filename)[1].lower()


def is_image_file(uploaded_file: UploadedFile) -> bool:
    """
    Basic image check using imghdr — it's conservative but helps.
    For production you may want to use python-magic lib for better detection.
    """
    try:
        # imghdr.what() requires a file-like object with read() and seek()
        uploaded_file.seek(0)
        kind = imghdr.what(uploaded_file)
        uploaded_file.seek(0)
        return kind is not None
    except Exception:
        return False


class MessageSerializer(serializers.ModelSerializer):
    sender = serializers.PrimaryKeyRelatedField(read_only=True)
    file_url = serializers.SerializerMethodField(read_only=True)
    message_type = serializers.ReadOnlyField()

    class Meta:
        model = Mes sage
        fields = [
            'id',
            'thread',
            'sender',
            'text',
            'file',          # upload only
            'file_url',      # response only
            'message_type',
            'created_at',
            'updated_at',
            'is_deleted',
        ]
        read_only_fields = [
            'id',
            'sender',
            'file_url',
            'message_type',
            'created_at',
            'updated_at',
            'is_deleted',
        ]
        extra_kwargs = {
            'file': {'write_only': True}  # 🔥 THIS FIXES CLOUDINARY ERROR
        }

    def get_file_url(self, obj):
        if not obj.file:
            return None
        try:
            request = self.context.get('request')
            url = obj.file.url
            return request.build_absolute_uri(url) if request else url
        except Exception:
            return None


class ChatThreadSerializer(serializers.ModelSerializer):
    """
    Serializer for ChatThread model.
    - Provide creation validation so a duplicate thread between same users is not created.
    - Expose embedded last message optionally (read-only).
    """
    # If you want nested participant info you can expand these fields
    client = serializers.PrimaryKeyRelatedField(queryset=ChatThread._meta.get_field('client').related_model.objects.all())
    landscaper = serializers.PrimaryKeyRelatedField(queryset=ChatThread._meta.get_field('landscaper').related_model.objects.all())
    last_message = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = ChatThread
        fields = ['id', 'client', 'landscaper', 'created_at', 'last_message']
        read_only_fields = ['id', 'created_at', 'last_message']

    def validate(self, attrs):
        client = attrs.get('client')
        landscaper = attrs.get('landscaper')

        if client == landscaper:
            raise serializers.ValidationError("client and landscaper must be different users.")

        # Optionally: enforce that both users exist and have correct roles (if you have role system)
        # e.g., if you have User.role and want landscaper.role == 'landscaper' enforce here.

        return attrs

    def create(self, validated_data):
        """
        Create a single thread between client & landscaper if not exists.
        """
        client = validated_data.get('client')
        landscaper = validated_data.get('landscaper')

        # Avoid duplicate threads — change the query according to your schema/indexes
        existing = ChatThread.objects.filter(client=client, landscaper=landscaper).first()
        if existing:
            return existing

        thread = ChatThread.objects.create(client=client, landscaper=landscaper)
        return thread

    def get_last_message(self, obj):
        last = obj.messages.order_by('-created_at').first()
        if not last:
            return None
        # use MessageSerializer to represent last message; must pass context
        return MessageSerializer(last, context=self.context).data
