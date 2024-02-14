ALTER TABLE categories ADD COLUMN icon_svg TEXT NOT NULL DEFAULT '';
ALTER TABLE sections ADD COLUMN color VARCHAR(6) NOT NULL DEFAULT '000000';

ALTER TABLE stations RENAME COLUMN coordinates_utm_ew TO coordinates_utm_e;
ALTER TABLE stations RENAME COLUMN coordinates_utm_ns TO coordinates_utm_n;
