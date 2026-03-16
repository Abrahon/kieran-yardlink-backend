from rest_framework import serializers
from invoices.models import Invoice, InvoiceLineItem


class InvoiceLineItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = InvoiceLineItem
        fields = [
            "id",
            "item_type",
            "name",
            "description",
            "unit_price",
            "quantity",
            "line_total",
        ]


class InvoiceSerializer(serializers.ModelSerializer):
    line_items = InvoiceLineItemSerializer(many=True, read_only=True)
    client_email = serializers.SerializerMethodField()
    client_name = serializers.SerializerMethodField()
    job_id = serializers.IntegerField(source="job.id", read_only=True)
    property_address = serializers.SerializerMethodField()

    class Meta:
        model = Invoice
        fields = [
            "id",
            "job_id",
            "invoice_number",
            "status",
            "issued_at",
            "due_at",
            "subtotal",
            "total",
            "notes",
            "stripe_checkout_url",
            "client_email",
            "client_name",
            "property_address",
            "line_items",
            "paid_at",
        ]

    def get_client_email(self, obj):
        return obj.job.client.user.email if obj.job and obj.job.client and obj.job.client.user else None

    def get_client_name(self, obj):
        profile = obj.job.client
        return getattr(profile, "name", None) if profile else None

    def get_property_address(self, obj):
        return str(obj.job.job_property) if obj.job and obj.job.job_property else None