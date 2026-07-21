from datetime import datetime

from sqlalchemy import DateTime, Float, Index, JSON, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class SensorHealthCurrent(Base):
    __tablename__ = "sensor_health_current"

    station_code: Mapped[str] = mapped_column(String(80), primary_key=True)
    station_name: Mapped[str] = mapped_column(String(180), nullable=False)
    ward_code: Mapped[str | None] = mapped_column(String(40))
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    data_quality_score: Mapped[float] = mapped_column(Float, nullable=False)
    last_reading_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    evaluated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    missing_pollutants: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    invalid_pollutants: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    repeated_pollutants: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    abnormal_signals: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    reasons: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    is_reliable: Mapped[bool] = mapped_column(nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    __table_args__ = (
        Index("idx_sensor_health_current_status", "status"),
        Index("idx_sensor_health_current_ward", "ward_code"),
    )


class SensorHealthHistory(Base):
    __tablename__ = "sensor_health_history"

    id: Mapped[int] = mapped_column(primary_key=True)
    station_code: Mapped[str] = mapped_column(String(80), nullable=False)
    station_name: Mapped[str] = mapped_column(String(180), nullable=False)
    ward_code: Mapped[str | None] = mapped_column(String(40))
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    data_quality_score: Mapped[float] = mapped_column(Float, nullable=False)
    last_reading_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    evaluated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    missing_pollutants: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    invalid_pollutants: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    repeated_pollutants: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    abnormal_signals: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    reasons: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    is_reliable: Mapped[bool] = mapped_column(nullable=False)
    changed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    __table_args__ = (
        Index("idx_sensor_health_history_station_changed", "station_code", "changed_at"),
        Index("idx_sensor_health_history_status", "status"),
    )
