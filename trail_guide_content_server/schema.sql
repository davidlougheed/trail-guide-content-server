-- A server for hosting a trail guide mobile app's content and data.
-- Copyright (C) 2021-2024  David Lougheed
-- See NOTICE for more information.

CREATE TABLE IF NOT EXISTS sections (
    id VARCHAR(31) PRIMARY KEY,
    title TEXT NOT NULL CHECK (length(title) > 0),
    color VARCHAR(6) NOT NULL,  -- RGB hex code for color
    rank INTEGER NOT NULL CHECK (rank >= 0)
);


CREATE TABLE IF NOT EXISTS categories (
    id VARCHAR(31) PRIMARY KEY,
    icon_svg TEXT NOT NULL
);


CREATE TABLE IF NOT EXISTS asset_types (
    id VARCHAR(31) PRIMARY KEY
);

-- Pre-populate asset types
INSERT OR IGNORE INTO asset_types VALUES
    ('image'),
    ('audio'),
    ('video'),
    ('video_text_track'),
    ('pdf');


CREATE TABLE IF NOT EXISTS assets (
    id VARCHAR(36) PRIMARY KEY,
    asset_type VARCHAR(31) NOT NULL,
    file_name TEXT NOT NULL,
    file_size INTEGER NOT NULL CHECK (file_size > 0),
    sha1_checksum VARCHAR(40) NOT NULL,  -- Checksum for checking for duplicates, etc.

    enabled INTEGER NOT NULL CHECK (enabled in (0, 1)),

    -- Deleted -> file is no longer available, but keep record
    deleted INTEGER NOT NULL CHECK (deleted in (0, 1)) DEFAULT 0,

    FOREIGN KEY (asset_type) REFERENCES asset_types
);


CREATE TABLE IF NOT EXISTS stations (
    id VARCHAR(36),

    revision INTEGER NOT NULL CHECK (revision > 0),
    revision_dt TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),  -- timestamp - parens to evaluate
    revision_msg TEXT NOT NULL DEFAULT 'created',  -- reason for latest revision

    title TEXT NOT NULL CHECK (length(title) > 0),
    long_title TEXT NOT NULL DEFAULT '',
    subtitle TEXT NOT NULL,

    coordinates_utm_crs TEXT NOT NULL DEFAULT 'NAD83',
    coordinates_utm_zone TEXT NOT NULL DEFAULT '18T',
    coordinates_utm_e TEXT NOT NULL,
    coordinates_utm_n TEXT NOT NULL,

    -- month-day inclusive, left side of interval (or null)
    visible_from TEXT CHECK (visible_from IS NULL OR length(visible_from) = 5),
    -- month-day inclusive, right side of interval (or null)
    visible_to TEXT CHECK (visible_to IS NULL OR length(visible_to) = 5),

    section TEXT NOT NULL,
    category TEXT NOT NULL,

    header_image TEXT,
    contents TEXT NOT NULL DEFAULT '[]',  -- JSON list of content objects

    enabled INTEGER NOT NULL CHECK (enabled in (0, 1)),
    rank INTEGER NOT NULL CHECK (rank >= 0),

    deleted INTEGER NOT NULL CHECK (deleted in (0, 1)) DEFAULT 0,

    PRIMARY KEY (id, revision),
    FOREIGN KEY (section) REFERENCES sections,
    FOREIGN KEY (category) REFERENCES categories ON DELETE RESTRICT,
    FOREIGN KEY (header_image) REFERENCES assets
);

CREATE TABLE IF NOT EXISTS stations_current_revision (
    id VARCHAR(36) PRIMARY KEY,
    revision INTEGER NOT NULL,

    FOREIGN KEY (id, revision) REFERENCES stations (id, revision) DEFERRABLE INITIALLY DEFERRED
);

CREATE TABLE IF NOT EXISTS stations_assets_used (
    obj VARCHAR(36),
    revision INTEGER NOT NULL,
    asset VARCHAR(36),

    PRIMARY KEY (obj, revision, asset),

    FOREIGN KEY (obj, revision) REFERENCES stations (id, revision) DEFERRABLE INITIALLY DEFERRED,
    FOREIGN KEY (asset) REFERENCES assets
);


CREATE TABLE IF NOT EXISTS pages (
    id VARCHAR(36),

    revision INTEGER NOT NULL CHECK (revision > 0),
    revision_dt TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),  -- timestamp - parens to evaluate
    revision_msg TEXT NOT NULL DEFAULT 'created',  -- reason for latest revision

    title VARCHAR(31) NOT NULL CHECK (length(title) > 0),
    icon TEXT NOT NULL,  -- react-native cross-platform Expo icon (md-* or ios-* implicitly prefixed)

    long_title TEXT NOT NULL CHECK (length(long_title) > 0),
    subtitle TEXT NOT NULL DEFAULT '',
    header_image VARCHAR(36),

    content TEXT NOT NULL,  -- HTML

    enabled INTEGER NOT NULL CHECK (enabled in (0, 1)),
    rank INTEGER NOT NULL CHECK (rank >= 0),

    -- Keep record when someone 'deletes' the page to keep the revision history, etc.
    deleted INTEGER NOT NULL CHECK (deleted in (0, 1)) DEFAULT 0,

    PRIMARY KEY (id, revision),
    FOREIGN KEY (header_image) REFERENCES assets
);

