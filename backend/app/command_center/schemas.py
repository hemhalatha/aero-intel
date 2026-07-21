from datetime import datetime
from typing import Literal

from pydantic import BaseModel

from app.environmental_data.time_series_schemas import StationLatestState, WeatherReading, WindReading
from app.heatmap.schemas import WardAQISummary


class HotspotSummary(BaseModel):
    hotspot_id: str
    ward_code: str | None = None
    severity: Literal["low", "medium", "high", "critical"]
    aqi: float
    detected_at: datetime
    summary: str


class CityPollutionTrendPoint(BaseModel):
    observed_at: datetime
    average_aqi: float


class CommandCenterDashboard(BaseModel):
    generated_at: datetime
    city_average_aqi: float | None
    worst_affected_ward: WardAQISummary | None
    active_hotspot_count: int
    offline_or_degraded_station_count: int
    latest_reliable_station_readings: list[StationLatestState]
    weather_summary: WeatherReading | None
    wind_information: WindReading | None
    current_hotspot_summaries: list[HotspotSummary]
    city_pollution_trend: list[CityPollutionTrendPoint]
