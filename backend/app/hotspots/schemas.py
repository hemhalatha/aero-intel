from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class HotspotTrigger(StrEnum):
    AQI_THRESHOLD = "aqi_threshold"
    BASELINE_DEVIATION = "baseline_deviation"
    POLLUTANT_SPIKE = "pollutant_spike"


class HotspotSeverity(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AlertLevel(StrEnum):
    WATCH = "watch"
    WARNING = "warning"
    EMERGENCY = "emergency"


class HotspotCandidate(BaseModel):
    ward_code: str
    station_code: str
    station_name: str
    aqi: float
    pollutant_snapshot: dict[str, float]
    severity: HotspotSeverity
    alert_level: AlertLevel
    trigger_reasons: list[HotspotTrigger]
    anomaly_score: float = Field(ge=0)
    observed_at: datetime
    data_quality_confidence: float = Field(ge=0, le=1)
