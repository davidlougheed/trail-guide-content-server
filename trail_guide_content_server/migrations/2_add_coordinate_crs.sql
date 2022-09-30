ALTER TABLE stations ADD COLUMN coordinates_utm_crs TEXT NOT NULL DEFAULT 'NAD83';
UPDATE stations SET coordinates_utm_zone = '18T' WHERE coordinates_utm_zone = '18N';
