import pathlib

from flask import Flask, g
from flask_cors import CORS

from .config import Config
from .db import get_db
from .routes import api_v1

application = Flask(__name__)
application.config.from_object(Config)

CORS(application, resources={r"/api/v1/*": {"origins": "*"}})

application.register_blueprint(api_v1, url_prefix="/api/v1")


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
