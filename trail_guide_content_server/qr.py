import qrcode
from flask import current_app
from io import BytesIO

__all__ = [
    "make_station_qr",
]


def make_station_qr(station_id: str):
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=12,
        border=6,
    )

    qr.add_data(f"{current_app.config['LINKING_SCHEME']}://stations/detail/{station_id}")
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")

    buf = BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)

    return buf
