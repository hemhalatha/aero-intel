from datetime import UTC, datetime
from typing import Any, Protocol
from uuid import uuid4

from app.hotspot_lifecycle.schemas import HotspotEventRecord

from .collectors import EvidenceCollector
from .schemas import (
    CollectionStatus,
    EvidenceCollectionRunRecord,
    EvidenceItemRecord,
    InvestigationDetail,
    InvestigationEventRecord,
    InvestigationRecord,
    InvestigationStatus,
)


class InvestigationRepositoryProtocol(Protocol):
    def find_by_hotspot_id(self, hotspot_id: int) -> InvestigationRecord | None:
        ...

    def create_investigation(self, investigation: InvestigationRecord) -> InvestigationRecord:
        ...

    def update_investigation(self, investigation: InvestigationRecord) -> InvestigationRecord:
        ...

    def get_investigation(self, investigation_id: int) -> InvestigationRecord | None:
        ...

    def list_investigations(self, status: InvestigationStatus | None = None) -> list[InvestigationRecord]:
        ...

    def add_collector_run(self, run: EvidenceCollectionRunRecord) -> EvidenceCollectionRunRecord:
        ...

    def update_collector_run(self, run: EvidenceCollectionRunRecord) -> EvidenceCollectionRunRecord:
        ...

    def get_collector_runs(self, investigation_id: int) -> list[EvidenceCollectionRunRecord]:
        ...

    def add_evidence_item(self, evidence: EvidenceItemRecord) -> EvidenceItemRecord:
        ...

    def get_evidence_items(self, investigation_id: int) -> list[EvidenceItemRecord]:
        ...

    def add_event(self, event: InvestigationEventRecord) -> InvestigationEventRecord:
        ...

    def get_events(self, investigation_id: int) -> list[InvestigationEventRecord]:
        ...

    def commit(self) -> None:
        ...


class EnvironmentalContextProvider(Protocol):
    def capture_context(self, hotspot_id: int) -> dict[str, Any]:
        ...


class EmptyEnvironmentalContextProvider:
    def capture_context(self, hotspot_id: int) -> dict[str, Any]:
        return {"hotspot_id": hotspot_id}


class HotspotLifecycleContextProvider:
    def __init__(self, hotspot_lifecycle_service) -> None:
        self.hotspot_lifecycle_service = hotspot_lifecycle_service

    def capture_context(self, hotspot_id: int) -> dict[str, Any]:
        detail = self.hotspot_lifecycle_service.get_hotspot_detail(hotspot_id)
        return {
            "hotspot": detail.hotspot.model_dump(mode="json"),
            "latest_observation": detail.observations[-1].model_dump(mode="json") if detail.observations else None,
            "status_history_count": len(detail.status_history),
        }


