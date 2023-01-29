# A server for hosting a trail guide mobile app's content and data.
# Copyright (C) 2021-2023  David Lougheed
# See NOTICE for more information.

import hashlib

from datetime import datetime, timezone
from flask import request
from pathlib import Path

from typing import Union

__all__ = [
    "get_file_hash_hex",
    "get_utc_str",
    "request_changed",
]


def get_file_hash_hex(path: Union[str, Path]) -> str:
    file_hash = hashlib.new("sha1", usedforsecurity=False)
    with open(path, "rb") as hfh:
        while data := hfh.read(1024):
            file_hash.update(data)
    return file_hash.hexdigest()


def get_utc_str() -> str:
    return datetime.utcnow().replace(microsecond=0, tzinfo=timezone.utc).isoformat()


def request_changed(old_val, form_data: bool = False, field: str = "id") -> bool:
    # Assume old object was a dict
    if request.json is None or isinstance(request.json, str):
        return True

    obj_to_check = request.form if form_data else request.json
    return field in obj_to_check and obj_to_check[field] != old_val
