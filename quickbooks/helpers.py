from quickbooks.models import QuickBooksConnection
# quickbooks/helpers.py
from django.utils import timezone
from quickbooks.token_service import refresh_quickbooks_token


def get_valid_connection(connection):
    if connection.access_token_expires_at and connection.access_token_expires_at > timezone.now():
        return connection

    return refresh_quickbooks_token(connection)



def get_active_qb_connection(user):
    landscaper = getattr(user, "landscaper_profile", None)

    if not landscaper:
        return None

    return QuickBooksConnection.objects.filter(
        landscaper=landscaper,
        is_active=True
    ).first()


def get_valid_connection(connection):
    if not connection:
        raise Exception("No QuickBooks connection found")

    if not connection.is_active:
        raise Exception("QuickBooks connection is inactive")

    return connection