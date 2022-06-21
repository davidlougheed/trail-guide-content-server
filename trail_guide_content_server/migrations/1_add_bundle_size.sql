ALTER TABLE releases ADD COLUMN bundle_size INTEGER CHECK (bundle_size IS NULL OR bundle_size >= 0);
