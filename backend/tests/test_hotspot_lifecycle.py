from datetime import UTC, datetime, timedelta

import pytest

from app.hotspot_lifecycle.schemas import HotspotStatus, HotspotStateUpdate
from app.hotspot_lifecycle.service import HotspotLifecycleService
from app.hotspots.schemas import AlertLevel, HotspotCandidate, HotspotSeverity, HotspotTrigger


NOW = datetime(2025, 1, 15, 12, tzinfo=UTC)


class FakeHotspotLifecycleRepository:
    def __init__(self) -> None:
        self.hotspots = {}
        self.observations = []
        self.status_history = []
        self.events = []
        self.next_id = 1

    def find_active_hotspot_for_candidate(self, candidate):
        for hotspot in self.hotspots.values():
            if hotspot.ward_code == candidate.ward_code and hotspot.status != HotspotStatus.RESOLVED:
                return hotspot
        return None

    def create_hotspot(self, hotspot):
        saved = hotspot.model_copy(update={"id": self.next_id})
        self.hotspots[saved.id] = saved
        self.next_id += 1
        return saved

    def update_hotspot(self, hotspot):
        self.hotspots[hotspot.id] = hotspot
        return hotspot

    def get_hotspot(self, hotspot_id):
        return self.hotspots.get(hotspot_id)

    def list_hotspots(self, status=None):
        records = list(self.hotspots.values())
        if status is not None:
            records = [item for item in records if item.status == status]
        return sorted(records, key=lambda item: item.last_detected_at, reverse=True)

    def add_observation(self, observation):
        saved = observation.model_copy(update={"id": len(self.observations) + 1})
        self.observations.append(saved)
        return saved

    def get_observations(self, hotspot_id):
        return [item for item in self.observations if item.hotspot_id == hotspot_id]

    def add_status_history(self, entry):
        saved = entry.model_copy(update={"id": len(self.status_history) + 1})
        self.status_history.append(saved)
        return saved

    def get_status_history(self, hotspot_id):
        return [item for item in self.status_history if item.hotspot_id == hotspot_id]

    def add_event(self, event):
        saved = event.model_copy(update={"id": len(self.events) + 1})
        self.events.append(saved)
        return saved

    def get_events(self, hotspot_id):
        return [item for item in self.events if item.hotspot_id == hotspot_id]


    def commit(self):
        return None

def candidate(
    ward_code: str = "BLR-W-001",
    station_code: str = "BLR-CBD-AQ",
    aqi: float = 225,
    severity: HotspotSeverity = HotspotSeverity.HIGH,
    observed_at: datetime = NOW,
) -> HotspotCandidate:
    return HotspotCandidate(
        ward_code=ward_code,
        station_code=station_code,
        station_name=f"{station_code} Station",
        aqi=aqi,
        pollutant_snapshot={"AQI": aqi, "PM2.5": 112, "NO2": 44},
        severity=severity,
        alert_level=AlertLevel.WARNING if severity == HotspotSeverity.HIGH else AlertLevel.WATCH,
        trigger_reasons=[HotspotTrigger.AQI_THRESHOLD],
        anomaly_score=1.4,
        observed_at=observed_at,
        data_quality_confidence=0.91,
    )


def test_creates_hotspot_with_observation_status_history_context_and_event() -> None:
    repository = FakeHotspotLifecycleRepository()
    service = HotspotLifecycleService(repository)

    hotspot = service.ingest_candidate(candidate(), detection_context={"baseline_aqi": 125}, now=NOW)

    assert hotspot.id == 1
    assert hotspot.status == HotspotStatus.ACTIVE
    assert hotspot.current_aqi == 225
    assert hotspot.detection_context == {"baseline_aqi": 125}
    assert len(repository.observations) == 1
    assert repository.observations[0].pollutant_snapshot["PM2.5"] == 112
    assert repository.status_history[0].to_status == HotspotStatus.ACTIVE
    assert repository.events[0].event_type == "hotspot.created"


def test_updates_existing_active_hotspot_in_same_ward_and_preserves_history() -> None:
    repository = FakeHotspotLifecycleRepository()
    service = HotspotLifecycleService(repository)
    first = service.ingest_candidate(candidate(aqi=210, severity=HotspotSeverity.MEDIUM), now=NOW)

    updated = service.ingest_candidate(
        candidate(station_code="BLR-ALT-AQ", aqi=275, severity=HotspotSeverity.HIGH, observed_at=NOW + timedelta(hours=1)),
        detection_context={"threshold": 200},
        now=NOW + timedelta(hours=1),
    )

    assert updated.id == first.id
    assert updated.station_code == "BLR-ALT-AQ"
    assert updated.current_aqi == 275
    assert updated.severity == HotspotSeverity.HIGH
    assert len(repository.observations) == 2
    assert [event.event_type for event in repository.events] == ["hotspot.created", "hotspot.escalated"]


def test_updates_existing_hotspot_without_escalation_when_conditions_do_not_worsen() -> None:
    repository = FakeHotspotLifecycleRepository()
    service = HotspotLifecycleService(repository)
    first = service.ingest_candidate(candidate(aqi=260, severity=HotspotSeverity.HIGH), now=NOW)

    updated = service.ingest_candidate(
        candidate(aqi=230, severity=HotspotSeverity.MEDIUM, observed_at=NOW + timedelta(minutes=30)),
        now=NOW + timedelta(minutes=30),
    )

    assert updated.id == first.id
    assert updated.severity == HotspotSeverity.HIGH
    assert updated.current_aqi == 230
    assert [event.event_type for event in repository.events] == ["hotspot.created", "hotspot.updated"]


def test_updates_hotspot_state_and_publishes_resolution_event() -> None:
    repository = FakeHotspotLifecycleRepository()
    service = HotspotLifecycleService(repository)
    hotspot = service.ingest_candidate(candidate(), now=NOW)

    resolved = service.update_hotspot_state(
        hotspot.id,
        HotspotStateUpdate(status=HotspotStatus.RESOLVED, reason="AQI returned to baseline", changed_by="ops"),
        now=NOW + timedelta(hours=3),
    )

    assert resolved.status == HotspotStatus.RESOLVED
    assert resolved.resolved_at == NOW + timedelta(hours=3)
    assert repository.status_history[-1].from_status == HotspotStatus.ACTIVE
    assert repository.status_history[-1].to_status == HotspotStatus.RESOLVED
    assert repository.events[-1].event_type == "hotspot.resolved"


def test_raises_for_unknown_hotspot_state_update() -> None:
    service = HotspotLifecycleService(FakeHotspotLifecycleRepository())

    with pytest.raises(ValueError, match="Hotspot not found"):
        service.update_hotspot_state(
            999,
            HotspotStateUpdate(status=HotspotStatus.INVESTIGATING, reason="manual review"),
            now=NOW,
        )
