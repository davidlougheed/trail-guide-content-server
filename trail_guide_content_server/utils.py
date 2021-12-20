import hashlib
import os

from datetime import datetime, timezone
from flask import request
from pathlib import Path

from typing import Union

__all__ = [
    "get_file_hash_hex",
    "detect_asset_type",
    "get_utc_str",
    "request_changed",
]


def get_file_hash_hex(path: Union[str, Path]) -> str:
    file_hash = hashlib.new("sha1", usedforsecurity=False)
    with open(path, "rb") as hfh:
        while data := hfh.read(1024):
            file_hash.update(data)
    return file_hash.hexdigest()


def detect_asset_type(file_name: Union[str, Path]) -> tuple[str, str]:
    file_ext = os.path.splitext(file_name)[1].lower().lstrip(".")

    # TODO: py3.10: match
    if file_ext in {"jpg", "jpeg", "png", "gif"}:
        asset_type = "image"
    elif file_ext in {"mp3", "m4a"}:
        asset_type = "audio"
    elif file_ext in {"mp4", "mov"}:
        asset_type = "video"
    elif file_ext in {"vtt"}:
        asset_type = "video_text_track"
    else:
        if "asset_type" not in request.form:
            return "", "No asset_type provided, and could not figure it out automatically"

        asset_type = request.form["asset_type"]

    return asset_type, ""


def get_utc_str() -> str:
    return datetime.utcnow().replace(microsecond=0, tzinfo=timezone.utc).isoformat()


def request_changed(old_val, form_data: bool = False, field: str = "id") -> bool:
    obj_to_check = request.form if form_data else request.json
    return field in obj_to_check and obj_to_check[field] != old_val
