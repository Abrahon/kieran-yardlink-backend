
import secrets
from datetime import timedelta

from django.shortcuts import redirect
from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from landscapers.models import BusinessProfile
from invoice.models import Invoice
from quickbooks.crypto import encrypt_text
from quickbooks.models import QuickBooksConnection, QuickBooksSyncLog
from quickbooks.serializers import (
    QuickBooksConnectionSerializer,
    QuickBooksConnectionConfigUpdateSerializer,
    QuickBooksSyncLogSerializer,
)
from quickbooks.services import (
    build_authorization_url,
    exchange_code_for_tokens,
    qbo_query,
    upsert_customer,
    create_invoice as qbo_create_invoice,
    create_payment as qbo_create_payment,
)
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import A4
from io import BytesIO
from django.http import HttpResponse
import json

from rest_framework.views import APIView
import secrets
from datetime import timedelta

from django.shortcuts import redirect
from django.utils import timezone
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework import status
from quickbooks.helpers import get_active_qb_connection
from landscapers.models import BusinessProfile
from quickbooks.crypto import encrypt_text
from quickbooks.models import QuickBooksConnection,QuickBooksOAuthState,QuickBooksSyncLog
from quickbooks.services import build_authorization_url, exchange_code_for_tokens
from subscriptions.helpers import can_use_quickbooks 
from django.shortcuts import render



@api_view(["GET"])
@permission_classes([IsAuthenticated])
def quickbooks_status_view(request):

    user = request.user

    connection = QuickBooksConnection.objects.filter(
        user=user,
        is_active=True
    ).first()

    # NOT CONNECTED
    if not connection:
        return Response({
            "connected": False,
            "company_name": None,
            "realm_id": None,
            "last_sync": None,
            "sync_status": "not_connected",
            "total_synced_invoices": 0
        })

    # last sync log
    last_log = QuickBooksSyncLog.objects.filter(
        user=user
    ).order_by("-created_at").first()

    total_synced = QuickBooksSyncLog.objects.filter(
        user=user,
        status="success"
    ).count()

    return Response({
        "connected": True,
        "company_name": connection.company_name,
        "realm_id": connection.realm_id,
        "sync_enabled": connection.sync_enabled,
        "created_at": connection.created_at,
        "last_sync": last_log.created_at if last_log else None,
        "last_sync_status": last_log.status if last_log else None,
        "total_synced_invoices": total_synced
    })



@api_view(["GET"])
@permission_classes([IsAuthenticated])
def quickbooks_connect(request):

    landscaper = getattr(request.user, "landscaper_profile", None)
    if not landscaper:
        return Response(
            {"error": "Landscaper profile not found."},
            status=status.HTTP_403_FORBIDDEN
        )

    #  ADD THIS CHECK HERE
    if not can_use_quickbooks(request.user):
        return Response(
            {"error": "QuickBooks integration is only available for Pro plan"},
            status=status.HTTP_403_FORBIDDEN
        )

    state = secrets.token_urlsafe(32)

    QuickBooksOAuthState.objects.create(
        landscaper=landscaper,
        state=state
    )

    return Response({
        "authorization_url": build_authorization_url(state)
    }, status=status.HTTP_200_OK)



# success page after quickbooks connection - can be used to show a nice message or redirect to app home
def quickbooks_success(request):
    return render(request, "quickbooks/success.html")