CREATE TABLE IF NOT EXISTS pages_current_revision (
    id VARCHAR(36) PRIMARY KEY,
    revision INTEGER NOT NULL,

    FOREIGN KEY (id, revision) REFERENCES pages (id, revision) DEFERRABLE INITIALLY DEFERRED
);

CREATE TABLE IF NOT EXISTS pages_assets_used (
    obj VARCHAR(36),
    revision INTEGER NOT NULL,
    asset VARCHAR(36),

    PRIMARY KEY (obj, revision, asset),

    FOREIGN KEY (obj, revision) REFERENCES pages (id, revision) DEFERRABLE INITIALLY DEFERRED,
    FOREIGN KEY (asset) REFERENCES assets
);

-- Pre-populate pages with about page
INSERT OR IGNORE INTO pages
    (id, revision, title, icon, long_title, subtitle, header_image, content, enabled, rank)
VALUES (
    'about',
    1,
    'About',
    'help-circle-outline',
    'About the app',
    '',
    NULL,
    '',
    1,
    0
);
INSERT OR IGNORE INTO pages_current_revision VALUES ('about', 1);


CREATE TABLE IF NOT EXISTS modals (
    id VARCHAR(36),  -- UUID

    revision INTEGER NOT NULL CHECK (revision > 0),
    revision_dt TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),  -- timestamp
    revision_msg TEXT NOT NULL DEFAULT 'created',  -- reason for latest revision

    title TEXT NOT NULL,
    content TEXT NOT NULL,  -- HTML
    close_text TEXT NOT NULL DEFAULT 'Close',

    -- Keep record when someone 'deletes' the page to keep the revision history, etc.
    deleted INTEGER NOT NULL CHECK (deleted in (0, 1)) DEFAULT 0,

    PRIMARY KEY (id, revision)
);

CREATE TABLE IF NOT EXISTS modals_current_revision (
    id VARCHAR(36) PRIMARY KEY,
    revision INTEGER NOT NULL,

    FOREIGN KEY (id, revision) REFERENCES modals (id, revision) DEFERRABLE INITIALLY DEFERRED
);

CREATE TABLE IF NOT EXISTS modals_assets_used (
    obj VARCHAR(36),
    revision INTEGER NOT NULL,
    asset VARCHAR(36),

    PRIMARY KEY (obj, revision, asset),

    FOREIGN KEY (obj, revision) REFERENCES modals (id, revision) DEFERRABLE INITIALLY DEFERRED,
    FOREIGN KEY (asset) REFERENCES assets
);


CREATE TABLE IF NOT EXISTS layers (
    id VARCHAR(36) PRIMARY KEY,  -- UUID
    name TEXT NOT NULL,
    geojson TEXT NOT NULL,

    enabled INTEGER NOT NULL CHECK (enabled in (0, 1)),
    rank INTEGER NOT NULL CHECK (rank >= 0),

    -- Keep record when someone 'deletes' the layer
    deleted INTEGER NOT NULL CHECK (deleted in (0, 1)) DEFAULT 0
);


CREATE TABLE IF NOT EXISTS releases (
    version INTEGER PRIMARY KEY AUTOINCREMENT,
    release_notes TEXT NOT NULL,

    bundle_path TEXT NOT NULL,
    -- bundle size in bytes, NULL is for legacy reasons/migrations:
    bundle_size INTEGER CHECK (bundle_size IS NULL OR bundle_size >= 0),

    submitted_dt TEXT NOT NULL,  -- ISO date + time
    published_dt TEXT   -- ISO date + time; NULL if not published yet
);


CREATE TABLE IF NOT EXISTS settings (
    setting_key VARCHAR(63) PRIMARY KEY,
    setting_value TEXT
);

-- Pre-populate settings
INSERT OR IGNORE INTO settings VALUES
    ('terms_modal', NULL);


CREATE TABLE IF NOT EXISTS feedback (
    id VARCHAR(36) PRIMARY KEY,  -- UUID
    from_name TEXT NOT NULL,
    from_email TEXT NOT NULL,
    content TEXT NOT NULL,
    submitted TEXT NOT NULL  -- ISO date + time
);


CREATE TABLE IF NOT EXISTS one_time_tokens (
    token VARCHAR(36) PRIMARY KEY,  -- UUID
    scope TEXT NOT NULL,  -- scope, simulating an OIDC token
    expiry TEXT NOT NULL  -- ISO date + time
);
