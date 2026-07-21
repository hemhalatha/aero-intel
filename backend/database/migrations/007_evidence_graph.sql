CREATE TABLE IF NOT EXISTS evidence_graphs (
    id SERIAL PRIMARY KEY,
    graph_uid VARCHAR(80) NOT NULL UNIQUE,
    hotspot_id INTEGER NOT NULL,
    investigation_id INTEGER NOT NULL,
    graph_version INTEGER NOT NULL DEFAULT 1,
    metadata_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    generated_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_evidence_graphs_hotspot ON evidence_graphs (hotspot_id);
CREATE INDEX IF NOT EXISTS idx_evidence_graphs_investigation ON evidence_graphs (investigation_id);
CREATE INDEX IF NOT EXISTS idx_evidence_graphs_investigation_version ON evidence_graphs (investigation_id, graph_version);

CREATE TABLE IF NOT EXISTS evidence_graph_nodes (
    id SERIAL PRIMARY KEY,
    graph_id INTEGER NOT NULL REFERENCES evidence_graphs(id) ON DELETE CASCADE,
    node_key VARCHAR(160) NOT NULL,
    node_type VARCHAR(40) NOT NULL,
    label VARCHAR(180) NOT NULL,
    properties JSONB NOT NULL DEFAULT '{}'::jsonb,
    CONSTRAINT uq_evidence_graph_nodes_graph_key UNIQUE (graph_id, node_key)
);

CREATE INDEX IF NOT EXISTS idx_evidence_graph_nodes_graph ON evidence_graph_nodes (graph_id);
CREATE INDEX IF NOT EXISTS idx_evidence_graph_nodes_type ON evidence_graph_nodes (node_type);

CREATE TABLE IF NOT EXISTS evidence_graph_edges (
    id SERIAL PRIMARY KEY,
    graph_id INTEGER NOT NULL REFERENCES evidence_graphs(id) ON DELETE CASCADE,
    edge_key VARCHAR(220) NOT NULL,
    source_node_key VARCHAR(160) NOT NULL,
    target_node_key VARCHAR(160) NOT NULL,
    edge_type VARCHAR(40) NOT NULL,
    label VARCHAR(180) NOT NULL,
    weight DOUBLE PRECISION NOT NULL DEFAULT 1.0,
    properties JSONB NOT NULL DEFAULT '{}'::jsonb,
    CONSTRAINT uq_evidence_graph_edges_graph_key UNIQUE (graph_id, edge_key)
);

CREATE INDEX IF NOT EXISTS idx_evidence_graph_edges_graph ON evidence_graph_edges (graph_id);
CREATE INDEX IF NOT EXISTS idx_evidence_graph_edges_type ON evidence_graph_edges (edge_type);
