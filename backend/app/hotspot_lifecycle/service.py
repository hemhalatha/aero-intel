from datetime import UTC, datetime
from typing import Any, Protocol
from uuid import uuid4

from app.hotspots.schemas import HotspotCandidate, HotspotSeverity

from .schemas import (
    HotspotDetail,
    HotspotEventRecord,
    HotspotObservationRecord,
    HotspotRecord,
    HotspotStateUpdate,
    HotspotStatus,
    HotspotStatusHistoryRecord,
)


class HotspotLifecycleRepositoryProtocol(Protocol):
    def find_active_hotspot_for_candidate(self, candidate: HotspotCandidate) -> HotspotRecord | None:
        ...

    def create_hotspot(self, hotspot: HotspotRecord) -> HotspotRecord:
        ...

    def update_hotspot(self, hotspot: HotspotRecord) -> HotspotRecord:
        ...

    def get_hotspot(self, hotspot_id: int) -> HotspotRecord | None:
        ...

    def list_hotspots(self, status: HotspotStatus | None = None) -> list[HotspotRecord]:
        ...

    def add_observation(self, observation: HotspotObservationRecord) -> HotspotObservationRecord:
        ...

    def get_observations(self, hotspot_id: int) -> list[HotspotObservationRecord]:
        ...

    def add_status_history(self, entry: HotspotStatusHistoryRecord) -> HotspotStatusHistoryRecord:
        ...

    def get_status_history(self, hotspot_id: int) -> list[HotspotStatusHistoryRecord]:
        ...

    def add_event(self, event: HotspotEventRecord) -> HotspotEventRecord:
        ...

    def get_events(self, hotspot_id: int) -> list[HotspotEventRecord]:
        ...

    def commit(self) -> None:
        ...


