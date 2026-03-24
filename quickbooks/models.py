from django.db import models
from django.conf import settings
from landscapers.models import BusinessProfile
from invoice.models import Invoice


class QuickBooksConnection(models.Model):
    landscaper = models.OneToOneField(
        BusinessProfile,
        on_delete=models.CASCADE,
        related_name="quickbooks_connection"
    )

    realm_id = models.CharField(max_length=100, db_index=True)

    access_token_encrypted = models.TextField()
    refresh_token_encrypted = models.TextField()

    access_token_expires_at = models.DateTimeField(null=True, blank=True)
    refresh_token_expires_at = models.DateTimeField(null=True, blank=True)

    default_service_item_id = models.CharField(max_length=100, null=True, blank=True)
    default_service_item_name = models.CharField(max_length=255, null=True, blank=True)

    default_deposit_account_id = models.CharField(max_length=100, null=True, blank=True)
    default_deposit_account_name = models.CharField(max_length=255, null=True, blank=True)


    connected_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    # optional profile data
    company_name = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return f"QBO Connection - {self.landscaper.business_name}"


class QuickBooksSyncLog(models.Model):
    class ObjectType(models.TextChoices):
        CUSTOMER = "customer", "Customer"
        INVOICE = "invoice", "Invoice"
        PAYMENT = "payment", "Payment"

    class Status(models.TextChoices):
        SUCCESS = "success", "Success"
        FAILED = "failed", "Failed"

    connection = models.ForeignKey(
        QuickBooksConnection,
        on_delete=models.CASCADE,
        related_name="sync_logs"
    )
    invoice = models.ForeignKey(
        Invoice,
        on_delete=models.CASCADE,
        related_name="quickbooks_sync_logs",
        null=True,
        blank=True
    )

    object_type = models.CharField(max_length=20, choices=ObjectType.choices)
    object_id_in_qbo = models.CharField(max_length=100, blank=True, null=True)
    status = models.CharField(max_length=20, choices=Status.choices)

    request_payload = models.JSONField(null=True, blank=True)
    response_payload = models.JSONField(null=True, blank=True)
    error_message = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.object_type} - {self.status}"





class QuickBooksOAuthState(models.Model):
    landscaper = models.ForeignKey(
        BusinessProfile,
        on_delete=models.CASCADE,
        related_name="quickbooks_oauth_states"
    )
    state = models.CharField(max_length=255, unique=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_used = models.BooleanField(default=False)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.landscaper.business_name} - {self.state}"