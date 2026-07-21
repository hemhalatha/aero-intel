ALTER TABLE evidence_items
    ADD COLUMN IF NOT EXISTS data_quality_score DOUBLE PRECISION NOT NULL DEFAULT 1.0 CHECK (data_quality_score BETWEEN 0 AND 1),
    ADD COLUMN IF NOT EXISTS checked_at TIMESTAMPTZ NOT NULL DEFAULT NOW();

CREATE INDEX IF NOT EXISTS idx_evidence_items_investigation_source_type
    ON evidence_items (investigation_id, source_type);
CREATE INDEX IF NOT EXISTS idx_evidence_items_investigation_support
    ON evidence_items (investigation_id, support_direction);
CREATE INDEX IF NOT EXISTS idx_evidence_items_investigation_type
    ON evidence_items (investigation_id, evidence_type);

CREATE TABLE IF NOT EXISTS evidence_item_versions (
    id BIGSERIAL PRIMARY KEY,
    evidence_id BIGINT NOT NULL REFERENCES evidence_items(id) ON DELETE CASCADE,
    investigation_id BIGINT NOT NULL REFERENCES investigations(id) ON DELETE CASCADE,
    version_number INTEGER NOT NULL,
    collector_name VARCHAR(120) NOT NULL,
    source_type VARCHAR(80) NOT NULL,
    evidence_type VARCHAR(120) NOT NULL,
    source VARCHAR(120) NOT NULL,
    detected BOOLEAN NOT NULL,
    support_direction VARCHAR(20) NOT NULL CHECK (support_direction IN ('SUPPORTS', 'CONTRADICTS', 'NEUTRAL')),
    payload JSONB NOT NULL,
    observed_at TIMESTAMPTZ NOT NULL,
    collected_at TIMESTAMPTZ NOT NULL,
    confidence DOUBLE PRECISION NOT NULL CHECK (confidence BETWEEN 0 AND 1),
    data_quality_score DOUBLE PRECISION NOT NULL CHECK (data_quality_score BETWEEN 0 AND 1),
    checked_at TIMESTAMPTZ NOT NULL,
    changed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    change_reason VARCHAR(240),
    UNIQUE (evidence_id, version_number)
);

CREATE INDEX IF NOT EXISTS idx_evidence_item_versions_evidence_version
    ON evidence_item_versions (evidence_id, version_number);
CREATE INDEX IF NOT EXISTS idx_evidence_item_versions_investigation
    ON evidence_item_versions (investigation_id);