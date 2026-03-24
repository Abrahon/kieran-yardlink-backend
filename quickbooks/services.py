import base64
from datetime import timedelta
from urllib.parse import urlencode, quote

import requests
from django.conf import settings
from django.utils import timezone

from quickbooks.crypto import encrypt_text, decrypt_text
from quickbooks.models import QuickBooksConnection, QuickBooksSyncLog


QBO_AUTH_URL = "https://appcenter.intuit.com/connect/oauth2"
QBO_TOKEN_URL = "https://oauth.platform.intuit.com/oauth2/v1/tokens/bearer"

QBO_API_BASE = {
    "production": "https://quickbooks.api.intuit.com",
    "sandbox": "https://sandbox-quickbooks.api.intuit.com",
}


def _basic_auth_header():
    raw = f"{settings.QUICKBOOKS_CLIENT_ID}:{settings.QUICKBOOKS_CLIENT_SECRET}"
    encoded = base64.b64encode(raw.encode()).decode()
    return {"Authorization": f"Basic {encoded}"}


def build_authorization_url(state: str) -> str:
    params = {
        "client_id": settings.QUICKBOOKS_CLIENT_ID,
        "response_type": "code",
        "scope": "com.intuit.quickbooks.accounting",
        "redirect_uri": settings.QUICKBOOKS_REDIRECT_URI,
        "state": state,
    }
    return f"{QBO_AUTH_URL}?{urlencode(params)}"


def exchange_code_for_tokens(code: str) -> dict:
    headers = {
        **_basic_auth_header(),
        "Accept": "application/json",
        "Content-Type": "application/x-www-form-urlencoded",
    }
    data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": settings.QUICKBOOKS_REDIRECT_URI,
    }
    r = requests.post(QBO_TOKEN_URL, headers=headers, data=data, timeout=30)
    r.raise_for_status()
    return r.json()


def refresh_tokens(connection: QuickBooksConnection) -> QuickBooksConnection:
    refresh_token = decrypt_text(connection.refresh_token_encrypted)

    headers = {
        **_basic_auth_header(),
        "Accept": "application/json",
        "Content-Type": "application/x-www-form-urlencoded",
    }
    data = {
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
    }

    r = requests.post(QBO_TOKEN_URL, headers=headers, data=data, timeout=30)

    if r.status_code != 200:
        connection.is_active = False
        connection.save(update_fields=["is_active", "updated_at"])
        raise Exception("QuickBooks token refresh failed. Reconnect required.")

    payload = r.json()

    connection.access_token_encrypted = encrypt_text(payload["access_token"])
    connection.refresh_token_encrypted = encrypt_text(payload["refresh_token"])
    connection.access_token_expires_at = timezone.now() + timedelta(seconds=payload.get("expires_in", 3600))
    connection.refresh_token_expires_at = timezone.now() + timedelta(seconds=payload.get("x_refresh_token_expires_in", 86400))
    connection.save(update_fields=[
        "access_token_encrypted",
        "refresh_token_encrypted",
        "access_token_expires_at",
        "refresh_token_expires_at",
        "updated_at",
    ])
    return connection


def get_valid_access_token(connection: QuickBooksConnection) -> str:
    if not connection.access_token_expires_at or connection.access_token_expires_at <= timezone.now() + timedelta(minutes=5):
        connection = refresh_tokens(connection)
    return decrypt_text(connection.access_token_encrypted)


def _qbo_headers(connection: QuickBooksConnection):
    token = get_valid_access_token(connection)
    return {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",
        "Content-Type": "application/json",
    }


def _qbo_base_url():
    return QBO_API_BASE[settings.QUICKBOOKS_ENVIRONMENT]


def qbo_post(connection: QuickBooksConnection, resource: str, payload: dict):
    url = f"{_qbo_base_url()}/v3/company/{connection.realm_id}/{resource}?minorversion={settings.QUICKBOOKS_MINOR_VERSION}"
    return requests.post(url, headers=_qbo_headers(connection), json=payload, timeout=30)


def qbo_get(connection: QuickBooksConnection, path: str):
    url = f"{_qbo_base_url()}/v3/company/{connection.realm_id}/{path}?minorversion={settings.QUICKBOOKS_MINOR_VERSION}"
    return requests.get(url, headers=_qbo_headers(connection), timeout=30)


def qbo_query(connection: QuickBooksConnection, query: str):
    encoded_query = quote(query, safe="")
    url = f"{_qbo_base_url()}/v3/company/{connection.realm_id}/query?query={encoded_query}&minorversion={settings.QUICKBOOKS_MINOR_VERSION}"
    return requests.get(url, headers=_qbo_headers(connection), timeout=30)


def _log_sync(connection, invoice, object_type, resp, payload):
    QuickBooksSyncLog.objects.create(
        connection=connection,
        invoice=invoice,
        object_type=object_type,
        status=QuickBooksSyncLog.Status.SUCCESS if resp.ok else QuickBooksSyncLog.Status.FAILED,
        request_payload=payload,
        response_payload=resp.json() if resp.content else None,
        error_message=None if resp.ok else resp.text,
        object_id_in_qbo=(
            resp.json().get("Customer", {}).get("Id")
            or resp.json().get("Invoice", {}).get("Id")
            or resp.json().get("Payment", {}).get("Id")
            if resp.ok else None
        ),
    )


