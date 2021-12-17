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
    "set_asset",

    "get_pages",
    "get_page",
    "set_page",

    "get_modals",
    "get_modal",
    "set_modal",
    "delete_modal",

    "get_releases",
    "get_release",
    "set_release",

    "get_settings",
    "set_settings",

    "get_feedback_items",
    "get_feedback_item",
    "set_feedback_item",

    "get_ott",
    "set_ott",
]


def get_db() -> sqlite3.Connection:
    db = getattr(g, "_database", None)
    if db is None:
        db = g._database = sqlite3.connect(current_app.config["DATABASE"])
        c = db.cursor()
        c.execute("PRAGMA foreign_keys = ON")  # By default FKs are off in SQLite; turn them on
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
    q = c.execute("SELECT id, title, rank FROM sections ORDER BY rank")
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
        "visible": {
            "from": r[7],
            "to": r[8],
        },
        "section": r[9],
        "category": r[10],
        "header_image": r[11],
        "contents": json.loads(r[12]),
        "enabled": bool(r[13]),
        "rank": r[14],
    }


def get_sections_with_stations(enabled_only: bool = False) -> list[dict]:
    c = get_db().cursor()
    q = c.execute(f"""
        SELECT 
            sections.id, -- 0
            sections.title, -- 1
            
            stations.id, -- 2
            stations.title, -- 3
            stations.long_title, -- 4
            stations.subtitle, -- 5
            stations.coordinates_utm_zone, -- 6
            stations.coordinates_utm_ew, -- 7
            stations.coordinates_utm_ns, -- 8
            stations.visible_from, -- 9
            stations.visible_to, -- 10
            stations.section, -- 11
            stations.category, -- 12
            stations.header_image, -- 13
            stations.contents, -- 14
            
            stations.enabled, -- 15
            stations.rank, -- 16
            
            sections.rank -- 17
        FROM sections LEFT JOIN stations ON sections.id = stations.section
        {'WHERE stations.enabled = 1' if enabled_only else ''}
        ORDER BY sections.rank, stations.rank""")

    sections_of_stations = defaultdict(lambda: {"data": []})

    for r in q.fetchall():
        sections_of_stations[r[0]]["title"] = r[1]
        sections_of_stations[r[0]]["rank"] = r[17]
        sections_of_stations[r[0]]["data"].append(_tuple_to_station(r[2:17]))

    return [{"id": k, **v} for k, v in sections_of_stations.items()]


