from quickbooks import QuickBooks
from quickbooks.objects.customer import Customer
from quickbooks.objects.invoice import Invoice, InvoiceLine, SalesItemLineDetail
from quickbooks.objects.payment import Payment

def get_qb_client(landscaper_profile):
    return QuickBooks(
        sandbox=True,
        client_id="<CLIENT_ID>",
        client_secret="<CLIENT_SECRET>",
        access_token=landscaper_profile.quickbooks_access_token,
        company_id=landscaper_profile.quickbooks_company_id,
    )

def create_customer(qb_client, client_profile):
    # Create QuickBooks customer for client if not exists
    if getattr(client_profile, "quickbooks_id", None):
        return client_profile.quickbooks_id

    customer = Customer()
    customer.DisplayName = client_profile.name
    customer.PrimaryEmailAddr = {"Address": client_profile.user.email}
    customer.save(qb=qb_client)

    client_profile.quickbooks_id = customer.Id
    client_profile.save(update_fields=["quickbooks_id"])
    return customer.Id

def create_invoice(qb_client, schedule):
    client_qb_id = create_customer(qb_client, schedule.client)

    invoice = Invoice()
    invoice.CustomerRef = {"value": client_qb_id}

    line = InvoiceLine()
    line.Amount = float(schedule.service.price)
    line.Description = schedule.service.name
    line.SalesItemLineDetail = SalesItemLineDetail()
    line.SalesItemLineDetail.ItemRef = {"value": "1"}  # default item
    line.SalesItemLineDetail.Qty = 1

    invoice.Line.append(line)
    invoice.save(qb=qb_client)

    schedule.quickbooks_invoice_id = invoice.Id
    schedule.save(update_fields=["quickbooks_invoice_id"])
    return invoice.Id

def record_payment(qb_client, schedule, received=True):
    if not schedule.quickbooks_invoice_id:
        raise ValueError("Invoice not created in QuickBooks")

    payment = Payment()
    payment.CustomerRef = {"value": schedule.client.quickbooks_id}
    payment.TotalAmt = float(schedule.service.price)
    payment.ApplyToTxn.append({"TxnId": schedule.quickbooks_invoice_id, "PaymentAmt": payment.TotalAmt})
    payment.save(qb=qb_client)

    if received:
        schedule.payment_status = schedule.PAID
        schedule.save(update_fields=["payment_status"])
    return payment.Id