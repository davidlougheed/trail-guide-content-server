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
import sqlite3

import click
import json
import os
import pathlib
import re
import shutil
import uuid
import werkzeug.exceptions

from datetime import datetime
from flask import Flask, g, jsonify
from flask_cors import CORS
from werkzeug.utils import secure_filename

from .auth import AuthError
from .config import Config
from .db import get_db, set_asset, set_station
from .routes import api_v1
from .utils import get_file_hash_hex, detect_asset_type

SRC_PATTERN = re.compile(r"src=\\?\"([A-Za-z0-9/._\-]+)\\?\"")
POSTER_PATTERN = re.compile(r"poster=\\?\"([A-Za-z0-9/._\-]+)\\?\"")

application = Flask(__name__)
application.config.from_object(Config)

CORS(application, resources={r"/api/v1/*": {"origins": "*"}})

application.register_blueprint(api_v1, url_prefix="/api/v1")


@application.errorhandler(werkzeug.exceptions.NotFound)
def handle_not_found(_e):
    return jsonify({"message": "Not found"}), 404


@application.errorhandler(werkzeug.exceptions.BadRequest)
def handle_bad_request(e):
    return jsonify({"message": "Bad request", "errors": [str(e)]}), 400


@application.errorhandler(werkzeug.exceptions.InternalServerError)
def handle_internal_server_error(e):
    return jsonify({"message": "Internal server error", "errors": [str(e)]}), 500


@application.errorhandler(AuthError)
def handle_auth_error(e):
    return jsonify(dict(e)), 401


@application.teardown_appcontext
def close_db(_exception):
    db = getattr(g, "_database", None)
    if db is not None:
        db.close()


def _import_file(c: sqlite3.Cursor, file_path, file_match) -> str:
    checksum = get_file_hash_hex(file_path)

    c.execute("SELECT id FROM assets WHERE sha1_checksum = ?", (checksum,))
    r = c.fetchone()

    if r:
        asset_id = r[0]

    else:
        # Make new asset since it isn't in the database

        file_name = f"{int(datetime.now().timestamp() * 1000)}-{secure_filename(file_match)}"
        new_file_path = pathlib.Path(application.config["ASSET_DIR"]) / file_name

        shutil.copyfile(file_path, new_file_path)

        new_asset = {
            "id": str(uuid.uuid4()),
            "asset_type": detect_asset_type(new_file_path)[0],
            "file_name": file_name,
            "file_size": os.path.getsize(new_file_path),
            "sha1_checksum": checksum,
            "enabled": True,
        }

        print("\tImporting", file_name)

        set_asset(new_asset["id"], new_asset)

        asset_id = new_asset["id"]

    return asset_id


@application.cli.command("import_stations")
@click.argument("base_path")
@click.argument("stations_json")
@click.argument("manifest_json")
def import_stations(base_path, stations_json, manifest_json):
    with open(stations_json, "r") as stf:
        data = json.load(stf)

    with open(manifest_json, "r") as afh:
        manifest = json.load(afh)

    asset_checksums = {}
    # for a, p in assets.items():
    #     asset_checksums[a] = get_file_hash_hex(p)

    db = get_db()
    c = db.cursor()

    for section in data:
        # TODO: Import section too
        for station_path, station in zip(manifest["stations"][section["id"]], section["data"]):
            print(f"Working on station: {station['title']}")
            # TODO: Validate station

            header_path = os.path.join(base_path, station_path, "header.jpg")
            header_asset = None
            if os.path.exists(header_path):
                header_asset = _import_file(c, header_path, f"{station_path}-header.jpg")

            contents = []

            def _replace_assets(string, direct=False):
                if not string:
                    return string

                if direct:
                    matches = [string]
                    print(f"\tmatches: {matches}")
                else:
                    src_data = SRC_PATTERN.findall(string)
                    poster_data = POSTER_PATTERN.findall(string)
                    print(f"\t   src matches: {src_data}")
                    print(f"\tposter matches: {poster_data}")
                    matches = [*src_data, *poster_data]

                for match in matches:
                    match_path = os.path.join(base_path, station_path, match)
                    if not os.path.exists(match_path):
                        print(f"\tMissing asset '{match}' (not in manifest.)")
                        continue

                    asset_id = _import_file(c, match_path, match)
                    string = string.replace(match, asset_id)

                return string

            for ci in station.get("contents", []):
                if ci["content_type"] == "html":
                    keys = ("content_before_fold", "content_after_fold")
                elif ci["content_type"] == "quiz":
                    keys = ("question", "answer")
                elif ci["content_type"] == "gallery":
                    # Filter out blank assets which seem to crop up occasionally
                    ci["items"] = list(filter(lambda item: item["asset"], ci["items"]))
                    keys = ("description", ("items", "asset"))
                else:
                    keys = ()

                for key in keys:
                    if isinstance(key, tuple):
                        for i in range(len(ci[key[0]])):
                            print(f"\tWorking on key: {key[0]}.{i}.{key[1]}")
                            ci[key[0]][i][key[1]] = _replace_assets(ci[key[0]][i][key[1]], direct=True)
                    else:
                        print(f"\tWorking on key: {key}")
                        ci[key] = _replace_assets(ci[key])

                contents.append(ci)

            set_station(str(uuid.uuid4()), {
                **station,
                "header_image": header_asset,
                "contents": contents,
                "section": section["id"],
            })


SCHEMA_PATH = pathlib.Path(__file__).parent.resolve() / "schema.sql"


# Initialize the DB on startup
with application.app_context(), open(SCHEMA_PATH, "r") as sf:
    application.logger.info(f"Initializing database at {application.config['DATABASE']}")
    application.logger.info(f"    Schema location: {SCHEMA_PATH}")
    get_db().executescript(sf.read())
