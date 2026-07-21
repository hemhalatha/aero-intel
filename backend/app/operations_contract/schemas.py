from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.aqi.schemas import AQIClassification
from app.environmental_data.time_series_schemas import (
    PollutantReading,
    TimeWindow,
    WeatherForecastReading,
    WeatherReading,
    WindReading,
)
from app.geo_master.schemas import WardRead
from app.hotspot_lifecycle.schemas import HotspotStatus
from app.hotspots.schemas import AlertLevel, HotspotSeverity
from app.sensor_health.schemas import SensorHealthSnapshot


class OperationsConsumer(StrEnum):
    OPERATIONS = "operations"
    CITIZEN_ADVISORY = "citizen_advisory"
    INTERVENTION_VERIFICATION = "intervention_verification"


class InterventionWindowType(StrEnum):
    PRE_INTERVENTION_BASELINE = "pre_intervention_baseline"
    PREDICTED_EVALUATION_WINDOW = "predicted_evaluation_window"
    ACTUAL_POST_INTERVENTION = "actual_post_intervention"


class DataQualityRollup(BaseModel):
    reading_count: int = Field(ge=0)
    valid_count: int = Field(ge=0)
    suspect_count: int = Field(ge=0)
    incomplete_count: int = Field(ge=0)
    reliable_sensor_count: int = Field(ge=0)
    unreliable_sensor_count: int = Field(ge=0)
    average_sensor_quality_score: float | None = Field(default=None, ge=0, le=1)
    notes: list[str] = Field(default_factory=list)


class HotspotStatusContract(BaseModel):
    hotspot_id: int
    hotspot_uid: str
    status: HotspotStatus
    severity: HotspotSeverity
    alert_level: AlertLevel
    current_aqi: float
    first_detected_at: datetime
    last_detected_at: datetime
    recurrence_count: int = Field(ge=0)
    data_quality_confidence: float = Field(ge=0, le=1)


class HotspotRecurrenceRecord(BaseModel):
    hotspot_id: int
    observed_at: datetime
    aqi: float
    severity: HotspotSeverity
    alert_level: AlertLevel
    pollutant_snapshot: dict[str, float] = Field(default_factory=dict)
    data_quality_confidence: float = Field(ge=0, le=1)


class WardOperationsState(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "contract_version": "v1",
                "generated_at": "2025-01-15T12:00:00Z",
                "supported_consumers": ["operations", "citizen_advisory", "intervention_verification"],
                "ward": {"id": 14, "city_id": 1, "code": "BLR-W-014", "name": "Silk Board", "population": 78000},
                "current_ward_aqi": 238,
                "aqi_band": {
                    "aqi": 238,
                    "band": "Poor",
                    "severity_rank": 4,
                    "display_label": "Poor",
                    "health_severity_category": "Unhealthy",
                },
                "pollutant_readings": [],
                "hotspot_statuses": [],
                "hotspot_recurrence_history": [],
                "sensor_quality": [],
                "data_quality": {"reading_count": 0, "valid_count": 0, "suspect_count": 0, "incomplete_count": 0},
            }
        }
    )

    contract_version: str = "v1"
    generated_at: datetime
    supported_consumers: list[OperationsConsumer]
    ward: WardRead | None
    ward_code: str
    current_ward_aqi: float | None = None
    aqi_band: AQIClassification | None = None
    pollutant_readings: list[PollutantReading] = Field(default_factory=list)
    hotspot_statuses: list[HotspotStatusContract] = Field(default_factory=list)
    hotspot_recurrence_history: list[HotspotRecurrenceRecord] = Field(default_factory=list)
    sensor_quality: list[SensorHealthSnapshot] = Field(default_factory=list)
    data_quality: DataQualityRollup


class OperationsTimeWindowQuery(BaseModel):
    ward_code: str
    start_at: datetime
    end_at: datetime
    pollutant: str | None = None
    station_code: str | None = None
    selected_at: datetime | None = None

    @model_validator(mode="after")
    def validate_window(self) -> "OperationsTimeWindowQuery":
        if self.end_at <= self.start_at:
            raise ValueError("end_at must be after start_at")
        return self


class OperationsTimeWindowReadings(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "contract_version": "v1",
                "ward_code": "BLR-W-014",
                "window": {"start_at": "2025-01-15T10:00:00Z", "end_at": "2025-01-15T12:00:00Z"},
                "selected_at": "2025-01-15T11:00:00Z",
                "pollutant": "PM2.5",
                "readings": [],
                "data_quality": {"reading_count": 0, "valid_count": 0, "suspect_count": 0, "incomplete_count": 0},
            }
        }
    )

    contract_version: str = "v1"
    generated_at: datetime
    ward_code: str
    window: TimeWindow
    selected_at: datetime | None = None
    pollutant: str | None = None
    station_code: str | None = None
    readings: list[PollutantReading]
    data_quality: DataQualityRollup


class InterventionWindowSegment(BaseModel):
    window_type: InterventionWindowType
    window: TimeWindow
    readings: list[PollutantReading] = Field(default_factory=list)
    weather_forecast: list[WeatherForecastReading] = Field(default_factory=list)
    data_quality: DataQualityRollup
    notes: list[str] = Field(default_factory=list)


class InterventionVerificationWindow(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "contract_version": "v1",
                "ward_code": "BLR-W-014",
                "intervention_id": "road-dust-control-42",
                "intervention_at": "2025-01-15T12:00:00Z",
                "pre_intervention_baseline": {"window_type": "pre_intervention_baseline", "readings": []},
                "predicted_evaluation_window": {"window_type": "predicted_evaluation_window", "weather_forecast": []},
                "actual_post_intervention": {"window_type": "actual_post_intervention", "readings": []},
            }
        }
    )

    contract_version: str = "v1"
    generated_at: datetime
    ward_code: str
    intervention_id: str | None = None
    intervention_at: datetime
    pollutant: str | None = None
    station_code: str | None = None
    pre_intervention_baseline: InterventionWindowSegment
    predicted_evaluation_window: InterventionWindowSegment
    actual_post_intervention: InterventionWindowSegment
    current_weather: WeatherReading | None = None
    current_wind: WindReading | None = None


class OperationsContractExamplePayload(BaseModel):
    name: str
    description: str
    payload: dict[str, Any]
