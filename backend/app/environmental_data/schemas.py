from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


DataProvenance = Literal["real_public", "controlled_demo"]


class EnvironmentalDataSourceSeed(BaseModel):
    code: str = Field(min_length=1, max_length=80)
    name: str = Field(min_length=1, max_length=180)
    source_type: str = Field(min_length=1, max_length=80)
    provenance: DataProvenance
    license: str = Field(min_length=1, max_length=120)
    url: str = Field(min_length=1)
    notes: str | None = None


class AirQualityReadingSeed(BaseModel):
    source_code: str
    station_code: str
    station_name: str
    city: str
    state: str
    observed_at: datetime
    pollutant: str
    value: float = Field(ge=0)
    unit: str
    averaging_period: str = "15min"
    raw_payload: dict[str, Any] = Field(default_factory=dict)


class WeatherObservationSeed(BaseModel):
    source_code: str
    location_code: str
    city: str
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    observed_at: datetime
    temperature_c: float | None = None
    relative_humidity_pct: float | None = Field(default=None, ge=0, le=100)
    wind_speed_kmh: float | None = Field(default=None, ge=0)
    wind_direction_degrees: float | None = Field(default=None, ge=0, le=360)
    raw_payload: dict[str, Any] = Field(default_factory=dict)


class ControlledScenarioSeed(BaseModel):
    source_code: str
    scenario_key: str = Field(min_length=1, max_length=80)
    title: str = Field(min_length=1, max_length=180)
    category: Literal["traffic_anomaly", "construction_permit", "industrial_activity"]
    city: str
    ward_code: str | None = None
    station_code: str | None = None
    starts_at: datetime
    ends_at: datetime
    severity: float = Field(ge=0, le=1)
    description: str
    evidence: dict[str, Any]
    provenance: Literal["controlled_demo"] = "controlled_demo"


class PreparedEnvironmentalSeed(BaseModel):
    sources: list[EnvironmentalDataSourceSeed]
    air_quality_readings: list[AirQualityReadingSeed]
    weather_observations: list[WeatherObservationSeed]
    controlled_scenarios: list[ControlledScenarioSeed]
