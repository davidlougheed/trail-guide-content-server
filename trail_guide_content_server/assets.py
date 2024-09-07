# A server for hosting a trail guide mobile app's content and data.
# Copyright (C) 2021-2023  David Lougheed
# See NOTICE for more information.

import json
import os

from datetime import datetime
from itertools import groupby
from pathlib import Path
from typing import Literal

from .db import get_asset_types
from .types import AssetType, AssetWithUsage

__all__ = [
    "ASSET_TYPE_IMAGE",
    "ASSET_TYPE_AUDIO",
    "ASSET_TYPE_VIDEO",
    "ASSET_TYPE_VIDEO_TEXT_TRACK",
    "ASSET_TYPE_PDF",
    "ASSET_TYPES",

    "AssetTypeError",
    "detect_asset_type",
    "make_asset_list",
]


ASSET_TYPE_IMAGE: Literal["image"] = "image"
ASSET_TYPE_AUDIO: Literal["audio"] = "audio"
ASSET_TYPE_VIDEO: Literal["video"] = "video"
ASSET_TYPE_VIDEO_TEXT_TRACK: Literal["video_text_track"] = "video_text_track"
ASSET_TYPE_PDF: Literal["pdf"] = "pdf"

ASSET_TYPES: frozenset[AssetType] = frozenset({
    ASSET_TYPE_IMAGE,
    ASSET_TYPE_AUDIO,
    ASSET_TYPE_VIDEO,
    ASSET_TYPE_VIDEO_TEXT_TRACK,
    ASSET_TYPE_PDF,
})


class AssetTypeError(Exception):
    pass


def detect_asset_type(file_name: str | Path, form_data=None) -> AssetType:
    form_data = form_data or {}
    file_ext = os.path.splitext(file_name)[1].lower().lstrip(".")

    match file_ext:
        case "jpg" | "jpeg" | "png" | "gif":
            return ASSET_TYPE_IMAGE
        case "mp3" | "m4a":
            return ASSET_TYPE_AUDIO
        case "mp4" | "mov":
            return ASSET_TYPE_VIDEO
        case "vtt":
            return ASSET_TYPE_VIDEO_TEXT_TRACK
        case "pdf":
            return ASSET_TYPE_PDF
        case _:
            if "asset_type" not in form_data:
                raise AssetTypeError("No asset_type provided, and could not figure it out automatically")

            asset_type = form_data["asset_type"]

            if asset_type not in ASSET_TYPES:
                raise AssetTypeError(f"'{asset_type}' is not a valid asset type")

            return asset_type


def _make_asset_list_js(assets: list[AssetWithUsage]) -> tuple[str, str]:
    def _asset_type(a: AssetWithUsage) -> AssetType:
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


def make_asset_list(assets: list[AssetWithUsage], as_js: bool = False) -> tuple[str, str]:
    if as_js:
        return _make_asset_list_js(assets)

    return json.dumps(assets), "application/json"
