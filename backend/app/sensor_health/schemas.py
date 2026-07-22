from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field



class SensorHealthStatus(str, Enum):
    ONLINE = "ONLINE"
    DELAYED = "DELAYED"
    DEGRADED = "DEGRADED"
    OFFLINE = "OFFLINE"



class SensorHealthSnapshot(BaseModel):
    station_code: str
    station_name: str
    ward_code: str | None = None
    status: SensorHealthStatus
    data_quality_score: float = Field(ge=0, le=1)
    last_reading_at: datetime | None = None
    evaluated_at: datetime
    missing_pollutants: list[str] = Field(default_factory=list)
    invalid_pollutants: list[str] = Field(default_factory=list)
    repeated_pollutants: list[str] = Field(default_factory=list)
    abnormal_signals: list[str] = Field(default_factory=list)
    reasons: list[str] = Field(default_factory=list)
    is_reliable: bool


class SensorHealthHistoryEntry(BaseModel):
    station_code: str
    status: SensorHealthStatus
    data_quality_score: float = Field(ge=0, le=1)
    changed_at: datetime
    reasons: list[str] = Field(default_factory=list)


class SensorReadingReliability(BaseModel):
    station_code: str
    reliable: bool
    status: SensorHealthStatus
    data_quality_score: float
    reasons: list[str] = Field(default_factory=list)
