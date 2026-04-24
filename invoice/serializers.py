
from rest_framework import serializers
from invoice.models import Invoice, InvoiceLineItem


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
            "service_fee_percent",
            "service_fee_amount",
            "net_amount",
            "total",
            "notes",
            "sent_to_email",
            "stripe_checkout_url",
            "stripe_session_id",
            "quickbooks_customer_id",
            "quickbooks_invoice_id",
            "quickbooks_payment_id",
            "client_email",
            "client_name",
            "property_address",
            "line_items",
            "paid_at",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "invoice_number",
            "issued_at",
            "subtotal",
            "service_fee_percent",
            "service_fee_amount",
            "net_amount",
            "total",
            "stripe_checkout_url",
            "stripe_session_id",
            "quickbooks_customer_id",
            "quickbooks_invoice_id",
            "quickbooks_payment_id",
            "paid_at",
            "created_at",
            "updated_at",
        ]

    def get_client_email(self, obj):
        if getattr(obj.job, "client", None) and getattr(obj.job.client, "user", None):
            return obj.job.client.user.email

        if getattr(obj.job, "external_client", None):
            return obj.job.external_client.email

        return obj.sent_to_email

    def get_client_name(self, obj):
        if getattr(obj.job, "external_client", None):
            return obj.job.external_client.name

        if getattr(obj.job, "client", None):
            user = getattr(obj.job.client, "user", None)

            # prefer real user name
            if user and getattr(user, "name", None):
                return user.name

            # fallback first_name + last_name
            if user:
                name = f"{getattr(user, 'first_name', '')} {getattr(user, 'last_name', '')}".strip()
                if name:
                    return name

            # fallback client profile name if not generic
            if getattr(obj.job.client, "name", None) and obj.job.client.name != "Client":
                return obj.job.client.name

        return "Client"

    def get_property_address(self, obj):
        return str(obj.job.job_property) if obj.job and obj.job.job_property else None