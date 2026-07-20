CREATE TABLE IF NOT EXISTS env_weather_forecasts (
    id BIGSERIAL PRIMARY KEY,
    source_id BIGINT NOT NULL REFERENCES env_data_sources(id) ON DELETE RESTRICT,
    location_code VARCHAR(80) NOT NULL,
    city VARCHAR(120) NOT NULL,
    latitude DOUBLE PRECISION NOT NULL CHECK (latitude BETWEEN -90 AND 90),
    longitude DOUBLE PRECISION NOT NULL CHECK (longitude BETWEEN -180 AND 180),
    generated_at TIMESTAMPTZ NOT NULL,
    forecast_for TIMESTAMPTZ NOT NULL,
    temperature_c DOUBLE PRECISION,
    relative_humidity_pct DOUBLE PRECISION CHECK (relative_humidity_pct IS NULL OR relative_humidity_pct BETWEEN 0 AND 100),
    wind_speed_kmh DOUBLE PRECISION CHECK (wind_speed_kmh IS NULL OR wind_speed_kmh >= 0),
    wind_direction_degrees DOUBLE PRECISION CHECK (wind_direction_degrees IS NULL OR wind_direction_degrees BETWEEN 0 AND 360),
    provider VARCHAR(80) NOT NULL,
    data_quality_status VARCHAR(40) NOT NULL DEFAULT 'valid' CHECK (data_quality_status IN ('valid', 'suspect', 'incomplete')),
    raw_payload JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_env_weather_forecast_location_generated_for_source UNIQUE (location_code, generated_at, forecast_for, source_id)
);

CREATE INDEX IF NOT EXISTS idx_env_weather_forecasts_location_for
    ON env_weather_forecasts (location_code, forecast_for);

CREATE INDEX IF NOT EXISTS idx_env_weather_forecasts_generated
    ON env_weather_forecasts (generated_at);
