from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


GeoEntityType = Literal["wards", "monitoring_stations", "road_segments", "land_use_zones"]


class GeoPoint(BaseModel):
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)


class CityBase(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    state: str = Field(min_length=1, max_length=120)
    country: str = Field(default="India", min_length=1, max_length=120)
    center_latitude: float = Field(ge=-90, le=90)
    center_longitude: float = Field(ge=-180, le=180)


class CityCreate(CityBase):
    code: str = Field(min_length=2, max_length=24)


class CityRead(CityBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    code: str
    created_at: datetime | None = None
    updated_at: datetime | None = None


class WardBase(BaseModel):
    city_id: int = Field(gt=0)
    code: str = Field(min_length=1, max_length=40)
    name: str = Field(min_length=1, max_length=120)
    population: int | None = Field(default=None, ge=0)


class WardCreate(WardBase):
    boundary_geojson: dict[str, Any]


class WardRead(WardBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    boundary_geojson: dict[str, Any] | None = None


class MonitoringStationBase(BaseModel):
    city_id: int = Field(gt=0)
    ward_id: int | None = Field(default=None, gt=0)
    code: str = Field(min_length=1, max_length=40)
    name: str = Field(min_length=1, max_length=160)
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    is_active: bool = True


class MonitoringStationCreate(MonitoringStationBase):
    pass


class MonitoringStationRead(MonitoringStationBase):
    model_config = ConfigDict(from_attributes=True)

    id: int


class RoadSegmentBase(BaseModel):
    city_id: int = Field(gt=0)
    ward_id: int | None = Field(default=None, gt=0)
    code: str = Field(min_length=1, max_length=60)
    name: str = Field(min_length=1, max_length=160)
    road_class: str = Field(min_length=1, max_length=60)
    length_meters: float | None = Field(default=None, ge=0)


class RoadSegmentCreate(RoadSegmentBase):
    geometry_geojson: dict[str, Any]


class RoadSegmentRead(RoadSegmentBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    geometry_geojson: dict[str, Any] | None = None


class LandUseZoneBase(BaseModel):
    city_id: int = Field(gt=0)
    ward_id: int | None = Field(default=None, gt=0)
    code: str = Field(min_length=1, max_length=60)
    name: str = Field(min_length=1, max_length=160)
    category: str = Field(min_length=1, max_length=80)


class LandUseZoneCreate(LandUseZoneBase):
    boundary_geojson: dict[str, Any]


class LandUseZoneRead(LandUseZoneBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    boundary_geojson: dict[str, Any] | None = None


class DistanceResponse(BaseModel):
    origin: GeoPoint
    destination: GeoPoint
    distance_meters: float


class RadiusSearchRequest(BaseModel):
    point: GeoPoint
    radius_meters: float = Field(gt=0, le=50_000)
    entity_type: GeoEntityType


class WardLookupRequest(BaseModel):
    point: GeoPoint
