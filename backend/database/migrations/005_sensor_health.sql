CREATE TABLE IF NOT EXISTS sensor_health_current (
    station_code VARCHAR(80) PRIMARY KEY,
    station_name VARCHAR(180) NOT NULL,
    ward_code VARCHAR(40),
    status VARCHAR(20) NOT NULL CHECK (status IN ('ONLINE', 'DELAYED', 'DEGRADED', 'OFFLINE')),
    data_quality_score DOUBLE PRECISION NOT NULL CHECK (data_quality_score BETWEEN 0 AND 1),
    last_reading_at TIMESTAMPTZ,
    evaluated_at TIMESTAMPTZ NOT NULL,
    missing_pollutants JSONB NOT NULL,
    invalid_pollutants JSONB NOT NULL,
    repeated_pollutants JSONB NOT NULL,
    abnormal_signals JSONB NOT NULL,
    reasons JSONB NOT NULL,
    is_reliable BOOLEAN NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS sensor_health_history (
    id BIGSERIAL PRIMARY KEY,
    station_code VARCHAR(80) NOT NULL,
    station_name VARCHAR(180) NOT NULL,
    ward_code VARCHAR(40),
    status VARCHAR(20) NOT NULL CHECK (status IN ('ONLINE', 'DELAYED', 'DEGRADED', 'OFFLINE')),
    data_quality_score DOUBLE PRECISION NOT NULL CHECK (data_quality_score BETWEEN 0 AND 1),
    last_reading_at TIMESTAMPTZ,
    evaluated_at TIMESTAMPTZ NOT NULL,
    missing_pollutants JSONB NOT NULL,
    invalid_pollutants JSONB NOT NULL,
    repeated_pollutants JSONB NOT NULL,
    abnormal_signals JSONB NOT NULL,
    reasons JSONB NOT NULL,
    is_reliable BOOLEAN NOT NULL,
    changed_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_sensor_health_current_status ON sensor_health_current (status);
CREATE INDEX IF NOT EXISTS idx_sensor_health_current_ward ON sensor_health_current (ward_code);
CREATE INDEX IF NOT EXISTS idx_sensor_health_history_station_changed
    ON sensor_health_history (station_code, changed_at);
CREATE INDEX IF NOT EXISTS idx_sensor_health_history_status ON sensor_health_history (status);
