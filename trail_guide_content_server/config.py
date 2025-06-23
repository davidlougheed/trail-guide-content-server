# A server for hosting a trail guide mobile app's content and data.
# Copyright (C) 2021-2025  David Lougheed
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

_public_config_values: set[str] = {
    "MAX_CONTENT_LENGTH",
    "AUTH_AUDIENCE",
    "AUTH_ISSUER",
    "BASE_URL",
    "APP_BASE_URL",
    "APP_NAME",
    "APP_SLUG",
    "APPLE_APP_ID",
    "ANDROID_PACKAGE_NAME",
    "ANDROID_CERT_FINGERPRINT",
}

_config_vars_and_defaults = {
    "ASSET_DIR": (str, DEFAULT_ASSET_DIR),
    "BUNDLE_DIR": (str, DEFAULT_BUNDLE_DIR),
    "DATABASE": (str, DEFAULT_DB),
    # -------------------------------------------------------------------------
    "MAX_CONTENT_LENGTH": (int, 10 * (1024**2)),  # 10 MB maximum upload size
    # -------------------------------------------------------------------------
    "AUTH_AUDIENCE": (str, ""),
    "AUTH_ISSUER": (str, ""),
    # -------------------------------------------------------------------------
    "BASE_URL": (str, "http://localhost:5000"),
    # -------------------------------------------------------------------------
    "APP_BASE_URL": (str, "http://localhost:5000/app"),
    "APP_NAME": (str, "Trail Guide"),
    "APP_SLUG": (str, "trail-guide"),
    # -------------------------------------------------------------------------
    "APPLE_APP_ID": (str, ""),
    "ANDROID_PACKAGE_NAME": (str, ""),
    "ANDROID_CERT_FINGERPRINT": (str, ""),
}

config = {k: os.environ.get(f"{ENV_PREFIX}{k}", v[0](v[1])) for k, v in _config_vars_and_defaults.items()}

public_config = {k: v for k, v in config.items() if k in _public_config_values}
