# bookings/serializers.py
from rest_framework import serializers
from .models import ServiceBooking
from django.utils import timezone
import datetime

class ServiceBookingRescheduleSerializer(serializers.ModelSerializer):
    class Meta:
        model = ServiceBooking
        fields = ["scheduled_date", "scheduled_time"]

    def validate(self, data):
        scheduled_date = data.get("scheduled_date")
        scheduled_time = data.get("scheduled_time")

        if scheduled_date and scheduled_date < timezone.now().date():
            raise serializers.ValidationError("Scheduled date cannot be in the past.")

        if scheduled_date == timezone.now().date() and scheduled_time and scheduled_time < timezone.now().time():
            raise serializers.ValidationError("Scheduled time cannot be in the past.")

        return data

# update serializers
from rest_framework import serializers
from .models import BookingRequest, BookingAddon
from property.models import Property
from services.models import Service, Addon
from django.utils import timezone


class BookingRequestSerializer(serializers.ModelSerializer):
    client = serializers.ReadOnlyField(source="client.id")
    addons = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Addon.objects.all(),
        required=False
    )

    class Meta:
        model = BookingRequest
        fields = [
            "id",
            "client",
            "property",
            "service",
            "description",
            "booking_type",
            "recurring_day_of_week",
            "scheduled_date",
            "scheduled_time",
            "addons",
            "price",
            "landscaper",
            "status",
            "note",
            "created_at",
            "updated_at"
        ]
        read_only_fields = [
            "id", "client", "landscaper", "price", "status",
            "created_at", "updated_at"
        ]

    def validate(self, attrs):
        booking_type = attrs.get("booking_type")
        service = attrs.get("service")
        description = attrs.get("description")
        scheduled_date = attrs.get("scheduled_date")
        scheduled_time = attrs.get("scheduled_time")
        recurring_day = attrs.get("recurring_day_of_week")

        if booking_type in ["one_time", "weekly", "biweekly"] and not service:
            raise serializers.ValidationError("Service is required for standard bookings.")

        if booking_type == "custom" and not description:
            raise serializers.ValidationError("Description is required for custom bookings.")

        if booking_type == "one_time" and (not scheduled_date or not scheduled_time):
            raise serializers.ValidationError("Scheduled date and time required for one-time bookings.")

        if booking_type in ["weekly", "biweekly"] and not recurring_day:
            raise serializers.ValidationError("Recurring day is required for weekly/biweekly bookings.")

        return attrs
