from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, Float, ForeignKey, Index, JSON, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class EvidenceGraph(Base):
    __tablename__ = "evidence_graphs"

    id: Mapped[int] = mapped_column(primary_key=True)
    graph_uid: Mapped[str] = mapped_column(String(80), unique=True, nullable=False, index=True)
    hotspot_id: Mapped[int] = mapped_column(nullable=False, index=True)
    investigation_id: Mapped[int] = mapped_column(nullable=False, index=True)
    graph_version: Mapped[int] = mapped_column(nullable=False, default=1)
    metadata_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    nodes: Mapped[list["EvidenceGraphNode"]] = relationship(back_populates="graph", cascade="all, delete-orphan")
    edges: Mapped[list["EvidenceGraphEdge"]] = relationship(back_populates="graph", cascade="all, delete-orphan")

    __table_args__ = (Index("idx_evidence_graphs_investigation_version", "investigation_id", "graph_version"),)


class EvidenceGraphNode(Base):
    __tablename__ = "evidence_graph_nodes"

    id: Mapped[int] = mapped_column(primary_key=True)
    graph_id: Mapped[int] = mapped_column(ForeignKey("evidence_graphs.id", ondelete="CASCADE"), nullable=False, index=True)
    node_key: Mapped[str] = mapped_column(String(160), nullable=False)
    node_type: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    label: Mapped[str] = mapped_column(String(180), nullable=False)
    properties: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)

    graph: Mapped[EvidenceGraph] = relationship(back_populates="nodes")

    __table_args__ = (UniqueConstraint("graph_id", "node_key", name="uq_evidence_graph_nodes_graph_key"),)


class EvidenceGraphEdge(Base):
    __tablename__ = "evidence_graph_edges"

    id: Mapped[int] = mapped_column(primary_key=True)
    graph_id: Mapped[int] = mapped_column(ForeignKey("evidence_graphs.id", ondelete="CASCADE"), nullable=False, index=True)
    edge_key: Mapped[str] = mapped_column(String(220), nullable=False)
    source_node_key: Mapped[str] = mapped_column(String(160), nullable=False)
    target_node_key: Mapped[str] = mapped_column(String(160), nullable=False)
    edge_type: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    label: Mapped[str] = mapped_column(String(180), nullable=False)
    weight: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)
    properties: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)

    graph: Mapped[EvidenceGraph] = relationship(back_populates="edges")

    __table_args__ = (UniqueConstraint("graph_id", "edge_key", name="uq_evidence_graph_edges_graph_key"),)
