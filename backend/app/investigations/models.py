from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, Float, ForeignKey, Index, JSON, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Investigation(Base):
    __tablename__ = "investigations"

    id: Mapped[int] = mapped_column(primary_key=True)
    investigation_uid: Mapped[str] = mapped_column(String(80), unique=True, nullable=False, index=True)
    hotspot_id: Mapped[int] = mapped_column(nullable=False, index=True)
    hotspot_uid: Mapped[str | None] = mapped_column(String(80), index=True)
    ward_code: Mapped[str | None] = mapped_column(String(40), index=True)
    station_code: Mapped[str | None] = mapped_column(String(80), index=True)
    status: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    environmental_context: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    last_collection_started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_collection_completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    collector_runs: Mapped[list["EvidenceCollectionRun"]] = relationship(back_populates="investigation")
    evidence_items: Mapped[list["EvidenceItem"]] = relationship(back_populates="investigation")
    events: Mapped[list["InvestigationEvent"]] = relationship(back_populates="investigation")

    __table_args__ = (
        Index("idx_investigations_hotspot_status", "hotspot_id", "status"),
        Index("idx_investigations_ward_status", "ward_code", "status"),
    )


class EvidenceCollectionRun(Base):
    __tablename__ = "evidence_collection_runs"

    id: Mapped[int] = mapped_column(primary_key=True)
    investigation_id: Mapped[int] = mapped_column(ForeignKey("investigations.id", ondelete="CASCADE"), nullable=False)
    collector_name: Mapped[str] = mapped_column(String(120), nullable=False)
    status: Mapped[str] = mapped_column(String(40), nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    error_message: Mapped[str | None] = mapped_column(Text)
    evidence_count: Mapped[int] = mapped_column(nullable=False, default=0)
    request_reason: Mapped[str | None] = mapped_column(String(240))

    investigation: Mapped[Investigation] = relationship(back_populates="collector_runs")

    __table_args__ = (
        Index("idx_evidence_collection_runs_investigation", "investigation_id"),
        Index("idx_evidence_collection_runs_status", "status"),
    )


class EvidenceItem(Base):
    __tablename__ = "evidence_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    investigation_id: Mapped[int] = mapped_column(ForeignKey("investigations.id", ondelete="CASCADE"), nullable=False)
    collector_name: Mapped[str] = mapped_column(String(120), nullable=False)
    source_type: Mapped[str] = mapped_column(String(80), nullable=False, default="unknown")
    evidence_type: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    source: Mapped[str] = mapped_column(String(120), nullable=False)
    detected: Mapped[bool] = mapped_column(nullable=False, default=True)
    support_direction: Mapped[str] = mapped_column(String(20), nullable=False, default="NEUTRAL")
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    collected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    data_quality_score: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)
    checked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    investigation: Mapped[Investigation] = relationship(back_populates="evidence_items")

    __table_args__ = (
        Index("idx_evidence_items_investigation_collected", "investigation_id", "collected_at"),
        Index("idx_evidence_items_source", "source"),
        Index("idx_evidence_items_investigation_source_type", "investigation_id", "source_type"),
        Index("idx_evidence_items_investigation_support", "investigation_id", "support_direction"),
    )


class EvidenceItemVersion(Base):
    __tablename__ = "evidence_item_versions"

    id: Mapped[int] = mapped_column(primary_key=True)
    evidence_id: Mapped[int] = mapped_column(ForeignKey("evidence_items.id", ondelete="CASCADE"), nullable=False)
    investigation_id: Mapped[int] = mapped_column(ForeignKey("investigations.id", ondelete="CASCADE"), nullable=False)
    version_number: Mapped[int] = mapped_column(nullable=False)
    collector_name: Mapped[str] = mapped_column(String(120), nullable=False)
    source_type: Mapped[str] = mapped_column(String(80), nullable=False)
    evidence_type: Mapped[str] = mapped_column(String(120), nullable=False)
    source: Mapped[str] = mapped_column(String(120), nullable=False)
    detected: Mapped[bool] = mapped_column(nullable=False)
    support_direction: Mapped[str] = mapped_column(String(20), nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    collected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    data_quality_score: Mapped[float] = mapped_column(Float, nullable=False)
    checked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    changed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    change_reason: Mapped[str | None] = mapped_column(String(240))

    __table_args__ = (
        Index("idx_evidence_item_versions_evidence_version", "evidence_id", "version_number"),
        Index("idx_evidence_item_versions_investigation", "investigation_id"),
    )


class InvestigationEvent(Base):
    __tablename__ = "investigation_events"

    id: Mapped[int] = mapped_column(primary_key=True)
    investigation_id: Mapped[int] = mapped_column(ForeignKey("investigations.id", ondelete="CASCADE"), nullable=False)
    event_type: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    published_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    investigation: Mapped[Investigation] = relationship(back_populates="events")

    __table_args__ = (Index("idx_investigation_events_investigation_published", "investigation_id", "published_at"),)
