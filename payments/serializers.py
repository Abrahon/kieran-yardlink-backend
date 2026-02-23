# from rest_framework import serializers
# # from bookings.models import ServiceBooking
# from services.models import ServiceSchedule
# from profiles.models import LandscaperProfilies, ClientProfile
# from services.serializers import CompletedServiceSerializer

# class PaymentHistorySerializer(serializers.ModelSerializer):
#     client_name = serializers.CharField(source='client.user.name')
#     client_email = serializers.CharField(source='client.user.email')
#     landscaper_name = serializers.CharField(source='landscaper.name')
#     service_name = serializers.CharField(source='service.name')
#     property_address = serializers.SerializerMethodField()
#     completed_services = CompletedServiceSerializer(many=True, read_only=True)  # if you want nested services

#     class Meta:
#         model = ServiceSchedule
#         fields = [
#             'id', 'client_name', 'client_email', 'landscaper_name', 'service_name',
#             'property_address', 'scheduled_date', 'scheduled_time', 'payment_status', "completed_services",  'stripe_payment_id'
#         ]

#     def get_property_address(self, obj):
#         """
#         Returns the first property address of the client.
#         """
#         user = getattr(obj.client, 'user', None)
#         if user:
#             prop = user.properties.first()  # use the related_name from Property model
#             if prop:
#                 return prop.address
#         return ""
    
#     def get_total_amount(self, obj):
#         # use annotated paid_amount if exists, else calculate
#         if hasattr(obj, "paid_amount"):
#             return round(obj.paid_amount, 2)
#         return round(obj.service.price * 1.02, 2)


# from rest_framework import serializers
# from services.models import ServiceSchedule
# from profiles.models import LandscaperProfilies, ClientProfile
# from services.serializers import CompletedServiceSerializer

# class PaymentHistorySerializer(serializers.ModelSerializer):
#     client_name = serializers.CharField(source='client.user.name')
#     client_email = serializers.CharField(source='client.user.email')
#     landscaper_name = serializers.CharField(source='landscaper.name')
#     service_name = serializers.CharField(source='service.name')
#     property_address = serializers.SerializerMethodField()
#     completed_services = CompletedServiceSerializer(many=True, read_only=True)  # nested services
#     total_amount = serializers.SerializerMethodField()  

#     class Meta:
#         model = ServiceSchedule
#         fields = [
#             'id', 'client_name', 'client_email', 'landscaper_name', 'service_name',
#             'property_address', 'scheduled_date', 'scheduled_time', 'payment_status',
#             'completed_services', 'stripe_payment_id', 'total_amount'  # include total_amount here
#         ]

#     def get_property_address(self, obj):
#         """
#         Returns the first property address of the client.
#         """
#         user = getattr(obj.client, 'user', None)
#         if user:
#             prop = user.properties.first()  
#             if prop:
#                 return prop.address
#         return ""

#     def get_total_amount(self, obj):
#         """
#         Returns the total paid amount for this job, including 2% markup.
#         """
#         if hasattr(obj, "paid_amount"):
#             return round(obj.paid_amount, 2)
#         # fallback to service price if annotation not present
#         return round(obj.service.price * 1.02, 2)
from rest_framework import serializers
from services.models import ServiceSchedule
from profiles.models import LandscaperProfilies, ClientProfile
from services.serializers import CompletedServiceSerializer

class PaymentHistorySerializer(serializers.ModelSerializer):
    client_name = serializers.SerializerMethodField()
    client_email = serializers.SerializerMethodField()
    landscaper_name = serializers.SerializerMethodField()
    service_name = serializers.CharField(source='service.name', default="")
    property_address = serializers.SerializerMethodField()
    completed_services = CompletedServiceSerializer(many=True, read_only=True)
    total_amount = serializers.SerializerMethodField()

    class Meta:
        model = ServiceSchedule
        fields = [
            'id',
            'client_name',
            'client_email',
            'landscaper_name',
            'service_name',
            # 'service_price',
            'property_address',
            'scheduled_date',
            'scheduled_time',
            'payment_status',
            'completed_services',
            'stripe_payment_id',
            'total_amount',
        ]

    def get_client_name(self, obj):
        """
        Returns the full name of the client safely.
        """
        client_user = getattr(obj.client, "user", None)
        if client_user:
            return getattr(client_user, "name", "Unknown Client")
        return "Unknown Client"

    def get_client_email(self, obj):
        """
        Returns the email of the client safely.
        """
        client_user = getattr(obj.client, "user", None)
        if client_user:
            return getattr(client_user, "email", "")
        return ""

    def get_landscaper_name(self, obj):
        """
        Returns the full name of the landscaper safely.
        """
        landscaper = getattr(obj, "landscaper", None)
        if landscaper:
            return getattr(landscaper, "name", "Unknown Landscaper")
        return "Unknown Landscaper"

    def get_property_address(self, obj):
        """
        Returns the first property address of the client, or empty string if none.
        """
        client_user = getattr(obj.client, "user", None)
        if client_user:
            prop = getattr(client_user, "properties", None)
            if prop:
                first_property = prop.first()
                if first_property:
                    return getattr(first_property, "address", "")
        return ""

    def get_total_amount(self, obj):
        """
        Returns the total paid amount for this job, including 2% markup if no paid_amount exists.
        """
        if hasattr(obj, "paid_amount") and obj.paid_amount is not None:
            return round(float(obj.paid_amount), 2)
        if getattr(obj, "service", None) and getattr(obj.service, "price", None) is not None:
            return round(float(obj.service.price) * 1.02, 2)
        return 0.0