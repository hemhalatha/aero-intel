from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, Float, ForeignKey, Index, JSON, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Hotspot(Base):
    __tablename__ = "hotspots"

    id: Mapped[int] = mapped_column(primary_key=True)
    hotspot_uid: Mapped[str] = mapped_column(String(80), unique=True, nullable=False, index=True)
    ward_code: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    station_code: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    station_name: Mapped[str] = mapped_column(String(180), nullable=False)
    status: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    severity: Mapped[str] = mapped_column(String(20), nullable=False)
    alert_level: Mapped[str] = mapped_column(String(20), nullable=False)
    current_aqi: Mapped[float] = mapped_column(Float, nullable=False)
    anomaly_score: Mapped[float] = mapped_column(Float, nullable=False)
    data_quality_confidence: Mapped[float] = mapped_column(Float, nullable=False)
    trigger_reasons: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    detection_context: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    first_detected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    last_detected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    observations: Mapped[list["HotspotObservation"]] = relationship(back_populates="hotspot")
    status_history: Mapped[list["HotspotStatusHistory"]] = relationship(back_populates="hotspot")
    events: Mapped[list["HotspotEvent"]] = relationship(back_populates="hotspot")

    __table_args__ = (
        Index("idx_hotspots_status_ward", "status", "ward_code"),
        Index("idx_hotspots_last_detected", "last_detected_at"),
    )


class HotspotObservation(Base):
    __tablename__ = "hotspot_observations"

    id: Mapped[int] = mapped_column(primary_key=True)
    hotspot_id: Mapped[int] = mapped_column(ForeignKey("hotspots.id", ondelete="CASCADE"), nullable=False, index=True)
    station_code: Mapped[str] = mapped_column(String(80), nullable=False)
    station_name: Mapped[str] = mapped_column(String(180), nullable=False)
    ward_code: Mapped[str] = mapped_column(String(40), nullable=False)
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    aqi: Mapped[float] = mapped_column(Float, nullable=False)
    pollutant_snapshot: Mapped[dict[str, float]] = mapped_column(JSON, nullable=False)
    severity: Mapped[str] = mapped_column(String(20), nullable=False)
    alert_level: Mapped[str] = mapped_column(String(20), nullable=False)
    trigger_reasons: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    anomaly_score: Mapped[float] = mapped_column(Float, nullable=False)
    data_quality_confidence: Mapped[float] = mapped_column(Float, nullable=False)
    detection_context: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    hotspot: Mapped[Hotspot] = relationship(back_populates="observations")

    __table_args__ = (
        Index("idx_hotspot_observations_hotspot_observed", "hotspot_id", "observed_at"),
        Index("idx_hotspot_observations_ward_observed", "ward_code", "observed_at"),
    )


class HotspotStatusHistory(Base):
    __tablename__ = "hotspot_status_history"

    id: Mapped[int] = mapped_column(primary_key=True)
    hotspot_id: Mapped[int] = mapped_column(ForeignKey("hotspots.id", ondelete="CASCADE"), nullable=False, index=True)
    from_status: Mapped[str | None] = mapped_column(String(40))
    to_status: Mapped[str] = mapped_column(String(40), nullable=False)
    reason: Mapped[str | None] = mapped_column(Text)
    changed_by: Mapped[str | None] = mapped_column(String(120))
    changed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    hotspot: Mapped[Hotspot] = relationship(back_populates="status_history")

    __table_args__ = (Index("idx_hotspot_status_history_hotspot_changed", "hotspot_id", "changed_at"),)


class HotspotEvent(Base):
    __tablename__ = "hotspot_events"

    id: Mapped[int] = mapped_column(primary_key=True)
    hotspot_id: Mapped[int] = mapped_column(ForeignKey("hotspots.id", ondelete="CASCADE"), nullable=False, index=True)
    event_type: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    published_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    hotspot: Mapped[Hotspot] = relationship(back_populates="events")

    __table_args__ = (Index("idx_hotspot_events_hotspot_published", "hotspot_id", "published_at"),)
