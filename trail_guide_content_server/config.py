# A server for hosting a trail guide mobile app's content and data.
# Copyright (C) 2021-2022  David Lougheed
# See NOTICE for more information.

import os
import pathlib
from dotenv import load_dotenv

__all__ = [
    "config",
    "public_config",
]

ENV_PREFIX = "TGCS_"

DEFAULT_ASSET_DIR = pathlib.Path(__file__).parent.parent.resolve() / "data" / "assets"
DEFAULT_BUNDLE_DIR = pathlib.Path(__file__).parent.parent.resolve() / "data" / "bundles"
DEFAULT_DB = pathlib.Path(__file__).parent.parent.resolve() / "data" / "db.sqlite3"

load_dotenv()

_public_config_values = {
    "AUTH_AUDIENCE",
    "AUTH_ISSUER",
    "BASE_URL",
    "MAX_CONTENT_LENGTH",
    "APP_NAME",
    "APP_SLUG",
    "LINKING_SCHEME",
}

_config_vars_and_defaults = {
    "ASSET_DIR": (str, DEFAULT_ASSET_DIR),
    "BUNDLE_DIR": (str, DEFAULT_BUNDLE_DIR),
    "DATABASE": (str, DEFAULT_DB),

    "AUTH_AUDIENCE": (str, ""),
    "AUTH_ISSUER": (str, ""),

    "BASE_URL": (str, "http://localhost:5000"),

    "MAX_CONTENT_LENGTH": (int, 5 * (1024 ** 2)),  # 5 MB maximum upload size

    "APP_NAME": (str, "Trail Guide"),
    "APP_SLUG": (str, "trail-guide"),
    "LINKING_SCHEME": (str, ""),
}

config = {
    k: os.environ.get(f"{ENV_PREFIX}{k}", v[0](v[1]))
    for k, v in _config_vars_and_defaults.items()
}

public_config = {
    k: v
    for k, v in config.items()
    if k in _public_config_values
}
