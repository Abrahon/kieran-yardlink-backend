from rest_framework import serializers
from quickbooks.models import QuickBooksConnection, QuickBooksSyncLog


class QuickBooksConnectionSerializer(serializers.ModelSerializer):
    landscaper_id = serializers.IntegerField(source="landscaper.id", read_only=True)
    landscaper_business_name = serializers.CharField(
        source="landscaper.business_name",
        read_only=True
    )

    class Meta:
        model = QuickBooksConnection
        fields = [
            "id",
            "landscaper_id",
            "landscaper_business_name",
            "realm_id",
            "default_service_item_id",
            "default_service_item_name",
            "default_deposit_account_id",
            "default_deposit_account_name",
            "company_name",
            "is_active",
            "connected_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "landscaper_id",
            "landscaper_business_name",
            "realm_id",
            "company_name",
            "is_active",
            "connected_at",
            "updated_at",
        ]


class QuickBooksConnectionConfigUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuickBooksConnection
        fields = [
            "default_service_item_id",
            "default_service_item_name",
            "default_deposit_account_id",
            "default_deposit_account_name",
        ]

    def validate(self, attrs):
        service_item_id = attrs.get("default_service_item_id")
        service_item_name = attrs.get("default_service_item_name")

        deposit_account_id = attrs.get("default_deposit_account_id")
        deposit_account_name = attrs.get("default_deposit_account_name")

        if service_item_id and not service_item_name:
            raise serializers.ValidationError({
                "default_service_item_name": "Service item name is required when service item id is provided."
            })

        if service_item_name and not service_item_id:
            raise serializers.ValidationError({
                "default_service_item_id": "Service item id is required when service item name is provided."
            })

        if deposit_account_id and not deposit_account_name:
            raise serializers.ValidationError({
                "default_deposit_account_name": "Deposit account name is required when deposit account id is provided."
            })

        if deposit_account_name and not deposit_account_id:
            raise serializers.ValidationError({
                "default_deposit_account_id": "Deposit account id is required when deposit account name is provided."
            })

        return attrs


class QuickBooksSyncLogSerializer(serializers.ModelSerializer):
    connection_id = serializers.IntegerField(source="connection.id", read_only=True)
    invoice_id = serializers.IntegerField(source="invoice.id", read_only=True)
    invoice_number = serializers.CharField(source="invoice.invoice_number", read_only=True)
    landscaper_business_name = serializers.CharField(
        source="connection.landscaper.business_name",
        read_only=True
    )

    class Meta:
        model = QuickBooksSyncLog
        fields = [
            "id",
            "connection_id",
            "landscaper_business_name",
            "invoice_id",
            "invoice_number",
            "object_type",
            "object_id_in_qbo",
            "status",
            "request_payload",
            "response_payload",
            "error_message",
            "created_at",
        ]
        read_only_fields = fields