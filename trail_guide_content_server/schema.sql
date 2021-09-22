CREATE TABLE IF NOT EXISTS sections (
    id VARCHAR(15) PRIMARY KEY,
    title TEXT NOT NULL,
    rank INTEGER NOT NULL CHECK (rank >= 0)
);

-- Pre-populate sections
INSERT OR REPLACE INTO sections VALUES
    ("red", "Red Trail", 0),
    ("blue", "Blue Trail", 1),
    ("orange", "Orange Trail", 2),
    ("green", "Green Trail", 3),
    ("other", "Main Facility and Off the Trails", 4);


CREATE TABLE IF NOT EXISTS categories (
    id VARCHAR(15) PRIMARY KEY
);

-- Pre-populate categories
INSERT OR REPLACE INTO categories VALUES
    ("culture"),
    ("environment"),
    ("research");


CREATE TABLE IF NOT EXISTS stations (
    id VARCHAR(63) PRIMARY KEY,

    title TEXT UNIQUE NOT NULL,
    long_title TEXT NOT NULL DEFAULT "",
    subtitle TEXT NOT NULL,

    coordinates_utm_zone TEXT NOT NULL DEFAULT "18N",
    coordinates_utm_ew TEXT NOT NULL,
    coordinates_utm_ns TEXT NOT NULL,

    section TEXT NOT NULL,
    category TEXT CHECK(category in ("culture", "environment", "research")),

    contents TEXT NOT NULL DEFAULT "[]",  -- JSON list of content objects

    enabled INTEGER NOT NULL CHECK (enabled in (0, 1)),
    rank INTEGER NOT NULL CHECK (rank >= 0),

    FOREIGN KEY (section) REFERENCES sections
);


CREATE TABLE IF NOT EXISTS asset_types (
    id VARCHAR(15) PRIMARY KEY
);

-- Pre-populate asset types
INSERT OR REPLACE INTO asset_types VALUES
    ("image"),
    ("audio"),
    ("video");


CREATE TABLE IF NOT EXISTS assets (
    id VARCHAR(127),
    asset_type VARCHAR(15) NOT NULL,
    file_name TEXT NOT NULL,
    file_size INTEGER NOT NULL CHECK (file_size > 0),

    FOREIGN KEY (asset_type) REFERENCES asset_types
);


CREATE TABLE IF NOT EXISTS pages (
    id VARCHAR(15) PRIMARY KEY,

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
    ("about", "About", "Introduction to the Elbow Lake Interpretive App", "help-circle-outline", "", 0, 1, 0);


CREATE TABLE IF NOT EXISTS modals (
    id VARCHAR(15) PRIMARY KEY,
    title TEXT NOT NULL,
    content TEXT NOT NULL,  -- HTML
    close_text TEXT NOT NULL DEFAULT "Close"
);


CREATE TABLE IF NOT EXISTS settings (
    setting_key VARCHAR(63) PRIMARY KEY,
    setting_value TEXT
);

-- Pre-populate settings
INSERT OR REPLACE INTO settings VALUES
    ("terms_modal", NULL);
