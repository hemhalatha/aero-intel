from sqlalchemy import select
from sqlalchemy.orm import Session

from .models import EvidenceCollectionRun, EvidenceItem, Investigation, InvestigationEvent
from .schemas import (
    CollectionStatus,
    EvidenceCollectionRunRecord,
    EvidenceItemRecord,
    InvestigationEventRecord,
    InvestigationRecord,
    InvestigationStatus,
)


class InvestigationRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def find_by_hotspot_id(self, hotspot_id: int) -> InvestigationRecord | None:
        row = self.db.scalars(select(Investigation).where(Investigation.hotspot_id == hotspot_id).limit(1)).first()
        return self._investigation(row) if row else None

    def create_investigation(self, investigation: InvestigationRecord) -> InvestigationRecord:
        row = Investigation(**self._investigation_values(investigation))
        self.db.add(row)
        self.db.flush()
        return self._investigation(row)

    def update_investigation(self, investigation: InvestigationRecord) -> InvestigationRecord:
        if investigation.id is None:
            raise ValueError("Investigation id is required for update.")
        row = self.db.get(Investigation, investigation.id)
        if row is None:
            raise ValueError("Investigation not found.")
        for key, value in self._investigation_values(investigation).items():
            setattr(row, key, value)
        self.db.flush()
        return self._investigation(row)

    def get_investigation(self, investigation_id: int) -> InvestigationRecord | None:
        row = self.db.get(Investigation, investigation_id)
        return self._investigation(row) if row else None

    def list_investigations(self, status: InvestigationStatus | None = None) -> list[InvestigationRecord]:
        statement = select(Investigation)
        if status is not None:
            statement = statement.where(Investigation.status == status.value)
        statement = statement.order_by(Investigation.created_at.desc())
        return [self._investigation(row) for row in self.db.scalars(statement)]

    def add_collector_run(self, run: EvidenceCollectionRunRecord) -> EvidenceCollectionRunRecord:
        row = EvidenceCollectionRun(**self._collector_run_values(run))
        self.db.add(row)
        self.db.flush()
        return self._collector_run(row)

    def update_collector_run(self, run: EvidenceCollectionRunRecord) -> EvidenceCollectionRunRecord:
        if run.id is None:
            raise ValueError("Collector run id is required for update.")
        row = self.db.get(EvidenceCollectionRun, run.id)
        if row is None:
            raise ValueError("Collector run not found.")
        for key, value in self._collector_run_values(run).items():
            setattr(row, key, value)
        self.db.flush()
        return self._collector_run(row)

    def get_collector_runs(self, investigation_id: int) -> list[EvidenceCollectionRunRecord]:
        statement = (
            select(EvidenceCollectionRun)
            .where(EvidenceCollectionRun.investigation_id == investigation_id)
            .order_by(EvidenceCollectionRun.started_at)
        )
        return [self._collector_run(row) for row in self.db.scalars(statement)]

    def add_evidence_item(self, evidence: EvidenceItemRecord) -> EvidenceItemRecord:
        row = EvidenceItem(**self._evidence_values(evidence))
        self.db.add(row)
        self.db.flush()
        return self._evidence(row)

    def get_evidence_items(self, investigation_id: int) -> list[EvidenceItemRecord]:
        statement = (
            select(EvidenceItem)
            .where(EvidenceItem.investigation_id == investigation_id)
            .order_by(EvidenceItem.collected_at)
        )
        return [self._evidence(row) for row in self.db.scalars(statement)]

    def add_event(self, event: InvestigationEventRecord) -> InvestigationEventRecord:
        row = InvestigationEvent(**self._event_values(event))
        self.db.add(row)
        self.db.flush()
        return self._event(row)

    def get_events(self, investigation_id: int) -> list[InvestigationEventRecord]:
        statement = (
            select(InvestigationEvent)
            .where(InvestigationEvent.investigation_id == investigation_id)
            .order_by(InvestigationEvent.published_at)
        )
        return [self._event(row) for row in self.db.scalars(statement)]

    def commit(self) -> None:
        self.db.commit()

    @staticmethod
    def _investigation_values(investigation: InvestigationRecord) -> dict:
        return {
            "investigation_uid": investigation.investigation_uid,
            "hotspot_id": investigation.hotspot_id,
            "hotspot_uid": investigation.hotspot_uid,
            "ward_code": investigation.ward_code,
            "station_code": investigation.station_code,
            "status": investigation.status.value,
            "environmental_context": investigation.environmental_context,
            "last_collection_started_at": investigation.last_collection_started_at,
            "last_collection_completed_at": investigation.last_collection_completed_at,
        }

    @staticmethod
    def _collector_run_values(run: EvidenceCollectionRunRecord) -> dict:
        return {
            "investigation_id": run.investigation_id,
            "collector_name": run.collector_name,
            "status": run.status.value,
            "started_at": run.started_at,
            "completed_at": run.completed_at,
            "error_message": run.error_message,
            "evidence_count": run.evidence_count,
            "request_reason": run.request_reason,
        }

    @staticmethod
    def _evidence_values(evidence: EvidenceItemRecord) -> dict:
        return {
            "investigation_id": evidence.investigation_id,
            "collector_name": evidence.collector_name,
            "source_type": evidence.source_type,
            "evidence_type": evidence.evidence_type,
            "source": evidence.source,
            "detected": evidence.detected,
            "support_direction": evidence.support_direction,
            "payload": evidence.payload,
            "observed_at": evidence.observed_at,
            "collected_at": evidence.collected_at,
            "confidence": evidence.confidence,
        }

    @staticmethod
    def _event_values(event: InvestigationEventRecord) -> dict:
        return {
            "investigation_id": event.investigation_id,
            "event_type": event.event_type,
            "payload": event.payload,
            "published_at": event.published_at,
        }

    @staticmethod
    def _investigation(row: Investigation) -> InvestigationRecord:
        return InvestigationRecord(
            id=row.id,
            investigation_uid=row.investigation_uid,
            hotspot_id=row.hotspot_id,
            hotspot_uid=row.hotspot_uid,
            ward_code=row.ward_code,
            station_code=row.station_code,
            status=InvestigationStatus(row.status),
            environmental_context=row.environmental_context,
            created_at=row.created_at,
            updated_at=row.updated_at,
            last_collection_started_at=row.last_collection_started_at,
            last_collection_completed_at=row.last_collection_completed_at,
        )

    @staticmethod
    def _collector_run(row: EvidenceCollectionRun) -> EvidenceCollectionRunRecord:
        return EvidenceCollectionRunRecord(
            id=row.id,
            investigation_id=row.investigation_id,
            collector_name=row.collector_name,
            status=CollectionStatus(row.status),
            started_at=row.started_at,
            completed_at=row.completed_at,
            error_message=row.error_message,
            evidence_count=row.evidence_count,
            request_reason=row.request_reason,
        )

    @staticmethod
    def _evidence(row: EvidenceItem) -> EvidenceItemRecord:
        return EvidenceItemRecord(
            id=row.id,
            investigation_id=row.investigation_id,
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
        )

    @staticmethod
    def _event(row: InvestigationEvent) -> InvestigationEventRecord:
        return InvestigationEventRecord(
            id=row.id,
            investigation_id=row.investigation_id,
            event_type=row.event_type,
            payload=row.payload,
            published_at=row.published_at,
        )
