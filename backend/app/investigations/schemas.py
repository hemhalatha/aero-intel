from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class InvestigationStatus(StrEnum):
    WAITING_FOR_EVIDENCE = "WAITING_FOR_EVIDENCE"
    PARTIALLY_COMPLETE = "PARTIALLY_COMPLETE"
    COMPLETE = "COMPLETE"


class CollectionStatus(StrEnum):
    RUNNING = "RUNNING"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"


class InvestigationRecord(BaseModel):
    id: int | None = None
    investigation_uid: str
    hotspot_id: int
    hotspot_uid: str | None = None
    ward_code: str | None = None
    station_code: str | None = None
    status: InvestigationStatus
    environmental_context: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime | None = None
    updated_at: datetime | None = None
    last_collection_started_at: datetime | None = None
    last_collection_completed_at: datetime | None = None


class EvidenceCollectionRunRecord(BaseModel):
    id: int | None = None
    investigation_id: int
    collector_name: str
    status: CollectionStatus
    started_at: datetime
    completed_at: datetime | None = None
    error_message: str | None = None
    evidence_count: int = 0
    request_reason: str | None = None


class EvidenceItemRecord(BaseModel):
    id: int | None = None
    investigation_id: int
    collector_name: str
    evidence_type: str
    source: str
    payload: dict[str, Any]
    observed_at: datetime
    collected_at: datetime
    confidence: float = Field(ge=0, le=1)


class InvestigationEventRecord(BaseModel):
    id: int | None = None
    investigation_id: int
    event_type: str
    payload: dict[str, Any]
    published_at: datetime


class AdditionalEvidenceRequest(BaseModel):
    requested_collectors: list[str] | None = None
    reason: str | None = Field(default=None, max_length=240)


class HotspotCreatedEventIn(BaseModel):
    hotspot_id: int
    event_type: str = "hotspot.created"
    payload: dict[str, Any] = Field(default_factory=dict)
    published_at: datetime


class InvestigationDetail(BaseModel):
    investigation: InvestigationRecord
    collector_runs: list[EvidenceCollectionRunRecord]
    evidence_items: list[EvidenceItemRecord]
    events: list[InvestigationEventRecord]