def get_stations(enabled_only: bool = False):
    c = get_db().cursor()
    q = c.execute(f"""
            SELECT 
                id, -- 0
                title, -- 1
                long_title, -- 2
                subtitle, -- 3
                coordinates_utm_zone, -- 4
                coordinates_utm_ew, -- 5
                coordinates_utm_ns, -- 6
                visible_from, -- 7
                visible_to, -- 8
                section, -- 9
                category, -- 10
                header_image, -- 11
                contents, -- 12
                enabled, -- 13
                rank -- 14
            FROM stations{' WHERE enabled = 1' if enabled_only else ''}
            ORDER BY rank""")

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
                    visible_from, -- 7
                    visible_to, -- 8
                    section, -- 9
                    category, -- 10
                    header_image, -- 11
                    contents, -- 12
                    enabled, -- 13
                    rank -- 14
                FROM stations
                WHERE id = ?""", (station_id,))

    r = q.fetchone()
    return _tuple_to_station(r) if r else None


def set_station(station_id: str, data: dict) -> dict:
    db = get_db()
    c = db.cursor()
    c.execute("""INSERT OR REPLACE INTO stations (
        id, -- 0
        title, -- 1
        long_title, -- 2
        subtitle, -- 3
        coordinates_utm_zone, -- 4
        coordinates_utm_ew, -- 5
        coordinates_utm_ns, -- 6
        visible_from, -- 7
        visible_to, -- 8
        section, -- 9
        category, -- 10
        header_image, -- 11
        contents, -- 12
        enabled, -- 13
        rank -- 14
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""", (
        station_id,
        data["title"],
        data["long_title"],
        data["subtitle"],

        data["coordinates_utm"]["zone"],

        # UTM Coordinates; these should be guaranteed to be set from the JSON schema checking earlier
        str(data["coordinates_utm"].get("east", data["coordinates_utm"].get("west"))) + (
            "E" if "east" in data["coordinates_utm"] else "W"),
        str(data["coordinates_utm"].get("north", data["coordinates_utm"].get("south"))) + (
            "N" if "north" in data["coordinates_utm"] else "S"),

        data.get("visible", {}).get("from") or None,
        data.get("visible", {}).get("to") or None,

        data["section"],
        data["category"],
        data.get("header_image") or None,
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
        "sha1_checksum": r[4],
        "enabled": bool(r[5]),
    }


def get_assets(filter_disabled: bool = False) -> list[dict]:
    c = get_db().cursor()
    q = c.execute(
        f"SELECT id, asset_type, file_name, file_size, sha1_checksum, enabled "
        f"FROM assets {'WHERE enabled = 1' if filter_disabled else ''}")
    return [_tuple_to_asset(r) for r in q.fetchall()]


def get_asset(asset_id: str) -> Optional[dict]:
    c = get_db().cursor()
    q = c.execute("SELECT id, asset_type, file_name, file_size, sha1_checksum, enabled FROM assets "
                  "WHERE id = ?", (asset_id,))
    r = q.fetchone()
    return _tuple_to_asset(r) if r else None


def set_asset(asset_id: str, data: dict) -> dict:
    db = get_db()
    c = db.cursor()
    c.execute(
        "INSERT OR REPLACE INTO assets (id, asset_type, file_name, file_size, sha1_checksum, enabled) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (asset_id, data["asset_type"], data["file_name"], data["file_size"], data["sha1_checksum"],
         int(data["enabled"])))
    db.commit()
    return get_asset(asset_id)


def _tuple_to_page(r: tuple) -> dict:
    return {
        "id": r[0],

        "title": r[1],
        "icon": r[2],

        "long_title": r[3],
        "subtitle": r[4],
        "header_image": r[5],
        "content": r[6],

        "enabled": bool(r[7]),
        "rank": r[8],
    }


def get_pages(enabled_only: bool = False) -> list[dict]:
    c = get_db().cursor()
    q = c.execute(
        "SELECT id, title, icon, long_title, subtitle, header_image, content, enabled, rank FROM pages" +
        (" WHERE enabled = 1" if enabled_only else ""))
    return list(map(_tuple_to_page, q))


def get_page(page_id: str) -> dict:
    c = get_db().cursor()
    q = c.execute("""
        SELECT 
          id, -- 0
          icon, -- 1
          title, -- 2
          long_title, -- 3
          subtitle, -- 4
          header_image, -- 5
          content, -- 6
          enabled, -- 7
          rank -- 8
        FROM pages WHERE id = ?
    """, (page_id,))
    p = q.fetchone()
    return _tuple_to_page(p) if p else None


def set_page(page_id: str, data: dict) -> dict:
    db = get_db()
    c = db.cursor()
    c.execute(
        "INSERT OR REPLACE INTO pages ("
        "  id, "
        "  title, "
        "  icon, "
        "  long_title, "
        "  subtitle, "
        "  header_image, "
        "  content, "
        "  enabled, "
        "  rank"
        ") VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            page_id,
            data["title"],
            data["icon"],
            data["long_title"],
            data["subtitle"],
            data.get("header_image", None) or None,
            data["content"],
            data["enabled"],
            data["rank"],
        )
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


def _tuple_to_release(r: tuple) -> dict:
    return {
        "version": r[0],
        "release_notes": r[1],
        "bundle_path": r[2],
        "submitted_dt": r[3],
        "published_dt": r[4],
    }


def get_releases():
    c = get_db().cursor()
    q = c.execute(
        "SELECT version, release_notes, bundle_path, submitted_dt, published_dt "
        "FROM releases ORDER BY version DESC")
    return list(map(_tuple_to_release, q))


def get_release(version: int):
    c = get_db().cursor()
    q = c.execute(
        "SELECT version, release_notes, bundle_path, submitted_dt, published_dt FROM releases WHERE version = ?",
        (version,))
    r = q.fetchone()
    return _tuple_to_release(r) if r else None


def set_release(version: Optional[int], data: dict) -> Optional[dict]:
    db = get_db()
    c = db.cursor()

    # we cannot do "insert or replace" with an auto-increment key

    if version is not None:
        c.execute(
            "UPDATE releases SET release_notes = ?, bundle_path = ?, submitted_dt = ?, published_dt = ? "
            "WHERE version = ?",
            (data["release_notes"], data["bundle_path"], data["submitted_dt"], data["published_dt"], version))
    else:
        c.execute(
            "INSERT INTO releases (release_notes, bundle_path, submitted_dt, published_dt) VALUES (?, ?, ?, ?)",
            (data["release_notes"], data["bundle_path"], data["submitted_dt"], data["published_dt"]))
        version = c.lastrowid

    db.commit()
    return get_release(version)


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


def _tuple_to_feedback(r: tuple) -> dict:
    return {
        "id": r[0],
        "from": {
            "name": r[1],
            "email": r[2],
        },
        "content": r[3],
        "submitted": r[4],
    }


def get_feedback_items() -> list[dict]:
    c = get_db().cursor()
    q = c.execute("SELECT id, from_name, from_email, content, submitted FROM feedback")
    return list(map(_tuple_to_feedback, q.fetchall()))


def get_feedback_item(feedback_id: str) -> dict:
    c = get_db().cursor()
    q = c.execute("SELECT id, from_name, from_email, content, submitted FROM feedback WHERE id = ?", (feedback_id,))
    r = q.fetchone()
    return _tuple_to_feedback(r) if r else None


def set_feedback_item(feedback_id: str, data: dict) -> dict:
    db = get_db()
    c = db.cursor()
    c.execute(
        "INSERT OR REPLACE INTO feedback (id, from_name, from_email, content, submitted) VALUES (?, ?, ?, ?, ?)",
        (feedback_id, data["from"]["name"], data["from"]["email"], data["content"], data["submitted"]))
    db.commit()
    return get_feedback_item(feedback_id)


def _tuple_to_ott(r: tuple) -> dict:
    return {
        "token": r[0],
        "scope": r[1],
        "expiry": r[2],
    }


def get_ott(token: str):
    c = get_db().cursor()
    q = c.execute("SELECT token, scope, expiry FROM one_time_tokens WHERE token = ?", (token,))
    r = q.fetchone()
    return _tuple_to_ott(r) if r else None


def set_ott(token: str, data: dict) -> dict:
    db = get_db()
    c = db.cursor()
    c.execute(
        "INSERT OR REPLACE INTO one_time_tokens (token, scope, expiry) VALUES (?, ?, ?)",
        (token, data["scope"], data["expiry"]))
    db.commit()
    return get_ott(token)
