CREATE TABLE IF NOT EXISTS env_data_sources (
    id BIGSERIAL PRIMARY KEY,
    code VARCHAR(80) NOT NULL UNIQUE,
    name VARCHAR(180) NOT NULL,
    source_type VARCHAR(80) NOT NULL,
    provenance VARCHAR(40) NOT NULL CHECK (provenance IN ('real_public', 'controlled_demo')),
    license VARCHAR(120) NOT NULL,
    url TEXT NOT NULL,
    notes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS env_air_quality_readings (
    id BIGSERIAL PRIMARY KEY,
    source_id BIGINT NOT NULL REFERENCES env_data_sources(id) ON DELETE RESTRICT,
    station_code VARCHAR(80) NOT NULL,
    station_name VARCHAR(180) NOT NULL,
    city VARCHAR(120) NOT NULL,
    state VARCHAR(120) NOT NULL,
    observed_at TIMESTAMPTZ NOT NULL,
    pollutant VARCHAR(40) NOT NULL,
    value DOUBLE PRECISION NOT NULL CHECK (value >= 0),
    unit VARCHAR(40) NOT NULL,
    averaging_period VARCHAR(40) NOT NULL,
    raw_payload JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_env_aq_station_time_pollutant_source UNIQUE (station_code, observed_at, pollutant, source_id)
);

CREATE TABLE IF NOT EXISTS env_weather_observations (
    id BIGSERIAL PRIMARY KEY,
    source_id BIGINT NOT NULL REFERENCES env_data_sources(id) ON DELETE RESTRICT,
    location_code VARCHAR(80) NOT NULL,
    city VARCHAR(120) NOT NULL,
    latitude DOUBLE PRECISION NOT NULL CHECK (latitude BETWEEN -90 AND 90),
    longitude DOUBLE PRECISION NOT NULL CHECK (longitude BETWEEN -180 AND 180),
    observed_at TIMESTAMPTZ NOT NULL,
    temperature_c DOUBLE PRECISION,
    relative_humidity_pct DOUBLE PRECISION CHECK (relative_humidity_pct IS NULL OR relative_humidity_pct BETWEEN 0 AND 100),
    wind_speed_kmh DOUBLE PRECISION CHECK (wind_speed_kmh IS NULL OR wind_speed_kmh >= 0),
    wind_direction_degrees DOUBLE PRECISION CHECK (wind_direction_degrees IS NULL OR wind_direction_degrees BETWEEN 0 AND 360),
    raw_payload JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_env_weather_location_time_source UNIQUE (location_code, observed_at, source_id)
);

CREATE TABLE IF NOT EXISTS env_controlled_scenarios (
    id BIGSERIAL PRIMARY KEY,
    source_id BIGINT NOT NULL REFERENCES env_data_sources(id) ON DELETE RESTRICT,
    scenario_key VARCHAR(80) NOT NULL UNIQUE,
    title VARCHAR(180) NOT NULL,
    category VARCHAR(80) NOT NULL CHECK (category IN ('traffic_anomaly', 'construction_permit', 'industrial_activity')),
    city VARCHAR(120) NOT NULL,
    ward_code VARCHAR(40),
    station_code VARCHAR(80),
    starts_at TIMESTAMPTZ NOT NULL,
    ends_at TIMESTAMPTZ NOT NULL,
    severity DOUBLE PRECISION NOT NULL CHECK (severity BETWEEN 0 AND 1),
    description TEXT NOT NULL,
    evidence JSONB NOT NULL,
    provenance VARCHAR(40) NOT NULL DEFAULT 'controlled_demo' CHECK (provenance = 'controlled_demo'),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CHECK (ends_at > starts_at)
);

CREATE INDEX IF NOT EXISTS idx_env_data_sources_provenance ON env_data_sources (provenance);
CREATE INDEX IF NOT EXISTS idx_env_aq_station_observed ON env_air_quality_readings (station_code, observed_at);
CREATE INDEX IF NOT EXISTS idx_env_aq_pollutant_observed ON env_air_quality_readings (pollutant, observed_at);
CREATE INDEX IF NOT EXISTS idx_env_weather_location_observed ON env_weather_observations (location_code, observed_at);
CREATE INDEX IF NOT EXISTS idx_env_controlled_scenarios_window ON env_controlled_scenarios (starts_at, ends_at);
CREATE INDEX IF NOT EXISTS idx_env_controlled_scenarios_category ON env_controlled_scenarios (category);
