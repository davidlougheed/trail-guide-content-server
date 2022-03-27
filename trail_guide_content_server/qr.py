# A server for hosting a trail guide mobile app's content and data.
# Copyright (C) 2021-2022  David Lougheed
# See NOTICE for more information.

import qrcode
from flask import current_app
from io import BytesIO

__all__ = [
    "make_station_qr",
]


def make_station_qr(station_id: str) -> BytesIO:
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=12,
        border=6,
    )

    qr.add_data(f"{current_app.config['BASE_URL']}/app/stations/detail/{station_id}")
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")

    buf = BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)

    return buf
