from django.urls import path
from invoice.views import (
    ClientInvoiceListView,
    ClientInvoiceDetailView,
    create_job_invoice,
    send_job_invoice,
    mark_invoice_paid,
    regenerate_invoice_checkout
)

urlpatterns = [
    path("client/invoices/", ClientInvoiceListView.as_view(), name="client-invoice-list"),
    path("client/invoices/<int:id>/", ClientInvoiceDetailView.as_view(), name="client-invoice-detail"),

    path("landscaper/jobs/<int:job_id>/invoice/create/", create_job_invoice, name="create-job-invoice"),
    path("landscaper/invoices/<int:invoice_id>/regenerate-checkout/", regenerate_invoice_checkout, name="regenerate-invoice-checkout"),
    path("landscaper/invoices/<int:invoice_id>/send/", send_job_invoice, name="send-job-invoice"),

    # optional manual mark paid, or call this from Stripe webhook
    path("invoices/<int:invoice_id>/mark-paid/", mark_invoice_paid, name="mark-invoice-paid"),
]