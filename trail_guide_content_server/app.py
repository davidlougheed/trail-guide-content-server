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

import pathlib
import werkzeug.exceptions

from flask import Flask, g, jsonify
from flask_cors import CORS

from .config import Config
from .db import get_db
from .routes import api_v1

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


@application.teardown_appcontext
def close_db(_exception):
    db = getattr(g, "_database", None)
    if db is not None:
        db.close()


SCHEMA_PATH = pathlib.Path(__file__).parent.resolve() / "schema.sql"


# Initialize the DB on startup
with application.app_context(), open(SCHEMA_PATH, "r") as sf:
    application.logger.info(f"Initializing database at {application.config['DATABASE']}")
    application.logger.info(f"    Schema location: {SCHEMA_PATH}")
    get_db().executescript(sf.read())
