# A server for hosting a trail guide mobile app's content and data.
# Copyright (C) 2021  David Lougheed
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import os
import pathlib
from dotenv import load_dotenv

__all__ = ["Config"]


DEFAULT_ASSET_DIR = pathlib.Path(__file__).parent.parent.resolve() / "data" / "assets"
DEFAULT_DB = pathlib.Path(__file__).parent.parent.resolve() / "data" / "db.sqlite3"

load_dotenv()


class Config:
    ASSET_DIR = os.environ.get("TGCS_ASSET_DIR", str(DEFAULT_ASSET_DIR))
    AUTH_AUDIENCE = os.environ.get("TGCS_AUTH_AUDIENCE", "")
    AUTH_ISSUER = os.environ.get("TGCS_AUTH_ISSUER", "").rstrip("/")
    DATABASE = os.environ.get("TGCS_DATABASE", str(DEFAULT_DB))
    MAX_CONTENT_LENGTH = 2 * (1024 ** 2)  # 2 MB maximum upload size
