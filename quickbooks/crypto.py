from cryptography.fernet import Fernet
from django.conf import settings


def get_fernet():
    return Fernet(settings.QUICKBOOKS_TOKEN_ENCRYPTION_KEY)


def encrypt_text(value: str) -> str:
    return get_fernet().encrypt(value.encode()).decode()


def decrypt_text(value: str) -> str:
    return get_fernet().decrypt(value.encode()).decode()