from rest_framework import serializers
# from bookings.models import ServiceBooking
from services.models import ServiceSchedule
from profiles.models import LandscaperProfilies, ClientProfile

class PaymentHistorySerializer(serializers.ModelSerializer):
    client_name = serializers.CharField(source='client.user.name')
    client_email = serializers.CharField(source='client.user.email')
    landscaper_name = serializers.CharField(source='landscaper.name')
    service_name = serializers.CharField(source='service.name')
    property_address = serializers.SerializerMethodField()

    class Meta:
        model = ServiceSchedule
        fields = [
            'id', 'client_name', 'client_email', 'landscaper_name', 'service_name',
            'property_address', 'scheduled_date', 'scheduled_time', 'payment_status', 'stripe_payment_id'
        ]

    def get_property_address(self, obj):
        """
        Returns the first property address of the client.
        """
        user = getattr(obj.client, 'user', None)
        if user:
            prop = user.properties.first()  # use the related_name from Property model
            if prop:
                return prop.address
        return ""



# class PaymentHistorySerializer(serializers.ModelSerializer):
#     client_name = serializers.CharField(source='client.user.name')
#     client_email = serializers.CharField(source='client.user.email')
#     landscaper_name = serializers.CharField(source='landscaper.name')
#     service_name = serializers.CharField(source='service.name')
#     property_address = serializers.SerializerMethodField()
#     amount_paid = serializers.SerializerMethodField()
#     platform_fee = serializers.SerializerMethodField()
#     landscaper_earning = serializers.SerializerMethodField()

#     class Meta:
#         model = ServiceSchedule
#         fields = [
#             'id', 'client_name', 'client_email', 'landscaper_name', 'service_name',
#             'property_address', 'scheduled_date', 'scheduled_time',
#             'payment_status', 'stripe_payment_id',
#             'amount_paid', 'platform_fee', 'landscaper_earning'
#         ]

#     def get_property_address(self, obj):
#         prop = obj.client.properties.first()
#         return prop.address if prop else ""

#     def get_amount_paid(self, obj):
#         return float(obj.service.price)

#     def get_platform_fee(self, obj):
#         return round(obj.service.price * 0.02, 2)

#     def get_landscaper_earning(self, obj):
#         return round(obj.service.price * 0.98, 2)
