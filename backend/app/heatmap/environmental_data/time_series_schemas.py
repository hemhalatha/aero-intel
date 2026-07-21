from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, model_validator

DataQualityStatus = Literal["valid", "suspect", "incomplete"]


class TimeWindow(BaseModel):
    start_at: datetime
    end_at: datetime

    @model_validator(mode="after")
    def validate_window(self) -> "TimeWindow":
        if self.end_at <= self.start_at:
            raise ValueError("end_at must be after start_at")
        return self


class PollutantReading(BaseModel):
    station_code: str
    station_name: str
    ward_code: str | None = None
    observed_at: datetime
    pollutant: str
    value: float = Field(ge=0)
    unit: str
    data_quality_status: DataQualityStatus


class StationLatestState(BaseModel):
    station_code: str
    station_name: str
    ward_code: str | None = None
    observed_at: datetime
    readings: list[PollutantReading]
    data_quality_status: DataQualityStatus


class WeatherReading(BaseModel):
    location_code: str
    city: str
    observed_at: datetime
    temperature_c: float | None = None
    relative_humidity_pct: float | None = Field(default=None, ge=0, le=100)
    data_quality_status: DataQualityStatus = "valid"


class WindReading(BaseModel):
    location_code: str
    city: str
    observed_at: datetime
    wind_speed_kmh: float | None = Field(default=None, ge=0)
    wind_direction_degrees: float | None = Field(default=None, ge=0, le=360)
    data_quality_status: DataQualityStatus = "valid"


class WeatherForecastReading(BaseModel):
    location_code: str
    forecast_for: datetime
    generated_at: datetime
    temperature_c: float | None = None
    relative_humidity_pct: float | None = Field(default=None, ge=0, le=100)
    wind_speed_kmh: float | None = Field(default=None, ge=0)
    wind_direction_degrees: float | None = Field(default=None, ge=0, le=360)
    provider: str
    data_quality_status: DataQualityStatus = "valid"


class HistoricalBaseline(BaseModel):
    ward_code: str
    pollutant: str
    comparison_days: int
    readings: list[PollutantReading]
    average_value: float | None
