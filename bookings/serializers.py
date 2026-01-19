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
