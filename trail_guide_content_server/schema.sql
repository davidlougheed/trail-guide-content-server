-- A server for hosting a trail guide mobile app's content and data.
-- Copyright (C) 2021  David Lougheed
--
-- This program is free software: you can redistribute it and/or modify
-- it under the terms of the GNU General Public License as published by
-- the Free Software Foundation, either version 3 of the License, or
-- (at your option) any later version.
--
-- This program is distributed in the hope that it will be useful,
-- but WITHOUT ANY WARRANTY; without even the implied warranty of
-- MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
-- GNU General Public License for more details.
--
-- You should have received a copy of the GNU General Public License
-- along with this program.  If not, see <https://www.gnu.org/licenses/>.

CREATE TABLE IF NOT EXISTS sections (
    id VARCHAR(31) PRIMARY KEY,
    title TEXT NOT NULL,
    rank INTEGER NOT NULL CHECK (rank >= 0)
);

-- Pre-populate sections
INSERT OR REPLACE INTO sections VALUES
    ('red', 'Red Trail', 0),
    ('blue', 'Blue Trail', 1),
    ('orange', 'Orange Trail', 2),
    ('green', 'Green Trail', 3),
    ('other', 'Main Facility and Off the Trails', 4);


CREATE TABLE IF NOT EXISTS categories (
    id VARCHAR(31) PRIMARY KEY
);

-- Pre-populate categories
INSERT OR REPLACE INTO categories VALUES
    ('culture'),
    ('environment'),
    ('research');


CREATE TABLE IF NOT EXISTS stations (
    id VARCHAR(36) PRIMARY KEY,

    title TEXT UNIQUE NOT NULL,
    long_title TEXT NOT NULL DEFAULT '',
    subtitle TEXT NOT NULL,

    coordinates_utm_zone TEXT NOT NULL DEFAULT '18N',
    coordinates_utm_ew TEXT NOT NULL,
    coordinates_utm_ns TEXT NOT NULL,

    -- month-day inclusive, left side of interval (or null)
    visible_from TEXT CHECK (visible_from IS NULL OR length(visible_from) = 5),
    -- month-day inclusive, right side of interval (or null)
    visible_to TEXT CHECK (visible_to IS NULL OR length(visible_to) = 5),

    section TEXT NOT NULL,
    category TEXT CHECK(category in ('culture', 'environment', 'research')),

    header_image TEXT,
    contents TEXT NOT NULL DEFAULT '[]',  -- JSON list of content objects

    enabled INTEGER NOT NULL CHECK (enabled in (0, 1)),
    rank INTEGER NOT NULL CHECK (rank >= 0),

    FOREIGN KEY (section) REFERENCES sections,
    FOREIGN KEY (header_image) REFERENCES assets
);


CREATE TABLE IF NOT EXISTS asset_types (
    id VARCHAR(31) PRIMARY KEY
);

-- Pre-populate asset types
INSERT OR REPLACE INTO asset_types VALUES
    ('image'),
    ('audio'),
    ('video'),
    ('video_text_track');


CREATE TABLE IF NOT EXISTS assets (
    id VARCHAR(36),
    asset_type VARCHAR(31) NOT NULL,
    file_name TEXT NOT NULL,
    file_size INTEGER NOT NULL CHECK (file_size > 0),

    enabled INTEGER NOT NULL CHECK (enabled in (0, 1)),

    FOREIGN KEY (asset_type) REFERENCES asset_types
);


CREATE TABLE IF NOT EXISTS pages (
    id VARCHAR(36) PRIMARY KEY,

    title VARCHAR(31) UNIQUE NOT NULL,
    long_title TEXT NOT NULL,
    subtitle TEXT NOT NULL,
    icon TEXT NOT NULL,  -- react-native cross-platform Expo icon (md-* or ios-* implicitly prefixed)

    content TEXT NOT NULL,  -- HTML

    enabled INTEGER NOT NULL CHECK (enabled in (0, 1)),
    rank INTEGER NOT NULL CHECK (rank >= 0)
);

-- Pre-populate pages with about page
INSERT OR REPLACE INTO pages VALUES
    ('about', 'About', 'Introduction to the Elbow Lake Interpretive App', 'help-circle-outline', '', 0, 1, 0);


CREATE TABLE IF NOT EXISTS modals (
    id VARCHAR(36) PRIMARY KEY,
    title TEXT NOT NULL,
    content TEXT NOT NULL,  -- HTML
    close_text TEXT NOT NULL DEFAULT 'Close'
);


CREATE TABLE IF NOT EXISTS settings (
    setting_key VARCHAR(63) PRIMARY KEY,
    setting_value TEXT
);

-- Pre-populate settings
INSERT OR REPLACE INTO settings VALUES
    ('terms_modal', NULL);
