from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator

from app.sensor_health.schemas import SensorHealthStatus


class BoundingBox(BaseModel):
    min_latitude: float = Field(ge=-90, le=90)
    min_longitude: float = Field(ge=-180, le=180)
    max_latitude: float = Field(ge=-90, le=90)
    max_longitude: float = Field(ge=-180, le=180)

    @model_validator(mode="after")
    def validate_bounds(self) -> "BoundingBox":
        if self.max_latitude < self.min_latitude:
            raise ValueError("max_latitude must be greater than or equal to min_latitude")
        if self.max_longitude < self.min_longitude:
            raise ValueError("max_longitude must be greater than or equal to min_longitude")
        return self


class HeatmapRequest(BaseModel):
    bbox: BoundingBox
    grid_resolution: float = Field(default=0.01, gt=0, le=1)
    include_unreliable_sensors: bool = True
    unhealthy_sensor_weight: float = Field(default=0.25, ge=0, le=1)
    output_format: Literal["geojson"] = "geojson"


class StationAQISample(BaseModel):
    station_code: str
    station_name: str
    ward_code: str | None = None
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    aqi: float = Field(ge=0)
    data_quality_score: float = Field(ge=0, le=1)
    sensor_status: SensorHealthStatus
    is_reliable: bool


class WardAQISummary(BaseModel):
    ward_code: str
    average_aqi: float
    station_count: int
    band: str
    severity_rank: int
    display_label: str
    health_severity_category: str


GeoJSONFeatureCollection = dict[str, Any]
