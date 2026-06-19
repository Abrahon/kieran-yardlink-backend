import requests
from django.utils import timezone
from datetime import timedelta
from quickbooks.crypto import decrypt_text, encrypt_text
from django.conf import settings


def refresh_quickbooks_token(connection):
    """
    Refresh expired access token using refresh token
    """

    refresh_token = decrypt_text(connection.refresh_token_encrypted)

    url = "https://oauth.platform.intuit.com/oauth2/v1/tokens/bearer"

    payload = {
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
    }

    auth = (settings.QUICKBOOKS_CLIENT_ID, settings.QUICKBOOKS_CLIENT_SECRET)

    headers = {
        "Accept": "application/json",
        "Content-Type": "application/x-www-form-urlencoded",
    }

    response = requests.post(url, data=payload, auth=auth, headers=headers)

    if response.status_code != 200:
        raise Exception(f"Token refresh failed: {response.text}")

    data = response.json()

    connection.access_token_encrypted = encrypt_text(data["access_token"])
    connection.refresh_token_encrypted = encrypt_text(data["refresh_token"])
    connection.access_token_expires_at = timezone.now() + timedelta(seconds=3600)
    connection.refresh_token_expires_at = timezone.now() + timedelta(seconds=data.get("x_refresh_token_expires_in", 86400))

    connection.save()

    return connection