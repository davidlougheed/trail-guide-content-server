# A server for hosting a trail guide mobile app's content and data.
# Copyright (C) 2021-2023  David Lougheed
# See NOTICE for more information.

import json
import os

from datetime import datetime
from itertools import groupby
from pathlib import Path

from .db import get_asset_types

__all__ = [
    "ASSET_TYPE_IMAGE",
    "ASSET_TYPE_AUDIO",
    "ASSET_TYPE_VIDEO",
    "ASSET_TYPE_VIDEO_TEXT_TRACK",
    "ASSET_TYPE_PDF",
    "ASSET_TYPES",

    "detect_asset_type",
    "make_asset_list",
]


ASSET_TYPE_IMAGE = "image"
ASSET_TYPE_AUDIO = "audio"
ASSET_TYPE_VIDEO = "video"
ASSET_TYPE_VIDEO_TEXT_TRACK = "video_text_track"
ASSET_TYPE_PDF = "pdf"

ASSET_TYPES: frozenset[str] = frozenset({
    ASSET_TYPE_IMAGE,
    ASSET_TYPE_AUDIO,
    ASSET_TYPE_VIDEO,
    ASSET_TYPE_VIDEO_TEXT_TRACK,
    ASSET_TYPE_PDF,
})


def detect_asset_type(file_name: str | Path, form_data=None) -> tuple[str, str]:
    form_data = form_data or {}
    file_ext = os.path.splitext(file_name)[1].lower().lstrip(".")

    match file_ext:
        case "jpg" | "jpeg" | "png" | "gif":
            asset_type = "image"
        case "mp3" | "m4a":
            asset_type = "audio"
        case "mp4" | "mov":
            asset_type = "video"
        case "vtt":
            asset_type = "video_text_track"
        case "pdf":
            asset_type = "pdf"
        case _:
            if "asset_type" not in form_data:
                return "", "No asset_type provided, and could not figure it out automatically"

            asset_type = form_data["asset_type"]

    return asset_type, ""


def _make_asset_list_js(assets: list[dict]) -> tuple[str, str]:
    def _asset_type(a):
        return a["asset_type"]

    assets_by_type = {
        at: {aa["id"]: f"""require("./{at}/{aa['file_name']}")""" for aa in v}
        for at, v in groupby(sorted(assets, key=_asset_type), key=_asset_type)
    }

    rt = (
        f"// Generated automatically by trail-guide-content-server\n"
        f"// at {datetime.now().isoformat()}\n"
        f"export default {{\n"
    )

    for at in get_asset_types():
        at_str = json.dumps(at)
        rt += f"    {at_str}: {{\n"
        for k, v in assets_by_type.get(at, {}).items():
            rt += f"        {json.dumps(k)}: {v},\n"

        rt += "    },\n"

    rt += "};\n"

    return rt, "application/js"


def make_asset_list(assets: list[dict], as_js: bool = False) -> tuple[str, str]:
    if as_js:
        return _make_asset_list_js(assets)

    return json.dumps(assets), "application/json"
