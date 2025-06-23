# A server for hosting a trail guide mobile app's content and data.
# Copyright (C) 2021-2025  David Lougheed
# See NOTICE for more information.

from typing import Literal, TypedDict

__all__ = [
    "AssetType",
    "Asset",
    "AssetWithIDAndUsage",
    "Category",
    "CategoryWithID",
]


AssetType = Literal["audio", "image", "pdf", "video", "video_text_track"]


class Asset(TypedDict):
    asset_type: AssetType
    file_name: str
    file_size: int
    sha1_checksum: str


class AssetWithIDAndUsage(Asset):
    id: str
    times_used_by_all: int
    times_used_by_enabled: int


class Category(TypedDict):
    icon_svg: str


class CategoryWithID(Category):
    id: str
