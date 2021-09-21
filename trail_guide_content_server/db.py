import json
import sqlite3

from collections import defaultdict
from flask import current_app, g
from typing import Optional

__all__ = [
    "get_db",

    "get_categories",

    "get_sections",
    "get_sections_with_stations",
    "get_stations",

    "get_asset_types",
    "get_assets",
    "get_asset",

    "get_pages",
    "get_modals",
    "get_modal",

    "get_settings",
]


def get_db() -> sqlite3.Connection:
    db = getattr(g, "_database", None)
    if db is None:
        db = g._database = sqlite3.connect(current_app.config["DATABASE"])
    return db


# Access methods


def get_categories():
    c = get_db().cursor()
    q = c.execute("SELECT id FROM categories")
    return [r[0] for r in q.fetchall()]


def get_sections() -> list[dict]:
    c = get_db().cursor()
    q = c.execute("SELECT id, title, rank FROM sections ORDER BY rank ASC")
    return [{"id": r[0], "title": r[1], "rank": r[2]} for r in q.fetchall()]


def get_sections_with_stations() -> list[dict]:
    c = get_db().cursor()
    q = c.execute("""
        SELECT 
            sections.id, -- 0
            sections.title, -- 1
            
            stations.title, -- 2
            stations.long_title, -- 3
            stations.subtitle, -- 4
            stations.coordinates_utm_zone, -- 5
            stations.coordinates_utm_ew, -- 6
            stations.coordinates_utm_ns, -- 7
            stations.category, -- 8
            stations.contents, -- 9
            
            stations.enabled, -- 10
            stations.rank, -- 11
            
            sections.rank, -- 12
        FROM sections LEFT JOIN stations ON sections.id = stations.list_section
        ORDER BY sections.rank ASC, stations.rank ASC""")

    sections_of_stations = defaultdict(lambda: {"data": []})

    for r in q.fetchall():
        sections_of_stations[r[0]]["title"] = r[1]
        sections_of_stations[r[0]]["rank"] = r[12]
        sections_of_stations[r[0]]["data"].append({
            "title": r[2],
            "long_title": r[3],
            "subtitle": r[4],
            "coordinates_utm": {
                "zone": r[5],
                **({"east": int(r[6][:-1])} if r[6][-1] == "E" else {"west": int(r[6][:-1])}),
                **({"north": int(r[7][:-1])} if r[7][-1] == "N" else {"south": int(r[7][:-1])}),
            },
            "category": r[8],
            "contents": json.loads(r[9]),
            "enabled": bool(r[10]),
            "rank": r[11],
        })

    return [{"id": k, **v} for k, v in sections_of_stations.items()]


def get_stations():
    c = get_db().cursor()
    q = c.execute("""
            SELECT 
                id, -- 0
                title, -- 1
                long_title, -- 2
                subtitle, -- 3
                coordinates_utm_zone, -- 4
                coordinates_utm_ew, -- 5
                coordinates_utm_ns, -- 6
                category, -- 7
                contents, -- 8
                enabled, -- 9
            FROM stations
            ORDER BY rank ASC""")

    return [{
        "id": r[0],
        "title": r[1],
        "long_title": r[2],
        "subtitle": r[3],
        "coordinates_utm": {
            "zone": r[4],
            **({"east": int(r[5][:-1])} if r[5][-1] == "E" else {"west": int(r[5][:-1])}),
            **({"north": int(r[6][:-1])} if r[6][-1] == "N" else {"south": int(r[6][:-1])}),
        },
        "category": r[7],
        "contents": json.loads(r[8]),
        "enabled": bool(r[9]),
    } for r in q.fetchall()]


def get_asset_types():
    c = get_db().cursor()
    q = c.execute("SELECT id FROM asset_types")
    return [r[0] for r in q.fetchall()]


def _tuple_to_asset(r: tuple) -> dict:
    return {
        "id": r[0],
        "asset_type": r[1],
        "file_name": r[2],
        "file_size": r[3],
    }


def get_assets() -> list[dict]:
    c = get_db().cursor()
    q = c.execute("SELECT id, asset_type, file_name, file_size FROM assets")
    return [_tuple_to_asset(r) for r in q.fetchall()]


def get_asset(asset_id) -> Optional[dict]:
    c = get_db().cursor()
    q = c.execute("SELECT id, asset_type, file_name, file_size FROM assets WHERE id = ?", (asset_id,))
    r = q.fetchone()
    return _tuple_to_asset(r) if r else None


def get_pages() -> list[dict]:
    c = get_db().cursor()
    q = c.execute("SELECT id, title, long_title, subtitle, icon, content, enabled, rank FROM pages")
    return [{
        "id": r[0],

        "title": r[1],
        "long_title": r[2],
        "subtitle": r[3],
        "icon": r[4],
        "content": r[5],

        "enabled": bool(r[6]),
        "rank": r[7]
    } for r in q]


def _tuple_to_modal(r: tuple) -> dict:
    return {
        "id": r[0],
        "title": r[1],
        "content": r[2],
        "close_text": r[3],
    }


def get_modals() -> list[dict]:
    c = get_db().cursor()
    q = c.execute("SELECT id, title, content, close_text FROM modals")
    return list(map(_tuple_to_modal, q))


def get_modal(modal_id) -> Optional[dict]:
    c = get_db().cursor()
    q = c.execute("SELECT id, title, content, close_text FROM modals WHERE id = ?", (modal_id,))
    r = q.fetchone()
    return _tuple_to_modal(r) if r else None


def get_settings() -> dict:
    c = get_db().cursor()
    q = c.execute("SELECT setting_key, setting_value FROM modals")
    return {r[0]: r[1] for r in q.fetchall()}