@api_view(["GET"])
@authentication_classes([])
@permission_classes([AllowAny])
def quickbooks_callback(request):
    state = request.GET.get("state")
    code = request.GET.get("code")
    realm_id = request.GET.get("realmId")

    if not state:
        return Response(
            {"error": "Missing state"},
            status=status.HTTP_400_BAD_REQUEST
        )

    if not code:
        return Response(
            {"error": "Missing authorization code"},
            status=status.HTTP_400_BAD_REQUEST
        )

    if not realm_id:
        return Response(
            {"error": "Missing realmId"},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        oauth_state = QuickBooksOAuthState.objects.select_related("landscaper").get(
            state=state,
            is_used=False
        )
    except QuickBooksOAuthState.DoesNotExist:
        return Response(
            {"error": "Invalid OAuth state"},
            status=status.HTTP_400_BAD_REQUEST
        )

    landscaper = oauth_state.landscaper

    try:
        payload = exchange_code_for_tokens(code)
    except Exception as e:
        return Response(
            {"error": f"QuickBooks token exchange failed: {str(e)}"},
            status=status.HTTP_400_BAD_REQUEST
        )

    QuickBooksConnection.objects.update_or_create(
        landscaper=landscaper,
        defaults={
            "realm_id": realm_id,
            "access_token_encrypted": encrypt_text(payload["access_token"]),
            "refresh_token_encrypted": encrypt_text(payload["refresh_token"]),
            "access_token_expires_at": timezone.now() + timedelta(seconds=payload.get("expires_in", 3600)),
            "refresh_token_expires_at": timezone.now() + timedelta(seconds=payload.get("x_refresh_token_expires_in", 86400)),
            "is_active": True,
        }
    )

    oauth_state.is_used = True
    oauth_state.save(update_fields=["is_used"])

    return redirect("/api/quickbooks-connected-success/")

# disconnect quickboos



class QuickBooksDisconnectAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        # Get landscaper profile from logged-in user
        landscaper = getattr(request.user, "landscaper_profile", None)

        if not landscaper:
            return Response(
                {"error": "Landscaper profile not found."},
                status=403
            )

        # Deactivate QuickBooks connection
        updated = QuickBooksConnection.objects.filter(
            landscaper=landscaper,
            is_active=True
        ).update(is_active=False)

        if updated == 0:
            return Response(
                {"message": "No active QuickBooks connection found."},
                status=404
            )

        return Response(
            {"message": "Disconnected successfully"},
            status=200
        )
        
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def quickbooks_connection_detail(request):
    landscaper = getattr(request.user, "landscaper_profile", None)
    if not landscaper:
        return Response(
            {"error": "Landscaper profile not found."},
            status=status.HTTP_403_FORBIDDEN
        )

    try:
        connection = QuickBooksConnection.objects.get(landscaper=landscaper)
    except QuickBooksConnection.DoesNotExist:
        return Response(
            {"error": "QuickBooks not connected."},
            status=status.HTTP_404_NOT_FOUND
        )

    return Response(
        QuickBooksConnectionSerializer(connection).data,
        status=status.HTTP_200_OK
    )


@api_view(["PATCH"])
@permission_classes([IsAuthenticated])
def quickbooks_update_config(request):
    landscaper = getattr(request.user, "landscaper_profile", None)
    if not landscaper:
        return Response(
            {"error": "Landscaper profile not found."},
            status=status.HTTP_403_FORBIDDEN
        )

    connection = get_active_qb_connection(request.user)

    if not connection:
        return Response(
            {"error": "QuickBooks not connected."},
            status=status.HTTP_404_NOT_FOUND
        )

    serializer = QuickBooksConnectionConfigUpdateSerializer(
        connection,
        data=request.data,
        partial=True
    )
    serializer.is_valid(raise_exception=True)
    serializer.save()

    return Response({
        "message": "QuickBooks default configuration updated successfully.",
        "data": QuickBooksConnectionSerializer(connection).data
    }, status=status.HTTP_200_OK)


# @api_view(["GET"])

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def quickbooks_service_items(request):

    landscaper = getattr(request.user, "landscaper_profile", None)
    if not landscaper:
        return Response(
            {"error": "Landscaper profile not found."},
            status=status.HTTP_403_FORBIDDEN
        )

    # =====================================
    # FIXED CONNECTION HANDLING (NEW)
    # =====================================
    connection = get_active_qb_connection(request.user)

    if not connection:
        return Response(
            {"error": "QuickBooks not connected."},
            status=status.HTTP_404_NOT_FOUND
        )
    connection = get_valid_connection(connection)  

    # =====================================
    # QUICKBOOKS QUERY
    # =====================================
    query = "select * from Item where Type = 'Service'"
    resp = qbo_query(connection, query)

    if not resp.ok:
        return Response(
            {"error": resp.text},
            status=status.HTTP_400_BAD_REQUEST
        )

    items = resp.json().get("QueryResponse", {}).get("Item", [])

    data = [
        {
            "id": item.get("Id"),
            "name": item.get("Name"),
            "type": item.get("Type"),
            "active": item.get("Active", True),
        }
        for item in items
    ]

    return Response({"items": data}, status=status.HTTP_200_OK)



@api_view(["GET"])
@permission_classes([IsAuthenticated])
def quickbooks_deposit_accounts(request):
    landscaper = getattr(request.user, "landscaper_profile", None)
    if not landscaper:
        return Response(
            {"error": "Landscaper profile not found."},
            status=status.HTTP_403_FORBIDDEN
        )

    connection = get_active_qb_connection(request.user)

    if not connection:
        return Response(
            {"error": "QuickBooks not connected."},
            status=status.HTTP_404_NOT_FOUND
        )
    connection = get_valid_connection(connection)  # ✅ ADD HERE

    query = "select * from Account"
    resp = qbo_query(connection, query)

    if not resp.ok:
        return Response(
            {"error": resp.text},
            status=status.HTTP_400_BAD_REQUEST
        )

    accounts = resp.json().get("QueryResponse", {}).get("Account", [])
    data = [
        {
            "id": account.get("Id"),
            "name": account.get("Name"),
            "account_type": account.get("AccountType"),
            "account_sub_type": account.get("AccountSubType"),
            "active": account.get("Active", True),
        }
        for account in accounts
        if account.get("AccountType") in ["Bank", "Other Current Asset"]
    ]

    return Response({"accounts": data}, status=status.HTTP_200_OK)



@api_view(["GET"])
@permission_classes([IsAuthenticated])
def quickbooks_sync_logs(request):
    landscaper = getattr(request.user, "landscaper_profile", None)
    if not landscaper:
        return Response(
            {"error": "Landscaper profile not found."},
            status=status.HTTP_403_FORBIDDEN
        )

    try:
        connection = QuickBooksConnection.objects.get(landscaper=landscaper)
    except QuickBooksConnection.DoesNotExist:
        return Response(
            {"error": "QuickBooks not connected."},
            status=status.HTTP_404_NOT_FOUND
        )

    logs = QuickBooksSyncLog.objects.filter(connection=connection).order_by("-created_at")
    serializer = QuickBooksSyncLogSerializer(logs, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)



# downlaod quiclbooks invoice
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def quickbooks_sync_log_detail_pdf(request, pk):

    landscaper = getattr(request.user, "landscaper_profile", None)
    if not landscaper:
        return Response({"error": "Landscaper profile not found."}, status=403)

    connection = get_active_qb_connection(request.user)

    if not connection:
        return Response(
            {"error": "QuickBooks not connected."},
            status=status.HTTP_404_NOT_FOUND
        )

    try:
        log = QuickBooksSyncLog.objects.get(id=pk, connection=connection)
    except QuickBooksSyncLog.DoesNotExist:
        return Response({"error": "Log not found."}, status=404)

    # =========================
    # PDF SETUP
    # =========================
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()

    elements = []

    # Title
    elements.append(Paragraph("QuickBooks Sync Log Detail", styles["Title"]))
    elements.append(Spacer(1, 12))

    # Basic Info
    elements.append(Paragraph(f"ID: {log.id}", styles["Normal"]))
    elements.append(Paragraph(f"Type: {log.object_type}", styles["Normal"]))
    elements.append(Paragraph(f"Status: {log.status}", styles["Normal"]))
    elements.append(Paragraph(f"Created: {log.created_at}", styles["Normal"]))
    elements.append(Spacer(1, 12))

    # =========================
    # REQUEST PAYLOAD
    # =========================
    elements.append(Paragraph("Request Payload:", styles["Heading2"]))
    elements.append(
        Paragraph(
            f"<pre>{json.dumps(log.request_payload, indent=2)}</pre>",
            styles["Code"]
        )
    )
    elements.append(Spacer(1, 12))

    # =========================
    # RESPONSE PAYLOAD
    # =========================
    elements.append(Paragraph("Response Payload:", styles["Heading2"]))
    elements.append(
        Paragraph(
            f"<pre>{json.dumps(log.response_payload, indent=2)}</pre>",
            styles["Code"]
        )
    )

    doc.build(elements)
    buffer.seek(0)

    response = HttpResponse(buffer, content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="quickbooks_log_{log.id}.pdf"'

    return response




@api_view(["POST"])
@permission_classes([IsAuthenticated])
def quickbooks_sync_invoice(request, invoice_id):

    landscaper = getattr(request.user, "landscaper_profile", None)
    if not landscaper:
        return Response(
            {"error": "Landscaper profile not found."},
            status=status.HTTP_403_FORBIDDEN
        )

    try:
        invoice = Invoice.objects.select_related(
            "job",
            "job__client",
            "job__client__user",
            "job__external_client",
            "job__landscaper",
        ).get(
            id=invoice_id,
            job__landscaper=landscaper
        )
    except Invoice.DoesNotExist:
        return Response(
            {"error": "Invoice not found."},
            status=status.HTTP_404_NOT_FOUND
        )
    connection = get_active_qb_connection(request.user)

    if not connection:
        return Response(
            {"error": "QuickBooks not connected."},
            status=status.HTTP_404_NOT_FOUND
        )
    connection = get_valid_connection(connection)  # ✅ ADD HERE

    # use request data first, fallback to saved defaults
    service_item_id = request.data.get("service_item_id") or connection.default_service_item_id
    deposit_to_account_id = request.data.get("deposit_to_account_id") or connection.default_deposit_account_id

    if not service_item_id:
        return Response(
            {"error": "service_item_id is required. Set it in request body or QuickBooks config."},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        customer = upsert_customer(connection, invoice)
        qbo_invoice = qbo_create_invoice(connection, invoice, customer["Id"], service_item_id)

        qbo_payment = None
        if invoice.status == Invoice.Status.PAID:
            if not deposit_to_account_id:
                return Response(
                    {"error": "deposit_to_account_id is required for paid invoice sync."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            qbo_payment = qbo_create_payment(
                connection,
                invoice,
                customer["Id"],
                qbo_invoice["Id"],
                deposit_to_account_id,
            )

    except Exception as e:
        return Response(
            {"error": str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )

    return Response({
        "message": "QuickBooks sync completed.",
        "customer_id": customer["Id"],
        "invoice_id": qbo_invoice["Id"],
        "payment_id": qbo_payment["Id"] if qbo_payment else None,
    }, status=status.HTTP_200_OK)