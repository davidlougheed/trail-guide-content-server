from ..app import application
from ..db import station_model, page_model, modal_model
import sqlite3
import sys

db_path = sys.argv[1]


def main():
    conn = sqlite3.connect(db_path)
    c = conn.cursor()

    with application.app_context():
        for model in (station_model, page_model, modal_model):
            for obj in model.get_all():
                print(f"processing {model}.{obj['id']}", flush=True)
                # noinspection PyProtectedMember
                model._set_asset_usage(c, obj["id"], obj["revision"]["number"], obj)
            conn.commit()

    conn.close()


if __name__ == "__main__":
    main()
