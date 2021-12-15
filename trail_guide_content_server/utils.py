from datetime import datetime, timezone
from flask import request

__all__ = [
    "get_utc_str",
    "request_changed",
]


def get_utc_str() -> str:
    return datetime.utcnow().replace(microsecond=0, tzinfo=timezone.utc).isoformat()


def request_changed(old_val, form_data: bool = False, field: str = "id") -> bool:
    obj_to_check = request.form if form_data else request.json
    return field in obj_to_check and obj_to_check[field] != old_val
