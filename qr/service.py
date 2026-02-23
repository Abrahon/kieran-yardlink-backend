import qrcode
from django.conf import settings
from pathlib import Path

def generate_landscaper_qr(qr_instance):
    url = f"{settings.FRONTEND_URL}/scan/{qr_instance.id}"
    qr = qrcode.make(url)

    qr_dir = Path(settings.MEDIA_ROOT) / "qr_codes"
    qr_dir.mkdir(parents=True, exist_ok=True)

    file_path = qr_dir / f"{qr_instance.id}.png"
    qr.save(file_path)

    return str(file_path)
