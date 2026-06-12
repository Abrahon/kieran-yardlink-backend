
from django.urls import path
from quickbooks.views import (
    quickbooks_connect,
    quickbooks_callback,
    quickbooks_connection_detail,
    quickbooks_update_config,
    quickbooks_service_items,
    quickbooks_deposit_accounts,
    quickbooks_sync_logs,
    quickbooks_sync_invoice,
    quickbooks_success,
    QuickBooksDisconnectAPIView,
    quickbooks_sync_log_detail_pdf
)


urlpatterns = [
    path("quickbooks/connect/", quickbooks_connect, name="quickbooks-connect"),
    path("quickbooks/callback/", quickbooks_callback, name="quickbooks-callback"),
    path("quickbooks-connected-success/",quickbooks_success,name="quickbooks_success"),

    path("quickbooks/config/", quickbooks_connection_detail, name="quickbooks-config-detail"),
    path("quickbooks/config/update/", quickbooks_update_config, name="quickbooks-config-update"),

    path("quickbooks/service-items/", quickbooks_service_items, name="quickbooks-service-items"),
    path("quickbooks/deposit-accounts/", quickbooks_deposit_accounts, name="quickbooks-deposit-accounts"),

    path("quickbooks/logs/", quickbooks_sync_logs, name="quickbooks-sync-logs"),
    path("api/quickbooks/sync-logs/pdf/",quickbooks_sync_log_detail_pdf,name="quickbooks-sync-logs-pdf"),

    path("quickbooks/invoices/<int:invoice_id>/sync/", quickbooks_sync_invoice, name="quickbooks-sync-invoice"),
    
    path("quickbooks/disconnect/",QuickBooksDisconnectAPIView.as_view(),name="quickbooks-disconnect" ),
]