# A server for hosting a trail guide mobile app's content and data.
# Copyright (C) 2021-2022  David Lougheed
# See NOTICE for more information.

import qrcode
from flask import current_app
from io import BytesIO

__all__ = [
    "make_station_qr",
    "make_page_qr",
]


def _make_qr(url: str) -> BytesIO:
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=12,
        border=6,
    )

    qr.add_data(url)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")

    buf = BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)

    return buf


def make_station_qr(station_id: str) -> BytesIO:
    return _make_qr(f"{current_app.config['APP_BASE_URL']}/stations/detail/{station_id}")


def make_page_qr(page_id: str) -> BytesIO:
    return _make_qr(f"{current_app.config['APP_BASE_URL']}/pages/{page_id}")
