from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field

from app.hotspots.schemas import AlertLevel, HotspotCandidate, HotspotSeverity, HotspotTrigger


class HotspotStatus(StrEnum):
    ACTIVE = "ACTIVE"
    INVESTIGATING = "INVESTIGATING"
    WAITING_FOR_EVIDENCE = "WAITING_FOR_EVIDENCE"
    ACTION_ASSIGNED = "ACTION_ASSIGNED"
    UNDER_VERIFICATION = "UNDER_VERIFICATION"
    RESOLVED = "RESOLVED"


class HotspotRecord(BaseModel):
    id: int | None = None
    hotspot_uid: str
    ward_code: str
    station_code: str
    station_name: str
    status: HotspotStatus
    severity: HotspotSeverity
    alert_level: AlertLevel
    current_aqi: float
    anomaly_score: float
    data_quality_confidence: float = Field(ge=0, le=1)
    trigger_reasons: list[HotspotTrigger]
    detection_context: dict[str, Any] = Field(default_factory=dict)
    first_detected_at: datetime
    last_detected_at: datetime
    resolved_at: datetime | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class HotspotObservationRecord(BaseModel):
    id: int | None = None
    hotspot_id: int
    station_code: str
    station_name: str
    ward_code: str
    observed_at: datetime
    aqi: float
    pollutant_snapshot: dict[str, float]
    severity: HotspotSeverity
    alert_level: AlertLevel
    trigger_reasons: list[HotspotTrigger]
    anomaly_score: float
    data_quality_confidence: float = Field(ge=0, le=1)
    detection_context: dict[str, Any] = Field(default_factory=dict)


class HotspotStatusHistoryRecord(BaseModel):
    id: int | None = None
    hotspot_id: int
    from_status: HotspotStatus | None = None
    to_status: HotspotStatus
    reason: str | None = None
    changed_by: str | None = None
    changed_at: datetime


class HotspotEventRecord(BaseModel):
    id: int | None = None
    hotspot_id: int
    event_type: str
    payload: dict[str, Any]
    published_at: datetime


class HotspotStateUpdate(BaseModel):
    status: HotspotStatus
    reason: str | None = Field(default=None, max_length=500)
    changed_by: str | None = Field(default=None, max_length=120)


class HotspotCandidateIngestionRequest(BaseModel):
    candidate: HotspotCandidate
    detection_context: dict[str, Any] = Field(default_factory=dict)


class HotspotDetail(BaseModel):
    hotspot: HotspotRecord
    observations: list[HotspotObservationRecord]
    status_history: list[HotspotStatusHistoryRecord]
    events: list[HotspotEventRecord]
