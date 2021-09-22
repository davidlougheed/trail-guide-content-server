import os
import pathlib

__all__ = ["Config"]


DEFAULT_ASSET_DIR = pathlib.Path(__file__).parent.parent.resolve() / "data" / "assets"
DEFAULT_DB = pathlib.Path(__file__).parent.parent.resolve() / "data" / "db.sqlite3"


class Config:
    ASSET_DIR = os.environ.get("TGCS_ASSET_DIR", str(DEFAULT_ASSET_DIR))
    DATABASE = os.environ.get("TGCS_DATABASE", str(DEFAULT_DB))
    MAX_CONTENT_LENGTH = 2 * (1024 ** 2)  # 2 MB maximum upload size
