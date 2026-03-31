
# from rest_framework import serializers
# from invoice.models import Invoice

# class PaymentHistorySerializer(serializers.ModelSerializer):
#     invoice_id = serializers.IntegerField(source="id", read_only=True)
#     invoice_number = serializers.CharField(read_only=True)

#     client_name = serializers.SerializerMethodField()
#     client_email = serializers.SerializerMethodField()

#     landscaper_name = serializers.SerializerMethodField()
#     landscaper_email = serializers.SerializerMethodField()

#     property_address = serializers.SerializerMethodField()
#     completed_at = serializers.SerializerMethodField()
#     completed_items = serializers.SerializerMethodField()

#     payment_status = serializers.CharField(source="status", read_only=True)
#     stripe_payment_id = serializers.CharField(source="stripe_session_id", read_only=True)
#     total_amount = serializers.SerializerMethodField()
#     job_id = serializers.IntegerField(source="job.id", read_only=True)
#     booking_price = serializers.SerializerMethodField()
#     pay_url = serializers.CharField(source="stripe_checkout_url", read_only=True)

#     class Meta:
#         model = Invoice
#         fields = [
#             "invoice_id",
#             "invoice_number",
#             "job_id",
#             "client_name",
#             "client_email",
#             "landscaper_name",
#             "landscaper_email",
#             "property_address",
#             "completed_at",
#             "payment_status",
#             "completed_items",
#             "stripe_payment_id",
#             "booking_price",
#             "total_amount",
#             "pay_url",
#             "issued_at",
#             "due_at",
#             "paid_at",
#         ]

#     def get_client_name(self, obj):
#         client = getattr(obj.job, "client", None)
#         if not client:
#             return "Unknown Client"
#         return getattr(client, "name", None) or getattr(client.user, "name", "Unknown Client")

#     def get_client_email(self, obj):
#         client = getattr(obj.job, "client", None)
#         if client and getattr(client, "user", None):
#             return client.user.email
#         return ""

#     def get_landscaper_name(self, obj):
#         business = getattr(obj.job, "landscaper", None)
#         if not business:
#             return "Unknown Landscaper"

#         personal = getattr(business.user, "landscaperprofilies", None)
#         if personal and personal.name:
#             return personal.name

#         return business.business_name or "Unknown Landscaper"

#     def get_landscaper_email(self, obj):
#         business = getattr(obj.job, "landscaper", None)
#         if business and getattr(business, "user", None):
#             return business.user.email
#         return ""

#     def get_property_address(self, obj):
#         job_property = getattr(obj.job, "job_property", None)
#         return str(job_property) if job_property else ""

#     def get_completed_at(self, obj):
#         completed_at = getattr(obj.job, "completed_at", None)
#         if completed_at:
#             return completed_at.strftime("%Y-%m-%d %H:%M:%S")
#         return None

#     def get_completed_items(self, obj):
#         job = getattr(obj, "job", None)
#         if not job:
#             return []

#         return [
#             {
#                 "id": item.id,
#                 "item_type": item.item_type,
#                 "name": item.name,
#                 "description": item.description,
#                 "price": round(float(item.price or 0), 2),
#                 "is_completed": item.is_completed,
#             }
#             for item in job.items.filter(is_completed=True).order_by("sort_order", "id")
#         ]

#     def get_booking_price(self, obj):
#         job = getattr(obj, "job", None)
#         booking = getattr(job, "booking", None)
#         if booking and booking.price is not None:
#             return round(float(booking.price), 2)
#         return 0.0

#     def get_total_amount(self, obj):
#         return round(float(obj.total or 0), 2)

from rest_framework import serializers
from invoice.models import Invoice


class PaymentHistorySerializer(serializers.ModelSerializer):
    invoice_id = serializers.IntegerField(source="id", read_only=True)
    invoice_number = serializers.CharField(read_only=True)

    client_name = serializers.SerializerMethodField()
    client_email = serializers.SerializerMethodField()

    landscaper_name = serializers.SerializerMethodField()
    landscaper_email = serializers.SerializerMethodField()

    property_address = serializers.SerializerMethodField()
    completed_at = serializers.SerializerMethodField()
    completed_items = serializers.SerializerMethodField()

    payment_status = serializers.CharField(source="status", read_only=True)
    stripe_payment_id = serializers.CharField(source="stripe_session_id", read_only=True)
    total_amount = serializers.SerializerMethodField()
    job_id = serializers.IntegerField(source="job.id", read_only=True)
    booking_price = serializers.SerializerMethodField()
    pay_url = serializers.CharField(source="stripe_checkout_url", read_only=True)

    class Meta:
        model = Invoice
        fields = [
            "invoice_id",
            "invoice_number",
            "job_id",
            "client_name",
            "client_email",
            "landscaper_name",
            "landscaper_email",
            "property_address",
            "completed_at",
            "payment_status",
            "completed_items",
            "stripe_payment_id",
            "booking_price",
            "total_amount",
            "pay_url",
            "issued_at",
            "due_at",
            "paid_at",
        ]

    def get_client_name(self, obj):
        job = getattr(obj, "job", None)
        client = getattr(job, "client", None)
        external_client = getattr(job, "external_client", None)

        if client:
            return getattr(client.user, "name", None) or getattr(client.user, "email", "Unknown Client")
        if external_client:
            return external_client.name or "Unknown Client"
        return "Unknown Client"

    def get_client_email(self, obj):
        job = getattr(obj, "job", None)
        client = getattr(job, "client", None)
        external_client = getattr(job, "external_client", None)

        if client and getattr(client, "user", None):
            return client.user.email
        if external_client:
            return external_client.email or ""
        return ""

    def get_landscaper_name(self, obj):
        job = getattr(obj, "job", None)
        business = getattr(job, "landscaper", None)

        if not business:
            return "Unknown Landscaper"

        if getattr(business, "business_name", None):
            return business.business_name

        if getattr(business, "user", None):
            return getattr(business.user, "name", "Unknown Landscaper")

        return "Unknown Landscaper"

    def get_landscaper_email(self, obj):
        job = getattr(obj, "job", None)
        business = getattr(job, "landscaper", None)

        if business and getattr(business, "user", None):
            return business.user.email
        return ""

    def get_property_address(self, obj):
        job = getattr(obj, "job", None)
        job_property = getattr(job, "job_property", None)
        return str(job_property) if job_property else ""

    def get_completed_at(self, obj):
        job = getattr(obj, "job", None)
        completed_at = getattr(job, "completed_at", None)
        if completed_at:
            return completed_at.strftime("%Y-%m-%d %H:%M:%S")
        return None

    def get_completed_items(self, obj):
        job = getattr(obj, "job", None)
        if not job:
            return []

        return [
            {
                "id": item.id,
                "item_type": item.item_type,
                "name": item.name,
                "description": item.description,
                "price": round(float(item.price or 0), 2),
                "is_completed": item.is_completed,
            }
            for item in job.items.filter(is_completed=True).order_by("sort_order", "id")
        ]

    def get_booking_price(self, obj):
        job = getattr(obj, "job", None)
        booking = getattr(job, "booking", None)
        if booking and booking.price is not None:
            return round(float(booking.price), 2)
        return 0.0

    def get_total_amount(self, obj):
        return round(float(obj.total or 0), 2)