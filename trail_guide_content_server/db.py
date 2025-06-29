# A server for hosting a trail guide mobile app's content and data.
# Copyright (C) 2021-2025  David Lougheed
# See NOTICE for more information.

import json
import os.path
import pathlib
import re
import sqlite3

from collections import defaultdict
from flask import current_app, g
from sqlite3 import Connection, Row  # for typing hints and row factory
from typing import Any, Callable, Type

from .types import Asset, AssetWithIDAndUsage, Category, CategoryWithID

__all__ = [
    "get_db",
    "init_db",
    # categories
    "get_categories",
    "get_category",
    "set_category",
    "delete_category",
    # sections / stations
    "get_sections",
    "get_sections_with_stations",
    "get_section",
    "set_section",
    "delete_section",
    "station_model",
    # assets + asset types
    "get_asset_types",
    "get_assets",
    "get_assets_used",
    "get_asset",
    "set_asset",
    "delete_asset",
    # pages
    "page_model",
    # modals
    "modal_model",
    # layers
    "get_layer",
    "get_layers",
    "set_layer",
    "delete_layer",
    # releases
    "get_releases",
    "get_release",
    "get_latest_release",
    "set_release",
    # settings
    "get_settings",
    "set_settings",
    # feedback
    "get_feedback_items",
    "get_feedback_item",
    "set_feedback_item",
    # OTTs
    "get_ott",
    "set_ott",
]


SCHEMA_PATH = pathlib.Path(__file__).parent.resolve() / "schema.sql"

ASSET_URI_PATTERN_FRAGMENT = r"https?://[a-zA-Z\d.\-_:]{1,127}/api/v1/assets/([a-zA-Z\d\-]{36})/bytes/?"
ASSET_PATTERN = re.compile(
    rf'src=\\"({ASSET_URI_PATTERN_FRAGMENT})\\"|'
    rf'source=\\"({ASSET_URI_PATTERN_FRAGMENT})\\"|'
    rf'poster=\\"({ASSET_URI_PATTERN_FRAGMENT})\\"|'
    rf'href=\\"({ASSET_URI_PATTERN_FRAGMENT})\\"|'
    rf'"asset": ?"([a-z0-9\-]{{36}})"'
)


def get_db() -> Connection:
    db = getattr(g, "_database", None)
    if db is None:
        db = g._database = sqlite3.connect(current_app.config["DATABASE"], isolation_level=None)
        db.row_factory = Row
        c = db.cursor()
        c.execute("PRAGMA foreign_keys = ON")  # By default, FKs are off in SQLite; turn them on
    return db


def init_db():
    with open(SCHEMA_PATH, "r") as sf:
        current_app.logger.info(f"Initializing database at {current_app.config['DATABASE']}")
        current_app.logger.info(f"    Schema location: {SCHEMA_PATH}")
        get_db().executescript(sf.read())


def map_to_id(rows: list[sqlite3.Row]) -> list[Any]:
    return [r["id"] for r in rows]


