# A server for hosting a trail guide mobile app's content and data.
# Copyright (C) 2021-2024  David Lougheed
# See NOTICE for more information.

from typing import Literal, TypedDict

__all__ = [
    "AssetType",
    "Asset",
    "AssetWithUsage",
]


AssetType = Literal["audio", "image", "pdf", "video", "video_text_track"]


class Asset(TypedDict):
    id: str
    asset_type: AssetType
    file_name: str
    file_size: int
    sha1_checksum: str


class AssetWithUsage(Asset):
    times_used_by_all: int
    times_used_by_enabled: int