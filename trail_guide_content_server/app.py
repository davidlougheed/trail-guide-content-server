from flask import Flask

from .config import Config
from .db import get_db
from .routes import api_v1

application = Flask(__name__)
application.config.from_object(Config)

application.register_blueprint(api_v1, url_prefix="/api/v1")

# Initialize the DB on startup
with application.app_context(), open("./schema.sql", "r") as sf:
    application.logger.info(f"Initializing database at {application.config['DATABASE']}")
    db = get_db()
    db.executescript(sf.read())
