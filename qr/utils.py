# import qrcode

# def generate_qr_code(url, file_path):
#     qr = qrcode.make(url)
#     qr.save(file_path)
import qrcode
from django.conf import settings
from pathlib import Path

def generate_landscaper_qr(qr_instance):
    """
    Generates a QR code PNG pointing directly to the backend scan API.
    Suitable for Postman and Flutter testing.
    """

    # Backend scan URL (NO frontend dependency)
    url = f"{settings.BACKEND_BASE_URL}/api/qr/scan/{qr_instance.id}/"

    qr = qrcode.make(url)

    qr_dir = Path(settings.MEDIA_ROOT) / "qr_codes"
    qr_dir.mkdir(parents=True, exist_ok=True)

    file_path = qr_dir / f"{qr_instance.id}.png"
    qr.save(file_path)

    return str(file_path)