def upsert_customer(connection: QuickBooksConnection, invoice):
    if invoice.quickbooks_customer_id:
        return {"Id": invoice.quickbooks_customer_id}

    customer_name = None
    customer_email = None

    if getattr(invoice.job, "external_client", None):
        ext = invoice.job.external_client
        customer_name = ext.full_name
        customer_email = ext.email
    elif getattr(invoice.job, "client", None):
        user = getattr(invoice.job.client, "user", None)
        customer_name = getattr(user, "name", None) or getattr(invoice.job.client, "name", None) or "Client"
        customer_email = getattr(user, "email", None)

    if not customer_name:
        customer_name = "Client"

    # Prefer email lookup if present
    found_customer = None
    if customer_email:
        # query = f"select * from Customer where PrimaryEmailAddr = '{customer_email.replace(\"'\", \"\\\\'\")}'"
        query = f"""select * from Customer where PrimaryEmailAddr = '{customer_email.replace("'", "\\'")}'"""
        query_resp = qbo_query(connection, query)
        if query_resp.ok:
            customers = query_resp.json().get("QueryResponse", {}).get("Customer", [])
            if customers:
                found_customer = customers[0]

    if not found_customer:
        # query = f"select * from Customer where DisplayName = '{customer_name.replace(\"'\", \"\\\\'\")}'"
        query = f"""select * from Customer where DisplayName = '{customer_name.replace("'", "\\'")}'"""
        query_resp = qbo_query(connection, query)
        if query_resp.ok:
            customers = query_resp.json().get("QueryResponse", {}).get("Customer", [])
            if customers:
                found_customer = customers[0]

    if found_customer:
        invoice.quickbooks_customer_id = found_customer["Id"]
        invoice.save(update_fields=["quickbooks_customer_id", "updated_at"])
        return found_customer

    payload = {"DisplayName": customer_name}
    if customer_email:
        payload["PrimaryEmailAddr"] = {"Address": customer_email}

    resp = qbo_post(connection, "customer", payload)
    _log_sync(connection, invoice, QuickBooksSyncLog.ObjectType.CUSTOMER, resp, payload)
    resp.raise_for_status()

    customer = resp.json()["Customer"]
    invoice.quickbooks_customer_id = customer["Id"]
    invoice.save(update_fields=["quickbooks_customer_id", "updated_at"])
    return customer


def create_invoice(connection: QuickBooksConnection, invoice, customer_qbo_id: str, service_item_id: str):
    if invoice.quickbooks_invoice_id:
        return {"Id": invoice.quickbooks_invoice_id}

    lines = []
    for line in invoice.line_items.all():
        lines.append({
            "Amount": float(line.line_total),
            "DetailType": "SalesItemLineDetail",
            "Description": line.name,
            "SalesItemLineDetail": {
                "Qty": line.quantity,
                "UnitPrice": float(line.unit_price),
                "ItemRef": {
                    "value": str(service_item_id)
                }
            }
        })

    if getattr(invoice, "service_fee_amount", 0) and float(invoice.service_fee_amount) > 0:
        lines.append({
            "Amount": float(invoice.service_fee_amount),
            "DetailType": "DescriptionOnly",
            "Description": f"Platform Fee ({invoice.service_fee_percent}%)"
        })

    payload = {
        "CustomerRef": {"value": customer_qbo_id},
        "Line": lines,
        "PrivateNote": f"Platform Invoice #{invoice.invoice_number}",
        "DocNumber": invoice.invoice_number,
    }

    resp = qbo_post(connection, "invoice", payload)
    _log_sync(connection, invoice, QuickBooksSyncLog.ObjectType.INVOICE, resp, payload)
    resp.raise_for_status()

    qbo_invoice = resp.json()["Invoice"]
    invoice.quickbooks_invoice_id = qbo_invoice["Id"]
    invoice.save(update_fields=["quickbooks_invoice_id", "updated_at"])
    return qbo_invoice


def create_payment(connection: QuickBooksConnection, invoice, customer_qbo_id: str, qbo_invoice_id: str, deposit_to_account_id: str):
    if invoice.quickbooks_payment_id:
        return {"Id": invoice.quickbooks_payment_id}

    payload = {
        "CustomerRef": {"value": customer_qbo_id},
        "TotalAmt": float(invoice.total),
        "Line": [
            {
                "Amount": float(invoice.total),
                "LinkedTxn": [
                    {
                        "TxnId": qbo_invoice_id,
                        "TxnType": "Invoice"
                    }
                ]
            }
        ],
        "DepositToAccountRef": {"value": str(deposit_to_account_id)},
        "PrivateNote": f"Stripe payment for {invoice.invoice_number}",
    }

    resp = qbo_post(connection, "payment", payload)
    _log_sync(connection, invoice, QuickBooksSyncLog.ObjectType.PAYMENT, resp, payload)
    resp.raise_for_status()

    qbo_payment = resp.json()["Payment"]
    invoice.quickbooks_payment_id = qbo_payment["Id"]
    invoice.save(update_fields=["quickbooks_payment_id", "updated_at"])
    return qbo_payment