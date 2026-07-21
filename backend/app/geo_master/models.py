from datetime import datetime

from geoalchemy2 import Geometry
from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Index, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class City(TimestampMixin, Base):
    __tablename__ = "geo_cities"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(24), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    state: Mapped[str] = mapped_column(String(120), nullable=False)
    country: Mapped[str] = mapped_column(String(120), nullable=False, default="India")
    center_latitude: Mapped[float] = mapped_column(Float, nullable=False)
    center_longitude: Mapped[float] = mapped_column(Float, nullable=False)

    wards: Mapped[list["Ward"]] = relationship(back_populates="city")
    monitoring_stations: Mapped[list["MonitoringStation"]] = relationship(back_populates="city")
    road_segments: Mapped[list["RoadSegment"]] = relationship(back_populates="city")
    land_use_zones: Mapped[list["LandUseZone"]] = relationship(back_populates="city")


class Ward(TimestampMixin, Base):
    __tablename__ = "geo_wards"

    id: Mapped[int] = mapped_column(primary_key=True)
    city_id: Mapped[int] = mapped_column(ForeignKey("geo_cities.id", ondelete="CASCADE"), nullable=False, index=True)
    code: Mapped[str] = mapped_column(String(40), nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    population: Mapped[int | None] = mapped_column(Integer)
    boundary: Mapped[object] = mapped_column(Geometry("POLYGON", srid=4326, spatial_index=True), nullable=False)

    city: Mapped[City] = relationship(back_populates="wards")
    monitoring_stations: Mapped[list["MonitoringStation"]] = relationship(back_populates="ward")
    road_segments: Mapped[list["RoadSegment"]] = relationship(back_populates="ward")
    land_use_zones: Mapped[list["LandUseZone"]] = relationship(back_populates="ward")

    __table_args__ = (Index("uq_geo_wards_city_code", "city_id", "code", unique=True),)


class MonitoringStation(TimestampMixin, Base):
    __tablename__ = "geo_monitoring_stations"

    id: Mapped[int] = mapped_column(primary_key=True)
    city_id: Mapped[int] = mapped_column(ForeignKey("geo_cities.id", ondelete="CASCADE"), nullable=False, index=True)
    ward_id: Mapped[int | None] = mapped_column(ForeignKey("geo_wards.id", ondelete="SET NULL"), index=True)
    code: Mapped[str] = mapped_column(String(40), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)
    location: Mapped[object] = mapped_column(Geometry("POINT", srid=4326, spatial_index=True), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    city: Mapped[City] = relationship(back_populates="monitoring_stations")
    ward: Mapped[Ward | None] = relationship(back_populates="monitoring_stations")


class RoadSegment(TimestampMixin, Base):
    __tablename__ = "geo_road_segments"

    id: Mapped[int] = mapped_column(primary_key=True)
    city_id: Mapped[int] = mapped_column(ForeignKey("geo_cities.id", ondelete="CASCADE"), nullable=False, index=True)
    ward_id: Mapped[int | None] = mapped_column(ForeignKey("geo_wards.id", ondelete="SET NULL"), index=True)
    code: Mapped[str] = mapped_column(String(60), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    road_class: Mapped[str] = mapped_column(String(60), nullable=False)
    length_meters: Mapped[float | None] = mapped_column(Float)
    geometry: Mapped[object] = mapped_column(Geometry("LINESTRING", srid=4326, spatial_index=True), nullable=False)

    city: Mapped[City] = relationship(back_populates="road_segments")
    ward: Mapped[Ward | None] = relationship(back_populates="road_segments")

    __table_args__ = (Index("uq_geo_road_segments_city_code", "city_id", "code", unique=True),)


class LandUseZone(TimestampMixin, Base):
    __tablename__ = "geo_land_use_zones"

    id: Mapped[int] = mapped_column(primary_key=True)
    city_id: Mapped[int] = mapped_column(ForeignKey("geo_cities.id", ondelete="CASCADE"), nullable=False, index=True)
    ward_id: Mapped[int | None] = mapped_column(ForeignKey("geo_wards.id", ondelete="SET NULL"), index=True)
    code: Mapped[str] = mapped_column(String(60), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    category: Mapped[str] = mapped_column(String(80), nullable=False)
    boundary: Mapped[object] = mapped_column(Geometry("POLYGON", srid=4326, spatial_index=True), nullable=False)

    city: Mapped[City] = relationship(back_populates="land_use_zones")
    ward: Mapped[Ward | None] = relationship(back_populates="land_use_zones")

    __table_args__ = (Index("uq_geo_land_use_zones_city_code", "city_id", "code", unique=True),)
