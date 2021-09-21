import os

__all__ = ["Config"]


class Config:
    ASSET_DIR = os.environ.get("TGCS_ASSET_DIR", "")  # TODO: Defaults
    DATABASE = os.environ.get("TGCS_DATABASE", "")  # TODO: Defaults
