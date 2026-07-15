-- PostgreSQL schema for Module 1. Evidence records are retained so later
-- explanation, recommendation, and simulation modules can reference them.
CREATE TABLE evidence_bundles (
    id BIGSERIAL PRIMARY KEY,
    hotspot_id BIGINT NOT NULL,
    payload JSONB NOT NULL,
    received_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE source_attributions (
    id BIGSERIAL PRIMARY KEY,
    evidence_bundle_id BIGINT REFERENCES evidence_bundles(id) ON DELETE CASCADE,
    hotspot_id BIGINT NOT NULL,
    primary_source VARCHAR(80) NOT NULL,
    confidence NUMERIC(5,2) NOT NULL CHECK (confidence BETWEEN 0 AND 100),
    rankings JSONB NOT NULL,
    model_version VARCHAR(40) NOT NULL DEFAULT 'weighted-rules-v1',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_evidence_bundles_hotspot_received ON evidence_bundles (hotspot_id, received_at DESC);
CREATE INDEX idx_source_attributions_hotspot_created ON source_attributions (hotspot_id, created_at DESC);

CREATE TABLE attribution_explanations (
    id BIGSERIAL PRIMARY KEY,
    source_attribution_id BIGINT REFERENCES source_attributions(id) ON DELETE CASCADE,
    hotspot_id BIGINT NOT NULL,
    primary_source VARCHAR(80) NOT NULL,
    confidence NUMERIC(5,2) NOT NULL CHECK (confidence BETWEEN 0 AND 100),
    headline TEXT NOT NULL,
    summary TEXT NOT NULL,
    evidence JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_attribution_explanations_hotspot_created
    ON attribution_explanations (hotspot_id, created_at DESC);