class HotspotLifecycleService:
    def __init__(self, repository: HotspotLifecycleRepositoryProtocol) -> None:
        self.repository = repository

    def ingest_candidate(
        self,
        candidate: HotspotCandidate,
        detection_context: dict[str, Any] | None = None,
        now: datetime | None = None,
    ) -> HotspotRecord:
        timestamp = now or datetime.now(UTC)
        detection_context = detection_context or {}
        existing = self.repository.find_active_hotspot_for_candidate(candidate)
        if existing is None:
            hotspot = self._create_hotspot(candidate, detection_context, timestamp)
        else:
            hotspot = self._update_existing_hotspot(existing, candidate, detection_context, timestamp)
        self.repository.commit()
        return hotspot

    def list_hotspots(self, status: HotspotStatus | None = None) -> list[HotspotRecord]:
        return self.repository.list_hotspots(status)

    def get_hotspot_detail(self, hotspot_id: int) -> HotspotDetail:
        hotspot = self.repository.get_hotspot(hotspot_id)
        if hotspot is None:
            raise ValueError("Hotspot not found.")
        return HotspotDetail(
            hotspot=hotspot,
            observations=self.repository.get_observations(hotspot_id),
            status_history=self.repository.get_status_history(hotspot_id),
            events=self.repository.get_events(hotspot_id),
        )

    def update_hotspot_state(
        self,
        hotspot_id: int,
        update: HotspotStateUpdate,
        now: datetime | None = None,
    ) -> HotspotRecord:
        timestamp = now or datetime.now(UTC)
        hotspot = self.repository.get_hotspot(hotspot_id)
        if hotspot is None:
            raise ValueError("Hotspot not found.")
        if hotspot.status == update.status:
            return hotspot

        previous_status = hotspot.status
        updated = hotspot.model_copy(
            update={
                "status": update.status,
                "resolved_at": timestamp if update.status == HotspotStatus.RESOLVED else None,
            }
        )
        saved = self.repository.update_hotspot(updated)
        self._record_status_change(saved.id, previous_status, update.status, update.reason, update.changed_by, timestamp)
        self._publish_event(
            saved,
            "hotspot.resolved" if update.status == HotspotStatus.RESOLVED else "hotspot.updated",
            timestamp,
            {"from_status": previous_status.value, "to_status": update.status.value, "reason": update.reason},
        )
        self.repository.commit()
        return saved

    def _create_hotspot(
        self,
        candidate: HotspotCandidate,
        detection_context: dict[str, Any],
        timestamp: datetime,
    ) -> HotspotRecord:
        hotspot = HotspotRecord(
            hotspot_uid=f"hs-{uuid4().hex[:12]}",
            ward_code=candidate.ward_code,
            station_code=candidate.station_code,
            station_name=candidate.station_name,
            status=HotspotStatus.ACTIVE,
            severity=candidate.severity,
            alert_level=candidate.alert_level,
            current_aqi=candidate.aqi,
            anomaly_score=candidate.anomaly_score,
            data_quality_confidence=candidate.data_quality_confidence,
            trigger_reasons=candidate.trigger_reasons,
            detection_context=detection_context,
            first_detected_at=candidate.observed_at,
            last_detected_at=candidate.observed_at,
        )
        saved = self.repository.create_hotspot(hotspot)
        self._record_observation(saved.id, candidate, detection_context)
        self._record_status_change(saved.id, None, HotspotStatus.ACTIVE, "Initial detection", None, timestamp)
        self._publish_event(saved, "hotspot.created", timestamp, {"candidate": self._candidate_payload(candidate)})
        return saved

    def _update_existing_hotspot(
        self,
        existing: HotspotRecord,
        candidate: HotspotCandidate,
        detection_context: dict[str, Any],
        timestamp: datetime,
    ) -> HotspotRecord:
        escalated = self._severity_rank(candidate.severity) > self._severity_rank(existing.severity)
        saved = self.repository.update_hotspot(
            existing.model_copy(
                update={
                    "station_code": candidate.station_code,
                    "station_name": candidate.station_name,
                    "severity": candidate.severity if escalated else existing.severity,
                    "alert_level": candidate.alert_level if escalated else existing.alert_level,
                    "current_aqi": candidate.aqi,
                    "anomaly_score": candidate.anomaly_score,
                    "data_quality_confidence": candidate.data_quality_confidence,
                    "trigger_reasons": candidate.trigger_reasons,
                    "detection_context": detection_context or existing.detection_context,
                    "last_detected_at": candidate.observed_at,
                }
            )
        )
        self._record_observation(saved.id, candidate, detection_context)
        self._publish_event(
            saved,
            "hotspot.escalated" if escalated else "hotspot.updated",
            timestamp,
            {"candidate": self._candidate_payload(candidate), "escalated": escalated},
        )
        return saved

    def _record_observation(
        self,
        hotspot_id: int | None,
        candidate: HotspotCandidate,
        detection_context: dict[str, Any],
    ) -> None:
        if hotspot_id is None:
            raise ValueError("Hotspot id is required to record observation.")
        self.repository.add_observation(
            HotspotObservationRecord(
                hotspot_id=hotspot_id,
                station_code=candidate.station_code,
                station_name=candidate.station_name,
                ward_code=candidate.ward_code,
                observed_at=candidate.observed_at,
                aqi=candidate.aqi,
                pollutant_snapshot=candidate.pollutant_snapshot,
                severity=candidate.severity,
                alert_level=candidate.alert_level,
                trigger_reasons=candidate.trigger_reasons,
                anomaly_score=candidate.anomaly_score,
                data_quality_confidence=candidate.data_quality_confidence,
                detection_context=detection_context,
            )
        )

    def _record_status_change(
        self,
        hotspot_id: int | None,
        from_status: HotspotStatus | None,
        to_status: HotspotStatus,
        reason: str | None,
        changed_by: str | None,
        changed_at: datetime,
    ) -> None:
        if hotspot_id is None:
            raise ValueError("Hotspot id is required to record status history.")
        self.repository.add_status_history(
            HotspotStatusHistoryRecord(
                hotspot_id=hotspot_id,
                from_status=from_status,
                to_status=to_status,
                reason=reason,
                changed_by=changed_by,
                changed_at=changed_at,
            )
        )

    def _publish_event(
        self,
        hotspot: HotspotRecord,
        event_type: str,
        published_at: datetime,
        payload: dict[str, Any],
    ) -> None:
        if hotspot.id is None:
            raise ValueError("Hotspot id is required to publish event.")
        self.repository.add_event(
            HotspotEventRecord(
                hotspot_id=hotspot.id,
                event_type=event_type,
                payload={"hotspot_uid": hotspot.hotspot_uid, **payload},
                published_at=published_at,
            )
        )

    @staticmethod
    def _severity_rank(severity: HotspotSeverity) -> int:
        return {
            HotspotSeverity.LOW: 1,
            HotspotSeverity.MEDIUM: 2,
            HotspotSeverity.HIGH: 3,
            HotspotSeverity.CRITICAL: 4,
        }[severity]

    @staticmethod
    def _candidate_payload(candidate: HotspotCandidate) -> dict[str, Any]:
        return {
            "ward_code": candidate.ward_code,
            "station_code": candidate.station_code,
            "aqi": candidate.aqi,
            "severity": candidate.severity.value,
            "alert_level": candidate.alert_level.value,
            "trigger_reasons": [reason.value for reason in candidate.trigger_reasons],
            "anomaly_score": candidate.anomaly_score,
            "observed_at": candidate.observed_at.isoformat(),
            "data_quality_confidence": candidate.data_quality_confidence,
        }
