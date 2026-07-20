from sqlalchemy import select
from sqlalchemy.orm import Session

from .models import Hotspot, HotspotEvent, HotspotObservation, HotspotStatusHistory
from .schemas import (
    HotspotEventRecord,
    HotspotObservationRecord,
    HotspotRecord,
    HotspotStatus,
    HotspotStatusHistoryRecord,
)


ACTIVE_STATUSES = {
    HotspotStatus.ACTIVE,
    HotspotStatus.INVESTIGATING,
    HotspotStatus.WAITING_FOR_EVIDENCE,
    HotspotStatus.ACTION_ASSIGNED,
    HotspotStatus.UNDER_VERIFICATION,
}


class HotspotLifecycleRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def find_active_hotspot_for_candidate(self, candidate) -> HotspotRecord | None:
        statement = (
            select(Hotspot)
            .where(Hotspot.ward_code == candidate.ward_code)
            .where(Hotspot.status.in_([status.value for status in ACTIVE_STATUSES]))
            .order_by(Hotspot.last_detected_at.desc())
            .limit(1)
        )
        row = self.db.scalars(statement).first()
        return self._hotspot(row) if row else None

    def create_hotspot(self, hotspot: HotspotRecord) -> HotspotRecord:
        row = Hotspot(**self._hotspot_values(hotspot))
        self.db.add(row)
        self.db.flush()
        return self._hotspot(row)

    def update_hotspot(self, hotspot: HotspotRecord) -> HotspotRecord:
        if hotspot.id is None:
            raise ValueError("Hotspot id is required for update.")
        row = self.db.get(Hotspot, hotspot.id)
        if row is None:
            raise ValueError("Hotspot not found.")
        for key, value in self._hotspot_values(hotspot).items():
            setattr(row, key, value)
        self.db.flush()
        return self._hotspot(row)

    def get_hotspot(self, hotspot_id: int) -> HotspotRecord | None:
        row = self.db.get(Hotspot, hotspot_id)
        return self._hotspot(row) if row else None

    def list_hotspots(self, status: HotspotStatus | None = None) -> list[HotspotRecord]:
        statement = select(Hotspot)
        if status is not None:
            statement = statement.where(Hotspot.status == status.value)
        statement = statement.order_by(Hotspot.last_detected_at.desc())
        return [self._hotspot(row) for row in self.db.scalars(statement)]

    def add_observation(self, observation: HotspotObservationRecord) -> HotspotObservationRecord:
        row = HotspotObservation(**self._observation_values(observation))
        self.db.add(row)
        self.db.flush()
        return self._observation(row)

    def get_observations(self, hotspot_id: int) -> list[HotspotObservationRecord]:
        statement = (
            select(HotspotObservation)
            .where(HotspotObservation.hotspot_id == hotspot_id)
            .order_by(HotspotObservation.observed_at)
        )
        return [self._observation(row) for row in self.db.scalars(statement)]

    def add_status_history(self, entry: HotspotStatusHistoryRecord) -> HotspotStatusHistoryRecord:
        row = HotspotStatusHistory(**self._status_history_values(entry))
        self.db.add(row)
        self.db.flush()
        return self._status_history(row)

    def get_status_history(self, hotspot_id: int) -> list[HotspotStatusHistoryRecord]:
        statement = (
            select(HotspotStatusHistory)
            .where(HotspotStatusHistory.hotspot_id == hotspot_id)
            .order_by(HotspotStatusHistory.changed_at)
        )
        return [self._status_history(row) for row in self.db.scalars(statement)]

    def add_event(self, event: HotspotEventRecord) -> HotspotEventRecord:
        row = HotspotEvent(**self._event_values(event))
        self.db.add(row)
        self.db.flush()
        return self._event(row)

    def get_events(self, hotspot_id: int) -> list[HotspotEventRecord]:
        statement = (
            select(HotspotEvent)
            .where(HotspotEvent.hotspot_id == hotspot_id)
            .order_by(HotspotEvent.published_at)
        )
        return [self._event(row) for row in self.db.scalars(statement)]

    def commit(self) -> None:
        self.db.commit()

    @staticmethod
    def _hotspot_values(hotspot: HotspotRecord) -> dict:
        return {
            "hotspot_uid": hotspot.hotspot_uid,
            "ward_code": hotspot.ward_code,
            "station_code": hotspot.station_code,
            "station_name": hotspot.station_name,
            "status": hotspot.status.value,
            "severity": hotspot.severity.value,
            "alert_level": hotspot.alert_level.value,
            "current_aqi": hotspot.current_aqi,
            "anomaly_score": hotspot.anomaly_score,
            "data_quality_confidence": hotspot.data_quality_confidence,
            "trigger_reasons": [reason.value for reason in hotspot.trigger_reasons],
            "detection_context": hotspot.detection_context,
            "first_detected_at": hotspot.first_detected_at,
            "last_detected_at": hotspot.last_detected_at,
            "resolved_at": hotspot.resolved_at,
        }

    @staticmethod
    def _observation_values(observation: HotspotObservationRecord) -> dict:
        return {
            "hotspot_id": observation.hotspot_id,
            "station_code": observation.station_code,
            "station_name": observation.station_name,
            "ward_code": observation.ward_code,
            "observed_at": observation.observed_at,
            "aqi": observation.aqi,
            "pollutant_snapshot": observation.pollutant_snapshot,
            "severity": observation.severity.value,
            "alert_level": observation.alert_level.value,
            "trigger_reasons": [reason.value for reason in observation.trigger_reasons],
            "anomaly_score": observation.anomaly_score,
            "data_quality_confidence": observation.data_quality_confidence,
            "detection_context": observation.detection_context,
        }

    @staticmethod
    def _status_history_values(entry: HotspotStatusHistoryRecord) -> dict:
        return {
            "hotspot_id": entry.hotspot_id,
            "from_status": entry.from_status.value if entry.from_status else None,
            "to_status": entry.to_status.value,
            "reason": entry.reason,
            "changed_by": entry.changed_by,
            "changed_at": entry.changed_at,
        }

    @staticmethod
    def _event_values(event: HotspotEventRecord) -> dict:
        return {
            "hotspot_id": event.hotspot_id,
            "event_type": event.event_type,
            "payload": event.payload,
            "published_at": event.published_at,
        }

    @staticmethod
    def _hotspot(row: Hotspot) -> HotspotRecord:
        return HotspotRecord(
            id=row.id,
            hotspot_uid=row.hotspot_uid,
            ward_code=row.ward_code,
            station_code=row.station_code,
            station_name=row.station_name,
            status=HotspotStatus(row.status),
            severity=row.severity,
            alert_level=row.alert_level,
            current_aqi=row.current_aqi,
            anomaly_score=row.anomaly_score,
            data_quality_confidence=row.data_quality_confidence,
            trigger_reasons=row.trigger_reasons,
            detection_context=row.detection_context,
            first_detected_at=row.first_detected_at,
            last_detected_at=row.last_detected_at,
            resolved_at=row.resolved_at,
            created_at=row.created_at,
            updated_at=row.updated_at,
        )

    @staticmethod
    def _observation(row: HotspotObservation) -> HotspotObservationRecord:
        return HotspotObservationRecord(
            id=row.id,
            hotspot_id=row.hotspot_id,
            station_code=row.station_code,
            station_name=row.station_name,
            ward_code=row.ward_code,
            observed_at=row.observed_at,
            aqi=row.aqi,
            pollutant_snapshot=row.pollutant_snapshot,
            severity=row.severity,
            alert_level=row.alert_level,
            trigger_reasons=row.trigger_reasons,
            anomaly_score=row.anomaly_score,
            data_quality_confidence=row.data_quality_confidence,
            detection_context=row.detection_context,
        )

    @staticmethod
    def _status_history(row: HotspotStatusHistory) -> HotspotStatusHistoryRecord:
        return HotspotStatusHistoryRecord(
            id=row.id,
            hotspot_id=row.hotspot_id,
            from_status=HotspotStatus(row.from_status) if row.from_status else None,
            to_status=HotspotStatus(row.to_status),
            reason=row.reason,
            changed_by=row.changed_by,
            changed_at=row.changed_at,
        )

    @staticmethod
    def _event(row: HotspotEvent) -> HotspotEventRecord:
        return HotspotEventRecord(
            id=row.id,
            hotspot_id=row.hotspot_id,
            event_type=row.event_type,
            payload=row.payload,
            published_at=row.published_at,
        )
