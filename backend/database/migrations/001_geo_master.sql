CREATE EXTENSION IF NOT EXISTS postgis;

CREATE TABLE IF NOT EXISTS geo_cities (
    id BIGSERIAL PRIMARY KEY,
    code VARCHAR(24) NOT NULL UNIQUE,
    name VARCHAR(120) NOT NULL,
    state VARCHAR(120) NOT NULL,
    country VARCHAR(120) NOT NULL DEFAULT 'India',
    center_latitude DOUBLE PRECISION NOT NULL CHECK (center_latitude BETWEEN -90 AND 90),
    center_longitude DOUBLE PRECISION NOT NULL CHECK (center_longitude BETWEEN -180 AND 180),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS geo_wards (
    id BIGSERIAL PRIMARY KEY,
    city_id BIGINT NOT NULL REFERENCES geo_cities(id) ON DELETE CASCADE,
    code VARCHAR(40) NOT NULL,
    name VARCHAR(120) NOT NULL,
    population INTEGER CHECK (population IS NULL OR population >= 0),
    boundary GEOMETRY(POLYGON, 4326) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_geo_wards_city_code UNIQUE (city_id, code)
);

CREATE TABLE IF NOT EXISTS geo_monitoring_stations (
    id BIGSERIAL PRIMARY KEY,
    city_id BIGINT NOT NULL REFERENCES geo_cities(id) ON DELETE CASCADE,
    ward_id BIGINT REFERENCES geo_wards(id) ON DELETE SET NULL,
    code VARCHAR(40) NOT NULL UNIQUE,
    name VARCHAR(160) NOT NULL,
    latitude DOUBLE PRECISION NOT NULL CHECK (latitude BETWEEN -90 AND 90),
    longitude DOUBLE PRECISION NOT NULL CHECK (longitude BETWEEN -180 AND 180),
    location GEOMETRY(POINT, 4326) NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS geo_road_segments (
    id BIGSERIAL PRIMARY KEY,
    city_id BIGINT NOT NULL REFERENCES geo_cities(id) ON DELETE CASCADE,
    ward_id BIGINT REFERENCES geo_wards(id) ON DELETE SET NULL,
    code VARCHAR(60) NOT NULL,
    name VARCHAR(160) NOT NULL,
    road_class VARCHAR(60) NOT NULL,
    length_meters DOUBLE PRECISION CHECK (length_meters IS NULL OR length_meters >= 0),
    geometry GEOMETRY(LINESTRING, 4326) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_geo_road_segments_city_code UNIQUE (city_id, code)
);

CREATE TABLE IF NOT EXISTS geo_land_use_zones (
    id BIGSERIAL PRIMARY KEY,
    city_id BIGINT NOT NULL REFERENCES geo_cities(id) ON DELETE CASCADE,
    ward_id BIGINT REFERENCES geo_wards(id) ON DELETE SET NULL,
    code VARCHAR(60) NOT NULL,
    name VARCHAR(160) NOT NULL,
    category VARCHAR(80) NOT NULL,
    boundary GEOMETRY(POLYGON, 4326) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_geo_land_use_zones_city_code UNIQUE (city_id, code)
);

CREATE INDEX IF NOT EXISTS idx_geo_cities_code ON geo_cities (code);
CREATE INDEX IF NOT EXISTS idx_geo_wards_city ON geo_wards (city_id);
CREATE INDEX IF NOT EXISTS idx_geo_wards_boundary ON geo_wards USING GIST (boundary);
CREATE INDEX IF NOT EXISTS idx_geo_monitoring_stations_city ON geo_monitoring_stations (city_id);
CREATE INDEX IF NOT EXISTS idx_geo_monitoring_stations_ward ON geo_monitoring_stations (ward_id);
CREATE INDEX IF NOT EXISTS idx_geo_monitoring_stations_location ON geo_monitoring_stations USING GIST (location);
CREATE INDEX IF NOT EXISTS idx_geo_road_segments_city ON geo_road_segments (city_id);
CREATE INDEX IF NOT EXISTS idx_geo_road_segments_ward ON geo_road_segments (ward_id);
CREATE INDEX IF NOT EXISTS idx_geo_road_segments_geometry ON geo_road_segments USING GIST (geometry);
CREATE INDEX IF NOT EXISTS idx_geo_land_use_zones_city ON geo_land_use_zones (city_id);
CREATE INDEX IF NOT EXISTS idx_geo_land_use_zones_ward ON geo_land_use_zones (ward_id);
CREATE INDEX IF NOT EXISTS idx_geo_land_use_zones_boundary ON geo_land_use_zones USING GIST (boundary);
