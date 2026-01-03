import qrcode

def generate_qr_code(url, file_path):
    qr = qrcode.make(url)
    qr.save(file_path)
