from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, Float, ForeignKey, Index, JSON, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class EnvironmentalDataSource(Base):
    __tablename__ = "env_data_sources"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(80), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(180), nullable=False)
    source_type: Mapped[str] = mapped_column(String(80), nullable=False)
    provenance: Mapped[str] = mapped_column(String(40), nullable=False)
    license: Mapped[str] = mapped_column(String(120), nullable=False)
    url: Mapped[str] = mapped_column(Text, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    air_quality_readings: Mapped[list["AirQualityReading"]] = relationship(back_populates="source")
    weather_observations: Mapped[list["WeatherObservation"]] = relationship(back_populates="source")
    controlled_scenarios: Mapped[list["ControlledScenario"]] = relationship(back_populates="source")


class AirQualityReading(Base):
    __tablename__ = "env_air_quality_readings"

    id: Mapped[int] = mapped_column(primary_key=True)
    source_id: Mapped[int] = mapped_column(ForeignKey("env_data_sources.id", ondelete="RESTRICT"), nullable=False)
    station_code: Mapped[str] = mapped_column(String(80), nullable=False)
    station_name: Mapped[str] = mapped_column(String(180), nullable=False)
    city: Mapped[str] = mapped_column(String(120), nullable=False)
    state: Mapped[str] = mapped_column(String(120), nullable=False)
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    pollutant: Mapped[str] = mapped_column(String(40), nullable=False)
    value: Mapped[float] = mapped_column(Float, nullable=False)
    unit: Mapped[str] = mapped_column(String(40), nullable=False)
    averaging_period: Mapped[str] = mapped_column(String(40), nullable=False)
    raw_payload: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    source: Mapped[EnvironmentalDataSource] = relationship(back_populates="air_quality_readings")

    __table_args__ = (
        UniqueConstraint("station_code", "observed_at", "pollutant", "source_id", name="uq_env_aq_station_time_pollutant_source"),
        Index("idx_env_aq_station_observed", "station_code", "observed_at"),
        Index("idx_env_aq_pollutant_observed", "pollutant", "observed_at"),
    )


class WeatherObservation(Base):
    __tablename__ = "env_weather_observations"

    id: Mapped[int] = mapped_column(primary_key=True)
    source_id: Mapped[int] = mapped_column(ForeignKey("env_data_sources.id", ondelete="RESTRICT"), nullable=False)
    location_code: Mapped[str] = mapped_column(String(80), nullable=False)
    city: Mapped[str] = mapped_column(String(120), nullable=False)
    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    temperature_c: Mapped[float | None] = mapped_column(Float)
    relative_humidity_pct: Mapped[float | None] = mapped_column(Float)
    wind_speed_kmh: Mapped[float | None] = mapped_column(Float)
    wind_direction_degrees: Mapped[float | None] = mapped_column(Float)
    raw_payload: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    source: Mapped[EnvironmentalDataSource] = relationship(back_populates="weather_observations")

    __table_args__ = (
        UniqueConstraint("location_code", "observed_at", "source_id", name="uq_env_weather_location_time_source"),
        Index("idx_env_weather_location_observed", "location_code", "observed_at"),
    )


class ControlledScenario(Base):
    __tablename__ = "env_controlled_scenarios"

    id: Mapped[int] = mapped_column(primary_key=True)
    source_id: Mapped[int] = mapped_column(ForeignKey("env_data_sources.id", ondelete="RESTRICT"), nullable=False)
    scenario_key: Mapped[str] = mapped_column(String(80), unique=True, nullable=False)
    title: Mapped[str] = mapped_column(String(180), nullable=False)
    category: Mapped[str] = mapped_column(String(80), nullable=False)
    city: Mapped[str] = mapped_column(String(120), nullable=False)
    ward_code: Mapped[str | None] = mapped_column(String(40))
    station_code: Mapped[str | None] = mapped_column(String(80))
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    ends_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    severity: Mapped[float] = mapped_column(Float, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    evidence: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    provenance: Mapped[str] = mapped_column(String(40), nullable=False, default="controlled_demo")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    source: Mapped[EnvironmentalDataSource] = relationship(back_populates="controlled_scenarios")

    __table_args__ = (
        Index("idx_env_controlled_scenarios_window", "starts_at", "ends_at"),
        Index("idx_env_controlled_scenarios_category", "category"),
    )
