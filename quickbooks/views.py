
from cmath import log
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
from django.urls import reverse
from django.shortcuts import redirect
from .helpers import get_active_qb_connection, get_valid_connection

import json
from io import BytesIO
from datetime import datetime

from django.http import HttpResponse

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)





@api_view(["GET"])
@permission_classes([IsAuthenticated])
def quickbooks_status_view(request):

    user = request.user
    landscaper = getattr(user, "landscaper_profile", None)

    if not landscaper:
        return Response({
            "connected": False,
            "message": "Landscaper profile not found"
        })

    connection = QuickBooksConnection.objects.filter(
        landscaper=landscaper,
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
        connection=connection
    ).order_by("-created_at").first()

    total_synced = QuickBooksSyncLog.objects.filter(
        connection=connection,
        status="success"
    ).count()

    return Response({
        "connected": True,
        "company_name": connection.company_name,
        "realm_id": connection.realm_id,
        "sync_enabled": connection.is_active,
        "created_at": connection.connected_at,
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

    return redirect(reverse("quickbooks_success"))


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




@api_view(["GET"])
@permission_classes([IsAuthenticated])
def quickbooks_sync_log_detail_pdf(request, pk):
    landscaper = getattr(request.user, "landscaper_profile", None)
    if not landscaper:
        return Response(
            {"error": "Landscaper profile not found."},
            status=403,
        )

    connection = get_active_qb_connection(request.user)
    if not connection:
        return Response(
            {"error": "QuickBooks not connected."},
            status=status.HTTP_404_NOT_FOUND,
        )

    try:
        log = QuickBooksSyncLog.objects.get(
            id=pk,
            connection=connection,
        )
    except QuickBooksSyncLog.DoesNotExist:
        return Response(
            {"error": "Log not found."},
            status=404,
        )

    # --------------------------------------------------
    # Dynamic Payload Parsing (Matches your specific JSON structure)
    # --------------------------------------------------
    def safe_load(payload):
        if isinstance(payload, str):
            try:
                return json.loads(payload)
            except Exception:
                return {}
        return payload if isinstance(payload, dict) else {}

    req_data = safe_load(log.request_payload)
    res_raw = safe_load(log.response_payload)
    
    # Extract the nested 'Invoice' object from the response JSON
    res_invoice = res_raw.get("Invoice", {})

    # --------------------------------------------------
    # PDF Setup & Styling
    # --------------------------------------------------
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36,
    )

    log_text_left = ParagraphStyle(
        "LogTextLeft", fontName="Courier", fontSize=9, leading=12, alignment=TA_LEFT
    )
    log_text_right = ParagraphStyle(
        "LogTextRight", fontName="Courier", fontSize=9, leading=12, alignment=TA_RIGHT
    )
    title_style = ParagraphStyle(
        "LogTitle", fontName="Courier-Bold", fontSize=12, leading=14, alignment=TA_CENTER
    )

    elements = []
    page_width = A4[0] - 72  # Dynamic canvas printable space (~523pt)
    char_repeat_count = 85   # Standard character count for A4 boundaries in Courier 9pt

    def add_divider(char="=", space=5):
        elements.append(Spacer(1, space))
        elements.append(Paragraph(char * char_repeat_count, log_text_left))
        elements.append(Spacer(1, space))

    def create_kv_table(data_list):
        table_data = []
        for key, value in data_list:
            v_str = str(value) if value is not None else ""
            table_data.append([
                Paragraph(str(key), log_text_left),
                Paragraph(":", log_text_left),
                Paragraph(v_str, log_text_left)
            ])
        t = Table(table_data, colWidths=[160, 15, page_width - 175])
        t.setStyle(TableStyle([
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('LEFTPADDING', (0,0), (-1,-1), 0),
            ('RIGHTPADDING', (0,0), (-1,-1), 0),
            ('BOTTOMPADDING', (0,0), (-1,-1), 2),
            ('TOPPADDING', (0,0), (-1,-1), 2),
        ]))
        return t

    # --------------------------------------------------
    # 1. Main Title Header
    # --------------------------------------------------
    elements.append(Paragraph("QuickBooks Sync Log", title_style))
    add_divider("=")

    # --------------------------------------------------
    # 2. Section: Log Information
    # --------------------------------------------------
    elements.append(Paragraph("Log Information", log_text_left))
    elements.append(Spacer(1, 5))
    
    created_str = ""
    if log.created_at:
        if hasattr(log.created_at, 'strftime'):
            created_str = log.created_at.strftime("%Y-%m-%d %H:%M")
        else:
            # If it's already a string, parse out the timestamp format cleanly
            try:
                dt = datetime.strptime(str(log.created_at)[:16], "%Y-%m-%dT%H:%M")
                created_str = dt.strftime("%Y-%m-%d %H:%M")
            except Exception:
                created_str = str(log.created_at)

    log_info = [
        ("ID", log.id),
        ("Object Type", str(log.object_type).capitalize() if log.object_type else ""),
        ("Status", str(log.status).capitalize() if log.status else ""),
        ("Created", created_str),
    ]
    elements.append(create_kv_table(log_info))
    add_divider("=")

    # --------------------------------------------------
    # 3. Section: Request Information
    # --------------------------------------------------
    elements.append(Paragraph("Request Information", log_text_left))
    elements.append(Spacer(1, 5))
    
    req_info = [
        ("Invoice Number", req_data.get("DocNumber", "")),
        ("Customer ID", req_data.get("CustomerRef", {}).get("value", "")),
        ("Private Note", req_data.get("PrivateNote", "")),
    ]
    elements.append(create_kv_table(req_info))
    add_divider("=")

    # --------------------------------------------------
    # 4. Section: Invoice Items
    # --------------------------------------------------
    elements.append(Paragraph("Invoice Items", log_text_left))
    add_divider("-", space=2)
    
    item_rows = [
        [Paragraph("Description", log_text_left), 
         Paragraph("Qty", log_text_right), 
         Paragraph("Unit Price", log_text_right), 
         Paragraph("Amount", log_text_right)]
    ]
    
    # Dynamically extract items safely from Request payload array
    lines = req_data.get("Line", [])
    for line in lines:
        desc = line.get("Description", "")
        qty = "-"
        unit_price = "-"
        amount = line.get("Amount")

        # Extract quantities and unit configurations if present
        detail = line.get("SalesItemLineDetail")
        if detail:
            qty = detail.get("Qty", "-")
            u_price = detail.get("UnitPrice")
            if isinstance(u_price, (int, float)):
                unit_price = f"${u_price:.2f}"
        
        if isinstance(amount, (int, float)):
            amount = f"${amount:.2f}"
        else:
            amount = ""

        item_rows.append([
            Paragraph(str(desc), log_text_left),
            Paragraph(str(qty), log_text_right),
            Paragraph(str(unit_price), log_text_right),
            Paragraph(str(amount), log_text_right)
        ])

    # Construct and style the dynamic line item list table
    item_table = Table(item_rows, colWidths=[243, 60, 110, 110])
    item_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('LEFTPADDING', (0,0), (-1,-1), 0),
        ('RIGHTPADDING', (0,0), (-1,-1), 0),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('TOPPADDING', (0,0), (-1,-1), 4),
    ]))
    elements.append(item_table)
    add_divider("=")

    # --------------------------------------------------
    # 5. Section: Response Information
    # --------------------------------------------------
    elements.append(Paragraph("Response Information", log_text_left))
    elements.append(Spacer(1, 5))
    
    res_total = res_invoice.get("TotalAmt")
    if isinstance(res_total, (int, float)): res_total = f"${res_total:.2f}"

    res_balance = res_invoice.get("Balance")
    if isinstance(res_balance, (int, float)): res_balance = f"${res_balance:.2f}"

    res_info = [
        ("QuickBooks Invoice ID", res_invoice.get("Id", "")),
        ("Invoice Number", res_invoice.get("DocNumber", "")),
        ("Customer", res_invoice.get("CustomerRef", {}).get("name", "")),
        ("Currency", res_invoice.get("CurrencyRef", {}).get("value", "")),
        ("Total Amount", res_total or ""),
        ("Balance", res_balance or ""),
        ("Transaction Date", res_invoice.get("TxnDate", "")),
        ("Due Date", res_invoice.get("DueDate", "")),
        ("Print Status", res_invoice.get("PrintStatus", "")),
        ("Email Status", res_invoice.get("EmailStatus", "")),
        ("Private Note", res_invoice.get("PrivateNote", "")),
    ]
    elements.append(create_kv_table(res_info))
    add_divider("=")

    # --------------------------------------------------
    # 6. Section: Shipping Address (Maps from ShipFromAddr dynamically)
    # --------------------------------------------------
    ship_addr = res_invoice.get("ShipFromAddr")
    if ship_addr:
        elements.append(Paragraph("Shipping Address", log_text_left))
        elements.append(Spacer(1, 5))
        
        addr_lines = []
        if ship_addr.get("Line1"): addr_lines.append(ship_addr.get("Line1"))
        if ship_addr.get("Line2"): addr_lines.append(ship_addr.get("Line2"))
        if ship_addr.get("Line3"): addr_lines.append(ship_addr.get("Line3"))
        
        address_html = "<br/>".join(addr_lines)
        elements.append(Paragraph(address_html, log_text_left))
        add_divider("-", space=10)

    # Automatically Generated Footer Note
    elements.append(Paragraph("Generated automatically from YardLink QuickBooks Integration.", log_text_left))

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