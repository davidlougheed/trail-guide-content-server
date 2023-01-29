# A server for hosting a trail guide mobile app's content and data.
# Copyright (C) 2021-2023  David Lougheed
# See NOTICE for more information.

import click
import json
import os
import pathlib
import re
import shutil
import sqlite3
import uuid
import werkzeug.exceptions

from datetime import datetime
from flask import Flask, g, jsonify
from flask_cors import CORS
from werkzeug.utils import secure_filename

from .assets import detect_asset_type
from .auth import AuthError
from .config import config
from .db import get_db, set_asset, station_model
from .routes import api_v1, well_known
from .utils import get_file_hash_hex

HREF_PATTERN = re.compile(r"href=\\?\"([A-Za-z0-9/._\-]+)\\?\"")
SRC_PATTERN = re.compile(r"src=\\?\"([A-Za-z0-9/._\-]+)\\?\"")
POSTER_PATTERN = re.compile(r"poster=\\?\"([A-Za-z0-9/._\-]+)\\?\"")

application = Flask(__name__)
application.config.from_mapping(config)

CORS(application, resources={r"/api/v1/*": {"origins": "*"}})

application.register_blueprint(api_v1, url_prefix="/api/v1")  # API
application.register_blueprint(well_known, url_prefix="/.well-known")  # Well known files, used for deep linking verif.


@application.errorhandler(werkzeug.exceptions.NotFound)
def handle_not_found(_e):
    return jsonify({"message": "Not found"}), 404


@application.errorhandler(werkzeug.exceptions.BadRequest)
def handle_bad_request(e):
    return jsonify({"message": "Bad request", "errors": [str(e)]}), 400


@application.errorhandler(werkzeug.exceptions.RequestEntityTooLarge)
def handle_too_large(e):
    return jsonify({
        "message": (
            f"Request is too large. "
            f"Maximum request size: {application.config['MAX_CONTENT_LENGTH'] / (1024 ** 2):.1f} MB"
        ),
        "errors": [str(e)],
    }), 413


@application.errorhandler(werkzeug.exceptions.InternalServerError)
def handle_internal_server_error(e):
    return jsonify({"message": "Internal server error", "errors": [str(e)]}), 500


@application.errorhandler(AuthError)
def handle_auth_error(e):
    return jsonify(dict(e)), 401


@application.teardown_appcontext
def close_db(_exception):
    if (db := getattr(g, "_database", None)) is not None:
        db.close()


def _import_file(c: sqlite3.Cursor, file_path, file_match) -> str:
    checksum = get_file_hash_hex(file_path)

    c.execute("SELECT id FROM assets WHERE sha1_checksum = ?", (checksum,))
    r = c.fetchone()

    if r:
        # Asset already exists (checksums match), so return it instead of duplicating it
        return r[0]

    # Otherwise, make new asset since it isn't in the database

    file_name = f"{int(datetime.now().timestamp() * 1000)}-{secure_filename(file_match)}"
    new_file_path = pathlib.Path(application.config["ASSET_DIR"]) / file_name

    print("\tImporting", file_name)

    shutil.copyfile(file_path, new_file_path)

    new_id = str(uuid.uuid4())

    set_asset(new_id, {
        "id": new_id,
        "asset_type": detect_asset_type(new_file_path)[0],
        "file_name": file_name,
        "file_size": os.path.getsize(new_file_path),
        "sha1_checksum": checksum,
        "enabled": True,
    })

    return new_id


@application.cli.command("import_stations")
@click.argument("base_path")
@click.argument("stations_json")
@click.argument("manifest_json")
def import_stations(base_path, stations_json, manifest_json):
    with open(stations_json, "r") as stf:
        data = json.load(stf)

    with open(manifest_json, "r") as afh:
        manifest = json.load(afh)

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

            def _replace_assets(string: str, direct=False) -> str:
                if not string:
                    return string

                if direct:
                    matches = [string]
                    print(f"\tmatches: {matches}")
                else:
                    href_data = HREF_PATTERN.findall(string)
                    src_data = SRC_PATTERN.findall(string)
                    poster_data = POSTER_PATTERN.findall(string)
                    print(f"\t  href matches: {href_data}")
                    print(f"\t   src matches: {src_data}")
                    print(f"\tposter matches: {poster_data}")
                    matches = [*href_data, *src_data, *poster_data]

                for match in matches:
                    match_path = os.path.join(base_path, station_path, match)
                    if not os.path.exists(match_path):
                        print(f"\tMissing asset '{match}' (not in manifest.)")
                        continue

                    if match_path.endswith(".html"):
                        # Skip importing HTML files for now
                        # TODO: Import these as modals...
                        print("Skipping", match_path, "(unsupported asset type)")
                        continue

                    asset_id = _import_file(c, match_path, match)

                    if direct:
                        string = string.replace(match, asset_id)
                    else:
                        # Use a sort of multipurpose URL which resolves but can also be hijacked by the app
                        # TODO: This breaks when an asset has a name which is a subset of another one
                        string = string.replace(
                            match, f"{application.config['BASE_URL']}/api/v1/assets/{asset_id}/bytes")

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

            station_model.set_obj(str(uuid.uuid4()), {
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
