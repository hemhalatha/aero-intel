from datetime import UTC, datetime
from enum import StrEnum
from typing import Any, Protocol

from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .models import EvidenceItem, EvidenceItemVersion


class EvidenceSupportDirection(StrEnum):
    SUPPORTS = "SUPPORTS"
    CONTRADICTS = "CONTRADICTS"
    NEUTRAL = "NEUTRAL"


class EvidenceCreate(BaseModel):
    investigation_id: int
    source_type: str = Field(min_length=1, max_length=80)
    evidence_type: str = Field(min_length=1, max_length=120)
    detected: bool
    confidence: float = Field(ge=0, le=1)
    support_direction: EvidenceSupportDirection
    raw_details: dict[str, Any] = Field(default_factory=dict)
    data_quality_score: float = Field(ge=0, le=1)
    collector_name: str = Field(min_length=1, max_length=120)
    checked_at: datetime
    source: str | None = Field(default=None, max_length=120)


class EvidenceUpdate(BaseModel):
    source_type: str | None = Field(default=None, min_length=1, max_length=80)
    evidence_type: str | None = Field(default=None, min_length=1, max_length=120)
    detected: bool | None = None
    confidence: float | None = Field(default=None, ge=0, le=1)
    support_direction: EvidenceSupportDirection | None = None
    raw_details: dict[str, Any] | None = None
    data_quality_score: float | None = Field(default=None, ge=0, le=1)
    collector_name: str | None = Field(default=None, min_length=1, max_length=120)
    checked_at: datetime | None = None
    source: str | None = Field(default=None, max_length=120)


class EvidenceRecord(BaseModel):
    evidence_id: int
    investigation_id: int
    source_type: str
    evidence_type: str
    detected: bool
    confidence: float = Field(ge=0, le=1)
    support_direction: EvidenceSupportDirection
    raw_details: dict[str, Any]
    data_quality_score: float = Field(ge=0, le=1)
    collector_name: str
    checked_at: datetime
    source: str
    collected_at: datetime


class EvidenceVersionRecord(EvidenceRecord):
    version_id: int
    version_number: int
    changed_at: datetime
    change_reason: str | None = None


class EvidenceRepositoryProtocol(Protocol):
    def list_for_investigation(
        self,
        investigation_id: int,
        source_type: str | None = None,
        evidence_type: str | None = None,
        support_direction: EvidenceSupportDirection | None = None,
    ) -> list[EvidenceRecord]:
        ...

    def add(self, evidence: EvidenceCreate) -> EvidenceRecord:
        ...

    def update(self, evidence_id: int, update: EvidenceUpdate, reason: str | None = None) -> EvidenceRecord:
        ...

    def list_versions(self, evidence_id: int) -> list[EvidenceVersionRecord]:
        ...

    def commit(self) -> None:
        ...


class EvidenceRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_for_investigation(
        self,
        investigation_id: int,
        source_type: str | None = None,
        evidence_type: str | None = None,
        support_direction: EvidenceSupportDirection | None = None,
    ) -> list[EvidenceRecord]:
        statement = select(EvidenceItem).where(EvidenceItem.investigation_id == investigation_id)
        if source_type is not None:
            statement = statement.where(EvidenceItem.source_type == source_type)
        if evidence_type is not None:
            statement = statement.where(EvidenceItem.evidence_type == evidence_type)
        if support_direction is not None:
            statement = statement.where(EvidenceItem.support_direction == support_direction.value)
        statement = statement.order_by(EvidenceItem.checked_at, EvidenceItem.id)
        return [self._record(row) for row in self.db.scalars(statement)]

    def add(self, evidence: EvidenceCreate) -> EvidenceRecord:
        checked_at = self._utc(evidence.checked_at)
        row = EvidenceItem(
            investigation_id=evidence.investigation_id,
            collector_name=evidence.collector_name,
            source_type=evidence.source_type,
            evidence_type=evidence.evidence_type,
            source=evidence.source or evidence.collector_name,
            detected=evidence.detected,
            support_direction=evidence.support_direction.value,
            payload=evidence.raw_details,
            observed_at=checked_at,
            collected_at=datetime.now(UTC),
            confidence=evidence.confidence,
            data_quality_score=evidence.data_quality_score,
            checked_at=checked_at,
        )
        self.db.add(row)
        self.db.flush()
        return self._record(row)

    def update(self, evidence_id: int, update: EvidenceUpdate, reason: str | None = None) -> EvidenceRecord:
        row = self.db.get(EvidenceItem, evidence_id)
        if row is None:
            raise ValueError("Evidence item not found.")
        self._save_version(row, reason)
        changes = update.model_dump(exclude_unset=True, exclude_none=True)
        field_map = {"raw_details": "payload"}
        for key, value in changes.items():
            column = field_map.get(key, key)
            if key == "support_direction" and value is not None:
                value = value.value
            if key == "checked_at" and value is not None:
                value = self._utc(value)
            setattr(row, column, value)
        self.db.flush()
        return self._record(row)

    def list_versions(self, evidence_id: int) -> list[EvidenceVersionRecord]:
        statement = (
            select(EvidenceItemVersion)
            .where(EvidenceItemVersion.evidence_id == evidence_id)
            .order_by(EvidenceItemVersion.version_number)
        )
        return [self._version_record(row) for row in self.db.scalars(statement)]

    def commit(self) -> None:
        self.db.commit()

    def _save_version(self, row: EvidenceItem, reason: str | None) -> None:
        latest = self.db.scalar(
            select(func.max(EvidenceItemVersion.version_number)).where(EvidenceItemVersion.evidence_id == row.id)
        )
        version = EvidenceItemVersion(
            evidence_id=row.id,
            investigation_id=row.investigation_id,
            version_number=(latest or 0) + 1,
            collector_name=row.collector_name,
            source_type=row.source_type,
            evidence_type=row.evidence_type,
            source=row.source,
            detected=row.detected,
            support_direction=row.support_direction,
            payload=row.payload,
            observed_at=row.observed_at,
            collected_at=row.collected_at,
            confidence=row.confidence,
            data_quality_score=row.data_quality_score,
            checked_at=row.checked_at,
            change_reason=reason,
        )
        self.db.add(version)

    @staticmethod
    def _record(row: EvidenceItem) -> EvidenceRecord:
        return EvidenceRecord(
            evidence_id=row.id,
            investigation_id=row.investigation_id,
            source_type=row.source_type,
            evidence_type=row.evidence_type,
            detected=row.detected,
            confidence=row.confidence,
            support_direction=EvidenceSupportDirection(row.support_direction),
            raw_details=row.payload,
            data_quality_score=row.data_quality_score,
            collector_name=row.collector_name,
            checked_at=row.checked_at,
            source=row.source,
            collected_at=row.collected_at,
        )

    @staticmethod
    def _version_record(row: EvidenceItemVersion) -> EvidenceVersionRecord:
        return EvidenceVersionRecord(
            evidence_id=row.evidence_id,
            investigation_id=row.investigation_id,
            source_type=row.source_type,
            evidence_type=row.evidence_type,
            detected=row.detected,
            confidence=row.confidence,
            support_direction=EvidenceSupportDirection(row.support_direction),
            raw_details=row.payload,
            data_quality_score=row.data_quality_score,
            collector_name=row.collector_name,
            checked_at=row.checked_at,
            source=row.source,
            collected_at=row.collected_at,
            version_id=row.id,
            version_number=row.version_number,
            changed_at=row.changed_at,
            change_reason=row.change_reason,
        )

    @staticmethod
    def _utc(value: datetime) -> datetime:
        if value.tzinfo is None:
            return value.replace(tzinfo=UTC)
        return value.astimezone(UTC)


class EvidenceService:
    def __init__(self, repository: EvidenceRepositoryProtocol) -> None:
        self.repository = repository

    def get_investigation_evidence(
        self,
        investigation_id: int,
        source_type: str | None = None,
        evidence_type: str | None = None,
    ) -> list[EvidenceRecord]:
        return self.repository.list_for_investigation(
            investigation_id,
            source_type=source_type,
            evidence_type=evidence_type,
        )

    def get_supporting_evidence(self, investigation_id: int) -> list[EvidenceRecord]:
        return self.repository.list_for_investigation(
            investigation_id,
            support_direction=EvidenceSupportDirection.SUPPORTS,
        )

    def get_contradictory_evidence(self, investigation_id: int) -> list[EvidenceRecord]:
        return self.repository.list_for_investigation(
            investigation_id,
            support_direction=EvidenceSupportDirection.CONTRADICTS,
        )

    def get_evidence_by_type(self, investigation_id: int, evidence_type: str) -> list[EvidenceRecord]:
        return self.repository.list_for_investigation(investigation_id, evidence_type=evidence_type)

    def add_followup_evidence(self, evidence: EvidenceCreate) -> EvidenceRecord:
        saved = self.repository.add(evidence)
        self.repository.commit()
        return saved

    def update_evidence(
        self,
        evidence_id: int,
        update: EvidenceUpdate,
        reason: str | None = None,
    ) -> EvidenceRecord:
        saved = self.repository.update(evidence_id, update, reason)
        self.repository.commit()
        return saved

    def get_evidence_versions(self, evidence_id: int) -> list[EvidenceVersionRecord]:
        return self.repository.list_versions(evidence_id)
