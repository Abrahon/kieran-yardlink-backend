# import qrcode

# def generate_qr_code(url, file_path):
#     qr = qrcode.make(url)
#     qr.save(file_path)
import qrcode
from django.conf import settings
from pathlib import Path

def generate_landscaper_qr(qr_instance):
    # url = f"{settings.BACKEND_BASE_URL}/api/qr/scan/{qr_instance.id}/"
    url = f"https://zznkjkkp-8000.inc1.devtunnels.ms/api/qr/scan/{qr_instance.id}/"

    qr = qrcode.make(url)

    qr_dir = Path(settings.MEDIA_ROOT) / "qr_codes"
    qr_dir.mkdir(parents=True, exist_ok=True)

    file_path = qr_dir / f"{qr_instance.id}.png"
    qr.save(file_path)

    return str(file_path)

# def generate_landscaper_qr(qr_instance):
#     # url = f"{settings.BACKEND_BASE_URL}/api/qr/scan/{qr_instance.id}/"
#      url = f"https://zznkjkkp-8000.inc1.devtunnels.ms/api/qr/scan/{qr_instance.id}/"

#     # generate qr
#     qr_img = qrcode.make(url)

#     buffer = BytesIO()
#     qr_img.save(buffer, format="PNG")
#     buffer.seek(0)

#     upload = cloudinary.uploader.upload(
#         buffer,
#         folder="qr_codes",
#         public_id=str(qr_instance.id),
#         overwrite=True
#     )

#     return upload["secure_url"]
