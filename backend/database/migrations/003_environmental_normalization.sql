ALTER TABLE env_air_quality_readings
    ADD COLUMN IF NOT EXISTS external_station_id VARCHAR(120),
    ADD COLUMN IF NOT EXISTS ward_code VARCHAR(40),
    ADD COLUMN IF NOT EXISTS data_quality_status VARCHAR(40) NOT NULL DEFAULT 'valid';

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'chk_env_aq_data_quality_status'
    ) THEN
        ALTER TABLE env_air_quality_readings
            ADD CONSTRAINT chk_env_aq_data_quality_status
            CHECK (data_quality_status IN ('valid', 'suspect', 'incomplete')) NOT VALID;
    END IF;
END
$$;

CREATE TABLE IF NOT EXISTS env_rejected_records (
    id BIGSERIAL PRIMARY KEY,
    provider VARCHAR(80) NOT NULL,
    external_station_id VARCHAR(120),
    observed_at TIMESTAMPTZ,
    pollutant VARCHAR(40),
    reason VARCHAR(120) NOT NULL,
    raw_payload JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_env_aq_ward_observed ON env_air_quality_readings (ward_code, observed_at);
CREATE INDEX IF NOT EXISTS idx_env_aq_quality_status ON env_air_quality_readings (data_quality_status);
CREATE INDEX IF NOT EXISTS idx_env_rejected_records_provider_reason ON env_rejected_records (provider, reason);
CREATE INDEX IF NOT EXISTS idx_env_rejected_records_observed ON env_rejected_records (observed_at);
