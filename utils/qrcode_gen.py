# utils/qrcode_gen.py — QR Code generation utility for PLAGENOR 4.0
from __future__ import annotations
import io, base64

try:
    import qrcode
    _HAS_QR = True
except ImportError:
    _HAS_QR = False


def generate_qr_base64(data: str) -> str:
    if not _HAS_QR:
        return ""
    qr = qrcode.QRCode(version=1, box_size=8, border=2)
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="#1A202C", back_color="white")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode()


def generate_qr_html(data: str, size: int = 180) -> str:
    b64 = generate_qr_base64(data)
    if not b64:
        return "<p>QR code unavailable (install qrcode package)</p>"
    return f'<img src="data:image/png;base64,{b64}" width="{size}" height="{size}" style="border-radius:8px;border:1px solid #E2E8F0"/>'