class InvestigationOrchestrator:
    def __init__(
        self,
        repository: InvestigationRepositoryProtocol,
        context_provider: EnvironmentalContextProvider | None = None,
        collectors: list[EvidenceCollector] | None = None,
    ) -> None:
        self.repository = repository
        self.context_provider = context_provider or EmptyEnvironmentalContextProvider()
        self.collectors = collectors or []

    def handle_hotspot_created(
        self,
        event: HotspotEventRecord,
        now: datetime | None = None,
    ) -> InvestigationRecord:
        if event.event_type != "hotspot.created":
            raise ValueError("Investigation orchestrator only handles hotspot.created events.")
        timestamp = now or datetime.now(UTC)
        investigation = self.repository.find_by_hotspot_id(event.hotspot_id)
        if investigation is None:
            investigation = self._create_investigation(event, timestamp)
        return self._run_collectors(investigation, None, "hotspot.created", timestamp)

    def collect_additional_evidence(
        self,
        investigation_id: int,
        requested_collectors: list[str] | None = None,
        reason: str | None = None,
        now: datetime | None = None,
    ) -> InvestigationRecord:
        timestamp = now or datetime.now(UTC)
        investigation = self.repository.get_investigation(investigation_id)
        if investigation is None:
            raise ValueError("Investigation not found.")
        return self._run_collectors(investigation, requested_collectors, reason, timestamp)

    def list_investigations(self, status: InvestigationStatus | None = None) -> list[InvestigationRecord]:
        return self.repository.list_investigations(status)

    def get_investigation_detail(self, investigation_id: int) -> InvestigationDetail:
        investigation = self.repository.get_investigation(investigation_id)
        if investigation is None:
            raise ValueError("Investigation not found.")
        return InvestigationDetail(
            investigation=investigation,
            collector_runs=self.repository.get_collector_runs(investigation_id),
            evidence_items=self.repository.get_evidence_items(investigation_id),
            events=self.repository.get_events(investigation_id),
        )

    def _create_investigation(self, event: HotspotEventRecord, timestamp: datetime) -> InvestigationRecord:
        context = self.context_provider.capture_context(event.hotspot_id)
        candidate = event.payload.get("candidate", {})
        investigation = InvestigationRecord(
            investigation_uid=f"inv-{uuid4().hex[:12]}",
            hotspot_id=event.hotspot_id,
            hotspot_uid=event.payload.get("hotspot_uid"),
            ward_code=candidate.get("ward_code") or context.get("ward_code"),
            station_code=candidate.get("station_code") or context.get("station_code"),
            status=InvestigationStatus.WAITING_FOR_EVIDENCE,
            environmental_context=context,
            created_at=timestamp,
        )
        return self.repository.create_investigation(investigation)

    def _run_collectors(
        self,
        investigation: InvestigationRecord,
        requested_collectors: list[str] | None,
        reason: str | None,
        timestamp: datetime,
    ) -> InvestigationRecord:
        selected = self._enabled_collectors(requested_collectors)
        refreshed = investigation.model_copy(update={"last_collection_started_at": timestamp})
        refreshed = self.repository.update_investigation(refreshed)
        successes = 0
        failures = 0

        for collector in selected:
            run = self.repository.add_collector_run(
                EvidenceCollectionRunRecord(
                    investigation_id=refreshed.id,
                    collector_name=collector.name,
                    status=CollectionStatus.RUNNING,
                    started_at=timestamp,
                    request_reason=reason,
                )
            )
            try:
                results = collector.collect(refreshed, refreshed.environmental_context)
                for result in results:
                    evidence = self.repository.add_evidence_item(
                        EvidenceItemRecord(
                            investigation_id=refreshed.id,
                            collector_name=collector.name,
                            source_type=result.source_type,
                            evidence_type=result.evidence_type,
                            source=result.source,
                            detected=result.detected,
                            support_direction=result.support_direction,
                            payload=result.payload,
                            observed_at=result.observed_at,
                            collected_at=timestamp,
                            confidence=result.confidence,
                        )
                    )
                    self._publish_event(
                        refreshed.id,
                        "evidence.collected",
                        {
                            "collector_name": collector.name,
                            "evidence_id": evidence.id,
                            "source_type": evidence.source_type,
                            "evidence_type": evidence.evidence_type,
                            "source": evidence.source,
                            "detected": evidence.detected,
                            "support_direction": evidence.support_direction,
                        },
                        timestamp,
                    )
                successes += 1 if results else 0
                run = run.model_copy(
                    update={
                        "status": CollectionStatus.SUCCEEDED,
                        "completed_at": timestamp,
                        "evidence_count": len(results),
                    }
                )
                self.repository.update_collector_run(run)
                self.repository.commit()
            except Exception as exc:
                failures += 1
                run = run.model_copy(
                    update={
                        "status": CollectionStatus.FAILED,
                        "completed_at": timestamp,
                        "error_message": str(exc),
                    }
                )
                self.repository.update_collector_run(run)
                self.repository.commit()

        status = self._completion_status(successes, failures, len(selected))
        completed = self.repository.update_investigation(
            refreshed.model_copy(
                update={
                    "status": status,
                    "last_collection_completed_at": timestamp,
                }
            )
        )
        self._publish_event(
            completed.id,
            "investigation.initial_collection_completed",
            {
                "status": status.value,
                "successful_collectors": successes,
                "failed_collectors": failures,
                "collector_count": len(selected),
                "reason": reason,
            },
            timestamp,
        )
        self.repository.commit()
        return completed

    def _enabled_collectors(self, requested_collectors: list[str] | None) -> list[EvidenceCollector]:
        requested = set(requested_collectors or [])
        return [
            collector
            for collector in self.collectors
            if collector.enabled and (not requested or collector.name in requested)
        ]

    @staticmethod
    def _completion_status(successes: int, failures: int, collector_count: int) -> InvestigationStatus:
        if successes == 0:
            return InvestigationStatus.WAITING_FOR_EVIDENCE
        if failures or successes < collector_count:
            return InvestigationStatus.PARTIALLY_COMPLETE
        return InvestigationStatus.COMPLETE

    def _publish_event(
        self,
        investigation_id: int | None,
        event_type: str,
        payload: dict[str, Any],
        published_at: datetime,
    ) -> None:
        if investigation_id is None:
            raise ValueError("Investigation id is required to publish event.")
        self.repository.add_event(
            InvestigationEventRecord(
                investigation_id=investigation_id,
                event_type=event_type,
                payload=payload,
                published_at=published_at,
            )
        )