def remove_blank(x: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(filter(lambda z: z != "", x))


# TODO: JSON schema
class ModelWithRevision:
    def __init__(
        self,
        table: str,
        get_fields: tuple[str, ...],
        set_fields: tuple[str, ...],
        asset_fields: tuple[str, ...],
        asset_search_fields: tuple[str, ...],
        insert_tuple_from_data_fn: Callable[[dict], tuple],
        row_to_dict: Callable[[Row], dict] | Type[dict],
        order: str = "",
        search_fields: tuple[str, ...] = ("id",),
    ):
        self.table: str = table
        self.get_fields: tuple[str, ...] = get_fields
        self.set_fields: tuple[str, ...] = set_fields
        self.asset_fields: tuple[str, ...] = asset_fields
        self.asset_search_fields: tuple[str, ...] = asset_search_fields
        self.insert_tuple_from_data_fn: Callable[[dict], tuple] | Type[dict] = insert_tuple_from_data_fn
        self._row_to_dict_partial: Callable[[Row], dict] = row_to_dict
        self._order = order
        self._search_fields = search_fields

    def row_to_dict(self, row: Row) -> dict:
        return {
            **self._row_to_dict_partial(row),
            "id": row["id"],
            "revision": {
                "number": row["revision"],
                "timestamp": row["revision_dt"],
                "message": row["revision_msg"],
            },
        }

    def get_one(self, obj_id: Any, include_deleted: bool = False, revision: int | None = None) -> dict | None:
        db = get_db()
        c = db.cursor()

        if revision is None:
            obj = c.execute(
                f"""
                SELECT td.id AS id, td.revision AS revision, revision_dt, revision_msg, {", ".join(self.get_fields)} 
                FROM {self.table} AS td INNER JOIN {self.table}_current_revision AS cr
                    ON td.id = cr.id AND td.revision = cr.revision
                WHERE td.id = ?{"" if include_deleted else " AND deleted = 0"}
                """,
                (obj_id,),
            ).fetchone()
        else:
            # Otherwise, return specified revision
            obj = c.execute(
                f"""
                SELECT td.id AS id, td.revision AS revision, revision_dt, revision_msg, {", ".join(self.get_fields)} 
                FROM {self.table} AS td 
                WHERE td.id = ? AND td.revision = ?{"" if include_deleted else " AND deleted = 0"}
                """,
                (obj_id, revision),
            ).fetchone()

        return self.row_to_dict(obj) if obj else None

    def get_all(self, include_deleted: bool = False, **kwargs) -> list[dict]:
        db = get_db()
        c = db.cursor()

        # Special field: enabled
        enabled_only = "enabled" in self.get_fields and kwargs.get("enabled", False)

        return list(
            map(
                self.row_to_dict,
                c.execute(
                    f"""
            SELECT td.id AS id, td.revision AS revision, revision_dt, revision_msg, {", ".join(self.get_fields)} 
            FROM {self.table} AS td INNER JOIN {self.table}_current_revision AS cr
                ON td.id = cr.id AND td.revision = cr.revision 
            WHERE 1{"" if include_deleted else " AND deleted = 0"}{" AND enabled = 1" if enabled_only else ""}
            {self._order}
            """
                ).fetchall(),
            )
        )

    def search(self, q: str, include_deleted: bool = False, **kwargs) -> list[dict]:
        db = get_db()
        c = db.cursor()

        # Special field: enabled
        enabled_only = "enabled" in self.get_fields and kwargs.get("enabled", False)

        q = f"%{q}%"
        search_conditions = " OR ".join((f"CAST(td.{sf} AS TEXT) LIKE :q" for sf in self._search_fields))

        return list(
            map(
                self.row_to_dict,
                c.execute(
                    f"""
            SELECT td.id AS id, td.revision AS revision, revision_dt, revision_msg, {", ".join(self.get_fields)} 
            FROM {self.table} AS td INNER JOIN {self.table}_current_revision AS cr
                ON td.id = cr.id AND td.revision = cr.revision 
            WHERE ({search_conditions})
            {"" if include_deleted else " AND deleted = 0"}{" AND enabled = 1" if enabled_only else ""}
            {self._order}
            """,
                    {"q": q},
                ).fetchall(),
            )
        )

    def _get_revision(self, c: sqlite3.Cursor, obj_id: Any) -> dict | None:
        # Get current revision
        c.execute(f"SELECT id, revision FROM {self.table}_current_revision WHERE id = ?", (obj_id,))
        current_revision = c.fetchone()
        return dict(current_revision) if current_revision else None

    def _get_new_revision(self, c: sqlite3.Cursor, obj_id: Any) -> int:
        current_revision = self._get_revision(c, obj_id)
        cr_num = (current_revision["revision"] + 1) if current_revision else 1
        return cr_num

    def _set_asset_usage(self, c: sqlite3.Cursor, obj_id: Any, revision: int, data: dict) -> None:
        asset_usages = set()

        for f in self.asset_fields:
            # TODO: Debug logging
            if fv := data.get(f):
                asset_usages.add(fv)

        for f in self.asset_search_fields:
            if fv := data.get(f):
                matches = [remove_blank(m)[-1] for m in ASSET_PATTERN.findall(json.dumps(fv))]
                asset_usages.update(set(matches))

        asset_usage_rows = [(obj_id, revision, a) for a in asset_usages if a.strip()]
        # TODO: Debug logging
        c.executemany(
            f"INSERT OR REPLACE INTO {self.table}_assets_used (obj, revision, asset) VALUES (?, ?, ?)", asset_usage_rows
        )

    def get_asset_usage(self, asset_id: str) -> dict[str, list[Any]]:
        """
        Fetch all usages (active and inactive, if relevant) of a particular asset by objects of this model.
        :param asset_id: ID of the asset to fetch usage details for.
        :return: A dictionary with keys being either 'active'/'inactive' (the latter is optional)
                 and a list of object IDs using the asset.
        """

        has_enabled = "enabled" in self.get_fields
        c = get_db().cursor()

        def _get_usage(enabled: int = 1) -> list[sqlite3.Row]:
            c.execute(
                f"""
                SELECT td.id AS id FROM {self.table} AS td 
                    INNER JOIN {self.table}_current_revision AS cr ON td.id = cr.id AND td.revision = cr.revision 
                    INNER JOIN {self.table}_assets_used AS au ON td.id = au.obj AND cr.revision = au.revision 
                WHERE au.asset = ? AND td.deleted = 0 AND {"td.enabled = ?" if has_enabled else "1"}
                """,
                (asset_id, enabled) if has_enabled else (asset_id,),
            )
            return c.fetchall()

        return {
            "active": map_to_id(_get_usage(1)),
            **(
                {
                    "inactive": map_to_id(_get_usage(0)),
                }
                if "enabled" in self.get_fields
                else {}
            ),
        }

    def set_obj(self, obj_id: Any, data: dict, extra_fields: tuple[str, ...] = (), extra_data: tuple[Any, ...] = ()):
        db = get_db()
        c = db.cursor()

        c.execute("BEGIN EXCLUSIVE TRANSACTION")

        # Insert object into database -----------

        cr_num = self._get_new_revision(c, obj_id)
        default_msg = "deleted" if data.get("deleted") else ("updated" if cr_num > 1 else "created")
        cr_msg = data.get("revision", {}).get("message", default_msg).strip() or default_msg

        c.execute(
            f"""
            INSERT INTO {self.table} (id, {", ".join((*self.set_fields, *extra_fields))}, revision, revision_msg) 
            VALUES ({", ".join(["?"] * (len(self.set_fields) + len(extra_fields) + 3))})
            """,
            (obj_id, *self.insert_tuple_from_data_fn(data), *extra_data, cr_num, cr_msg),
        )
        c.execute(
            f"INSERT OR REPLACE INTO {self.table}_current_revision (id, revision) VALUES (?, ?)", (obj_id, cr_num)
        )

        # Collect asset usage -------------------

        self._set_asset_usage(c, obj_id, cr_num, data)

        # Commit --------------------------------

        db.commit()

        return self.get_one(obj_id)

    def delete_obj(self, obj_id: Any) -> None:
        obj = self.get_one(obj_id)
        if not obj:  # not present or already deleted
            return

        self.set_obj(
            obj_id,
            {
                **obj,
                "revision": {**obj.get("revision", {}), "message": "deleted"},
            },
            extra_fields=("deleted",),
            extra_data=(1,),
        )

    def __str__(self) -> str:
        return self.table


# Access methods

# Nothing special to do here, just convert to dict
_row_to_category = dict


def get_categories() -> list[CategoryWithID]:
    c = get_db().cursor()
    q = c.execute("SELECT id, icon_svg FROM categories")
    return [_row_to_category(r) for r in q.fetchall()]


def get_category(category_id: str) -> CategoryWithID | None:
    c = get_db().cursor()
    q = c.execute("SELECT id, icon_svg FROM categories WHERE id = ?", (category_id,))
    r = q.fetchone()
    return _row_to_category(r) if r else None


def set_category(category_id: str, data: Category) -> CategoryWithID | None:
    db = get_db()
    c = db.cursor()
    c.execute("INSERT OR REPLACE INTO categories (id, icon_svg) VALUES (?, ?)", (category_id, data["icon_svg"]))
    db.commit()
    return get_category(category_id)


def delete_category(category_id: str) -> None:
    db = get_db()
    c = db.cursor()
    c.execute("DELETE FROM categories WHERE id = ?", (category_id,))
    db.commit()


# Nothing special to do here, just convert to dict
_row_to_section = dict


def get_sections() -> list[dict]:
    c = get_db().cursor()
    q = c.execute("SELECT id, title, color, rank FROM sections ORDER BY rank")
    return [_row_to_section(r) for r in q.fetchall()]


def get_section(section_id: str) -> dict | None:
    c = get_db().cursor()
    q = c.execute("SELECT id, title, color, rank FROM sections WHERE id = ?", (section_id,))
    r = q.fetchone()
    return _row_to_section(r) if r else None


def set_section(section_id: str, data: dict) -> dict | None:
    db = get_db()
    c = db.cursor()
    c.execute(
        "INSERT OR REPLACE INTO sections (id, title, color, rank) VALUES (?, ?, ?, ?)",
        (section_id, data["title"], data["color"], int(data["rank"])),
    )
    db.commit()
    return get_section(section_id)


def delete_section(section_id: str) -> None:
    db = get_db()
    c = db.cursor()
    c.execute("DELETE FROM sections WHERE id = ?", (section_id,))
    db.commit()


def _row_to_station(r: Row, prefix: str = "") -> dict:
    def p(s: str) -> str:
        return f"{prefix}.{s}" if prefix else s

    c_e = r[p("coordinates_utm_e")]
    c_n = r[p("coordinates_utm_n")]

    return {
        "title": r[p("title")],
        "long_title": r[p("long_title")],
        "subtitle": r[p("subtitle")],
        "coordinates_utm": {
            "crs": r[p("coordinates_utm_crs")],
            "zone": r[p("coordinates_utm_zone")],
            "east": int(c_e[:-1]) if c_e[-1] == "E" else int(c_e),
            "north": int(c_n[:-1]) if c_n[-1] == "N" else int(c_n),
        },
        "visible": {
            "from": r[p("visible_from")],
            "to": r[p("visible_to")],
        },
        "section": r[p("section")],
        "category": r[p("category")],
        "header_image": r[p("header_image")],
        "contents": json.loads(r[p("contents")]),
        "enabled": bool(r[p("enabled")]),
        "rank": r[p("rank")],
    }


def _station_data_to_insert_tuple(data: dict) -> tuple:
    return (
        data["title"],
        data["long_title"],
        data["subtitle"],
        # -----------------------------------------------------------------------------------------
        data["coordinates_utm"]["crs"],
        data["coordinates_utm"]["zone"],
        # -----------------------------------------------------------------------------------------
        # TODO: Some future SQLite migration - convert east/north strings to integers
        str(data["coordinates_utm"]["east"]).rstrip("E"),  # gradually convert to integer-strings
        str(data["coordinates_utm"]["north"]).rstrip("N"),  # gradually convert to integer-strings
        # -----------------------------------------------------------------------------------------
        data.get("visible", {}).get("from") or None,
        data.get("visible", {}).get("to") or None,
        # -----------------------------------------------------------------------------------------
        data["section"],
        data["category"],
        data.get("header_image") or None,
        json.dumps(data["contents"]),
        # -----------------------------------------------------------------------------------------
        data["enabled"],
        data["rank"],
    )


station_content_fields = (
    "title",
    "long_title",
    "subtitle",
    "coordinates_utm_crs",
    "coordinates_utm_zone",
    "coordinates_utm_e",
    "coordinates_utm_n",
    "visible_from",
    "visible_to",
    "section",
    "category",
    "header_image",
    "contents",
    "enabled",
    "rank",
)
station_model = ModelWithRevision(
    "stations",
    station_content_fields,
    station_content_fields,
    ("header_image",),
    ("contents",),
    _station_data_to_insert_tuple,
    _row_to_station,
    "ORDER BY section, rank",
    search_fields=("id", "title", "long_title"),
)


def get_sections_with_stations(enabled_only: bool = False) -> list[dict]:
    c = get_db().cursor()
    q = c.execute(f"""
        SELECT 
            sc.id AS sc_id,
            sc.title AS sc_title,
            sc.color AS sc_color,
            sc.rank AS sc_rank,
            
            st.id,
            st.title,
            st.long_title,
            st.subtitle,
            
            st.coordinates_utm_crs,
            st.coordinates_utm_zone,
            st.coordinates_utm_e,
            st.coordinates_utm_n,
            
            st.visible_from,
            st.visible_to,
            
            st.section,
            st.category,
            st.header_image,
            st.contents,
            
            st.enabled,
            st.rank
        FROM sections AS sc
        LEFT JOIN stations AS st ON sc.id = st.section
        INNER JOIN stations_current_revision AS cr ON st.id = cr.id AND st.revision = cr.revision
        WHERE st.deleted = 0 {"AND st.enabled = 1" if enabled_only else ""}
        ORDER BY sc.rank, st.rank""")

    sections_of_stations: defaultdict[str, dict] = defaultdict(lambda: {"data": []})

    for r in q.fetchall():
        section_id = r["sc_id"]
        sections_of_stations[section_id]["title"] = r["sc_title"]
        sections_of_stations[section_id]["color"] = r["sc_color"]
        sections_of_stations[section_id]["rank"] = r["sc_rank"]
        sections_of_stations[section_id]["data"].append({"id": r["id"], **_row_to_station(r)})

    return [{"id": k, **v} for k, v in sections_of_stations.items()]


def perma_delete_section_stations(section_id: str):
    db = get_db()
    c = db.cursor()
    # TODO: use model definition
    p = (section_id,)
    c.execute("DELETE FROM stations_current_revision WHERE id IN (SELECT id FROM stations WHERE section = ?)", p)
    c.execute("DELETE FROM stations_assets_used WHERE obj IN (SELECT id FROM stations WHERE section = ?)", p)
    c.execute("DELETE FROM stations WHERE section = ?", p)
    db.commit()


def get_asset_types():
    c = get_db().cursor()
    q = c.execute("SELECT id FROM asset_types")
    return [r["id"] for r in q.fetchall()]


def _row_to_asset(r: Row) -> AssetWithIDAndUsage:
    return {
        "id": r["id"],
        "asset_type": r["asset_type"],
        "file_name": r["file_name"],
        "file_size": r["file_size"],
        "sha1_checksum": r["sha1_checksum"],
        "times_used_by_all": r["times_used_by_all"],
        "times_used_by_enabled": r["times_used_by_enabled"],
    }


def get_asset_usage_query(only_enabled: bool) -> str:
    pages_extra = " AND pages.enabled = 1" if only_enabled else ""
    stations_extra = " AND stations.enabled = 1" if only_enabled else ""

    return f"""(
        SELECT COUNT(asset) AS times_used, asset FROM (
            SELECT asset FROM (
                SELECT mau.asset 
                FROM modals_assets_used AS mau 
                INNER JOIN modals 
                    ON mau.obj = modals.id
                INNER JOIN modals_current_revision AS cr 
                    ON cr.id = modals.id AND cr.revision = modals.revision 
                WHERE modals.deleted = 0
            )
            UNION ALL
            SELECT asset FROM (
                SELECT pau.asset
                FROM pages_assets_used AS pau
                INNER JOIN pages 
                    ON pau.obj = pages.id
                INNER JOIN pages_current_revision AS cr 
                    ON cr.id = pages.id AND cr.revision = pages.revision
                WHERE pages.deleted = 0{pages_extra}
            )
            UNION ALL
            SELECT asset FROM (
                SELECT sau.asset 
                FROM stations_assets_used AS sau
                INNER JOIN stations 
                    ON sau.obj = stations.id
                INNER JOIN stations_current_revision AS cr 
                    ON cr.id = stations.id AND cr.revision = stations.revision
                WHERE stations.deleted = 0{stations_extra}
            )
        )
        GROUP BY asset
    )"""


def get_assets() -> list[AssetWithIDAndUsage]:
    c = get_db().cursor()
    q = c.execute(f"""
        SELECT 
            id, 
            asset_type, 
            file_name, 
            file_size, 
            sha1_checksum, 
            IFNULL(asset_usage.times_used, 0) AS times_used_by_all,
            IFNULL(asset_usage_enabled.times_used, 0) AS times_used_by_enabled
        FROM assets 
        LEFT JOIN {get_asset_usage_query(only_enabled=False)} AS asset_usage 
               ON assets.id = asset_usage.asset
        LEFT JOIN {get_asset_usage_query(only_enabled=True)} AS asset_usage_enabled 
               ON assets.id = asset_usage_enabled.asset
        WHERE deleted = 0
    """)
    return [_row_to_asset(r) for r in q.fetchall()]


def get_assets_used(only_enabled: bool = False) -> list[AssetWithIDAndUsage]:
    """
    Gets all assets which are used by one or more enabled stations, pages, or modals.
    :return: A list of assets, represented by dictionaries.
    """

    c = get_db().cursor()
    q = c.execute(f"""
        SELECT 
            id, 
            asset_type, 
            file_name, 
            file_size, 
            sha1_checksum, 
            IFNULL(asset_usage.times_used, 0) AS times_used_by_all,
            IFNULL(asset_usage_enabled.times_used, 0) AS times_used_by_enabled
        FROM assets 
        INNER JOIN {get_asset_usage_query(only_enabled=False)} AS asset_usage 
            ON assets.id = asset_usage.asset
        {"INNER JOIN" if only_enabled else "LEFT JOIN"} {get_asset_usage_query(only_enabled=True)} 
            AS asset_usage_enabled 
            ON assets.id = asset_usage_enabled.asset
        WHERE deleted = 0
    """)
    return [_row_to_asset(r) for r in q.fetchall()]


def get_asset(asset_id: str) -> AssetWithIDAndUsage | None:
    c = get_db().cursor()
    q = c.execute(
        f"""
        SELECT 
            id, 
            asset_type, 
            file_name, 
            file_size, 
            sha1_checksum, 
            IFNULL(asset_usage.times_used, 0) AS times_used_by_all, 
            IFNULL(asset_usage_enabled.times_used, 0) AS times_used_by_enabled
        FROM assets
        LEFT JOIN {get_asset_usage_query(only_enabled=False)} AS asset_usage 
               ON assets.id = asset_usage.asset
        LEFT JOIN {get_asset_usage_query(only_enabled=True)} AS asset_usage_enabled
               ON assets.id = asset_usage_enabled.asset
        WHERE id = ? AND deleted = 0
        """,
        (asset_id,),
    )
    r = q.fetchone()
    return _row_to_asset(r) if r else None


def set_asset(asset_id: str, data: Asset) -> AssetWithIDAndUsage | None:
    db = get_db()
    c = db.cursor()
    c.execute(
        """
        INSERT OR REPLACE INTO assets (id, asset_type, file_name, file_size, sha1_checksum)
        VALUES (?, ?, ?, ?, ?)
    """,
        (asset_id, data["asset_type"], data["file_name"], data["file_size"], data["sha1_checksum"]),
    )
    db.commit()
    return get_asset(asset_id)


def delete_asset(asset_id: str) -> None:
    obj = get_asset(asset_id)
    if not obj:
        return

    db = get_db()
    c = db.cursor()
    c.execute("UPDATE assets SET deleted = 1 WHERE id = ?", (asset_id,))
    db.commit()


page_content_fields = (
    "title",
    "icon",
    "long_title",
    "subtitle",
    "header_image",
    "content",
    "enabled",
    "rank",
)
page_model = ModelWithRevision(
    "pages",
    page_content_fields,
    page_content_fields,
    ("header_image",),
    ("content",),
    lambda d: (
        d["title"],
        d["icon"],
        d["long_title"],
        d["subtitle"],
        d.get("header_image", None) or None,
        d["content"],
        d["enabled"],
        d["rank"],
    ),
    lambda r: {
        "title": r["title"],
        "icon": r["icon"],
        # ---------------------------------------
        "long_title": r["long_title"],
        "subtitle": r["subtitle"],
        "header_image": r["header_image"],
        "content": r["content"],
        # ---------------------------------------
        "enabled": bool(r["enabled"]),
        "rank": r["rank"],
    },
    "ORDER BY rank",
    search_fields=("id", "title", "long_title"),
)


modal_content_fields = ("title", "content", "close_text")
modal_model = ModelWithRevision(
    "modals",
    modal_content_fields,
    modal_content_fields,
    (),
    ("content",),
    lambda d: (d["title"], d["content"], d["close_text"]),
    dict,
    search_fields=("id", "title"),
)


def _row_to_layer(r: Row) -> dict:
    return {
        "id": r["id"],
        "name": r["name"],
        "geojson": json.loads(r["geojson"]),
        "enabled": bool(r["enabled"]),
        "rank": r["rank"],
    }


def get_layers() -> list[dict]:
    c = get_db().cursor()
    q = c.execute("SELECT id, name, geojson, enabled, rank FROM layers WHERE deleted = 0")
    return list(map(_row_to_layer, q))


def get_layer(layer_id: str, include_deleted: bool = False) -> dict | None:
    c = get_db().cursor()
    q = c.execute(
        f"""
        SELECT id, name, geojson, enabled, rank 
        FROM layers 
        WHERE id = ?{"" if include_deleted else " AND deleted = 0"}
        ORDER BY rank
        """,
        (layer_id,),
    )
    r = q.fetchone()
    return _row_to_layer(r) if r else None


def set_layer(layer_id: str, data: dict) -> dict | None:
    db = get_db()
    c = db.cursor()

    if isinstance(data["geojson"], dict):
        data["geojson"] = json.dumps(data["geojson"])

    c.execute(
        "INSERT OR REPLACE INTO layers (id, name, geojson, enabled, rank) VALUES (?, ?, ?, ?, ?)",
        (layer_id, data["name"], data["geojson"], int(data["enabled"]), int(data["rank"])),
    )
    db.commit()
    return get_layer(layer_id)


def delete_layer(layer_id) -> None:
    db = get_db()
    c = db.cursor()
    c.execute("UPDATE layers SET deleted = 1 WHERE id = ?", (layer_id,))
    db.commit()


# Nothing to transform
def _row_to_release(row: sqlite3.Row) -> dict:
    r = dict(row)
    if not r["bundle_size"]:
        # Get bundle size manually for pre-0.11.0 bundles
        try:
            r["bundle_size"] = os.path.getsize(r["bundle_path"])
        except FileNotFoundError:
            pass  # No bundle found on FS anymore, leave it null
    return r


def get_releases() -> list[dict]:
    c = get_db().cursor()
    q = c.execute("""
        SELECT version, release_notes, bundle_path, bundle_size, submitted_dt, published_dt
        FROM releases
        ORDER BY version DESC
    """)
    return list(map(_row_to_release, q))


def get_release(version: int) -> dict | None:
    c = get_db().cursor()
    q = c.execute(
        """
        SELECT version, release_notes, bundle_path, bundle_size, submitted_dt, published_dt 
        FROM releases 
        WHERE version = ?
        """,
        (version,),
    )
    r = q.fetchone()
    return _row_to_release(r) if r else None


def get_latest_release() -> dict | None:
    c = get_db().cursor()
    q = c.execute("SELECT MAX(version) AS latest_version FROM releases")
    r = q.fetchone()
    return get_release(r["latest_version"]) if r else None


def set_release(version: int | None, data: dict, commit: bool = True) -> dict | None:
    db = get_db()
    c = db.cursor()

    # we cannot do "insert or replace" with an auto-increment key

    if version is not None:
        c.execute(
            """
            UPDATE releases 
            SET release_notes = ?, bundle_path = ?, bundle_size = ?, submitted_dt = ?, published_dt = ?
            WHERE version = ?
            """,
            (
                data["release_notes"],
                data["bundle_path"],
                data.get("bundle_size"),
                data["submitted_dt"],
                data["published_dt"],
                version,
            ),
        )
    else:
        c.execute(
            """
            INSERT INTO releases (release_notes, bundle_path, bundle_size, submitted_dt, published_dt) 
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                data["release_notes"],
                data["bundle_path"],
                data.get("bundle_size"),
                data["submitted_dt"],
                data["published_dt"],
            ),
        )
        version = c.lastrowid

    if commit:
        db.commit()

    return get_release(version)


def get_settings() -> dict[str, str]:
    c = get_db().cursor()
    q = c.execute("SELECT setting_key, setting_value FROM settings")
    return {r[0]: r[1] for r in q.fetchall()}


def set_settings(data: dict[str, str]) -> dict[str, str]:
    db = get_db()
    c = db.cursor()
    for k, v in data.items():
        c.execute("INSERT OR REPLACE INTO settings (setting_key, setting_value) VALUES (?, ?)", (k, v))
    db.commit()
    return get_settings()


def _row_to_feedback(r: Row) -> dict:
    return {
        "id": r["id"],
        "from": {
            "name": r["from_name"],
            "email": r["from_email"],
        },
        "content": r["content"],
        "submitted": r["submitted"],
    }


def get_feedback_items() -> list[dict]:
    c = get_db().cursor()
    q = c.execute("SELECT id, from_name, from_email, content, submitted FROM feedback")
    return list(map(_row_to_feedback, q.fetchall()))


def get_feedback_item(feedback_id: str) -> dict | None:
    c = get_db().cursor()
    q = c.execute("SELECT id, from_name, from_email, content, submitted FROM feedback WHERE id = ?", (feedback_id,))
    r = q.fetchone()
    return _row_to_feedback(r) if r else None


def set_feedback_item(feedback_id: str, data: dict) -> dict:
    db = get_db()
    c = db.cursor()
    c.execute(
        "INSERT OR REPLACE INTO feedback (id, from_name, from_email, content, submitted) VALUES (?, ?, ?, ?, ?)",
        (feedback_id, data["from"]["name"], data["from"]["email"], data["content"], data["submitted"]),
    )
    db.commit()

    if fb := get_feedback_item(feedback_id):
        return fb

    raise Exception(f"Something went very wrong: feedback item '{feedback_id}' did not save correctly")


# Nothing to transform here
_tuple_to_ott = dict


def get_ott(token: str) -> dict | None:
    c = get_db().cursor()
    q = c.execute("SELECT token, scope, expiry FROM one_time_tokens WHERE token = ?", (token,))
    r = q.fetchone()
    return _tuple_to_ott(r) if r else None


def set_ott(token: str, data: dict) -> dict:
    db = get_db()
    c = db.cursor()
    c.execute(
        "INSERT OR REPLACE INTO one_time_tokens (token, scope, expiry) VALUES (?, ?, ?)",
        (token, data["scope"], data["expiry"]),
    )
    db.commit()

    if ott := get_ott(token):
        return ott

    raise Exception("Something went very wrong: OTT did not save correctly")
