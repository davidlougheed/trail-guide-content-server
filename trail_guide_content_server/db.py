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
    "get_section",
    "set_section",

    "get_stations",
    "get_station",
    "set_station",
    "delete_station",

    "get_asset_types",
    "get_assets",
    "get_asset",

    "get_pages",
    "get_page",
    "set_page",

    "get_modals",
    "get_modal",
    "set_modal",
    "delete_modal",

    "get_settings",
    "set_settings",
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


def _tuple_to_section(r: tuple) -> dict:
    return {"id": r[0], "title": r[1], "rank": r[2]}


def get_sections() -> list[dict]:
    c = get_db().cursor()
    q = c.execute("SELECT id, title, rank FROM sections ORDER BY rank ASC")
    return [_tuple_to_section(r) for r in q.fetchall()]


def get_section(section_id: str) -> dict:
    c = get_db().cursor()
    q = c.execute("SELECT id, title, rank FROM sections WHERE id = ?", (section_id,))
    r = q.fetchone()
    return _tuple_to_section(r) if r else None


def set_section(section_id: str, data: dict) -> dict:
    db = get_db()
    c = db.cursor()
    c.execute(
        "INSERT OR REPLACE INTO sections (id, title, rank) VALUES (?, ?, ?)",
        (section_id, data["title"], data["rank"]))
    db.commit()
    return get_section(section_id)


def _tuple_to_station(r: tuple) -> dict:
    return {
        "id": r[0],
        "title": r[1],
        "long_title": r[2],
        "subtitle": r[3],
        "coordinates_utm": {
            "zone": r[4],
            **({"east": int(r[5][:-1])} if r[5][-1] == "E" else {"west": int(r[5][:-1])}),
            **({"north": int(r[6][:-1])} if r[6][-1] == "N" else {"south": int(r[6][:-1])}),
        },
        "section": r[7],
        "category": r[8],
        "contents": json.loads(r[9]),
        "enabled": bool(r[10]),
        "rank": bool(r[11]),
    }


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
            stations.section, -- 8
            stations.category, -- 9
            stations.contents, -- 10
            
            stations.enabled, -- 11
            stations.rank, -- 12
            
            sections.rank, -- 13
        FROM sections LEFT JOIN stations ON sections.id = stations.list_section
        ORDER BY sections.rank ASC, stations.rank ASC""")

    sections_of_stations = defaultdict(lambda: {"data": []})

    for r in q.fetchall():
        sections_of_stations[r[0]]["title"] = r[1]
        sections_of_stations[r[0]]["rank"] = r[13]
        sections_of_stations[r[0]]["data"].append(_tuple_to_station(r[2:13]))

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
                section, -- 7
                category, -- 8
                contents, -- 9
                enabled, -- 10
                rank -- 11
            FROM stations
            ORDER BY rank ASC""")

    return [_tuple_to_station(r) for r in q.fetchall()]


def get_station(station_id: str):
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
                    section, -- 7
                    category, -- 8
                    contents, -- 9
                    enabled, -- 10
                    rank, -- 11
                FROM stations
                WHERE id = ?""", (station_id,))

    r = q.fetchone()
    return _tuple_to_station(r) if r else None


def set_station(station_id: str, data: dict) -> dict:
    db = get_db()
    c = db.cursor()
    c.execute("""INSERT OR REPLACE INTO stations ("
        id, -- 0
        title, -- 1
        long_title, -- 2
        subtitle, -- 3
        coordinates_utm_zone, -- 4
        coordinates_utm_ew, -- 5
        coordinates_utm_ns, -- 6
        section, -- 7
        category, -- 8
        contents, -- 9
        enabled, -- 10
        rank -- 11
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""", (
        station_id,
        data["title"],
        data["long_title"],
        data["subtitle"],
        data["coordinates_utm"]["zone"],
        data["coordinates_utm"].get("east", data["coordinates_utm"].get("west")),
        data["coordinates_utm"].get("north", data["coordinates_utm"].get("south")),
        data["section"],
        data["category"],
        json.dumps(data["contents"]),
        data["enabled"],
        data["rank"],
    ))
    db.commit()
    return get_station(station_id)


def delete_station(station_id: str):
    db = get_db()
    c = db.cursor()
    c.execute("DELETE FROM stations WHERE id = ?", (station_id,))
    db.commit()


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


def get_asset(asset_id: str) -> Optional[dict]:
    c = get_db().cursor()
    q = c.execute("SELECT id, asset_type, file_name, file_size FROM assets WHERE id = ?", (asset_id,))
    r = q.fetchone()
    return _tuple_to_asset(r) if r else None


def _tuple_to_page(r: tuple) -> dict:
    return {
        "id": r[0],

        "title": r[1],
        "long_title": r[2],
        "subtitle": r[3],
        "icon": r[4],
        "content": r[5],

        "enabled": bool(r[6]),
        "rank": r[7],
    }


def get_pages() -> list[dict]:
    c = get_db().cursor()
    q = c.execute("SELECT id, title, long_title, subtitle, icon, content, enabled, rank FROM pages")
    return list(map(_tuple_to_page, q))


def get_page(page_id: str) -> dict:
    c = get_db().cursor()
    q = c.execute(
        "SELECT id, title, long_title, subtitle, icon, content, enabled, rank FROM pages WHERE id = ?", (page_id,))
    p = q.fetchone()
    return _tuple_to_page(p) if p else None


def set_page(page_id: str, data: dict) -> dict:
    db = get_db()
    c = db.cursor()
    c.execute(
        "INSERT OR REPLACE INTO pages (id, title, long_title, subtitle, icon, content, enabled, rank) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (page_id, data["title"], data["long_title"], data["subtitle"], data["icon"], data["content"], data["enabled"],
         data["rank"])
    )
    db.commit()
    return get_page(page_id)


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


def get_modal(modal_id: str) -> Optional[dict]:
    c = get_db().cursor()
    q = c.execute("SELECT id, title, content, close_text FROM modals WHERE id = ?", (modal_id,))
    r = q.fetchone()
    return _tuple_to_modal(r) if r else None


def set_modal(modal_id: str, data: dict) -> Optional[dict]:
    db = get_db()
    c = db.cursor()
    c.execute(
        "INSERT OR REPLACE INTO modals (id, title, content, close_text) VALUES (?, ?, ?, ?)",
        (modal_id, data["title"], data["content"], data["close_text"]))
    db.commit()
    return get_modal(modal_id)


def delete_modal(modal_id):
    db = get_db()
    c = db.cursor()
    c.execute("DELETE FROM modals WHERE id = ?", (modal_id,))
    db.commit()


def get_settings() -> dict:
    c = get_db().cursor()
    q = c.execute("SELECT setting_key, setting_value FROM settings")
    return {r[0]: r[1] for r in q.fetchall()}


def set_settings(data: dict) -> dict:
    db = get_db()
    c = db.cursor()
    for k, v in data.items():
        c.execute("INSERT OR REPLACE INTO settings (setting_key, setting_value) VALUES (?, ?)", (k, v))
    db.commit()
    return get_settings()
