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
