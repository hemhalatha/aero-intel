from datetime import UTC, datetime

from app.hotspot_lifecycle.schemas import HotspotEventRecord
from app.investigations.collectors import CollectorResult, EvidenceCollector
from app.investigations.schemas import CollectionStatus, InvestigationStatus
from app.investigations.service import InvestigationOrchestrator


NOW = datetime(2025, 1, 15, 12, tzinfo=UTC)


class FakeInvestigationRepository:
    def __init__(self) -> None:
        self.investigations = {}
        self.collector_runs = []
        self.evidence = []
        self.events = []
        self.next_id = 1

    def find_by_hotspot_id(self, hotspot_id):
        return next((item for item in self.investigations.values() if item.hotspot_id == hotspot_id), None)

    def create_investigation(self, investigation):
        saved = investigation.model_copy(update={"id": self.next_id})
        self.investigations[saved.id] = saved
        self.next_id += 1
        return saved

    def update_investigation(self, investigation):
        self.investigations[investigation.id] = investigation
        return investigation

    def get_investigation(self, investigation_id):
        return self.investigations.get(investigation_id)

    def list_investigations(self, status=None):
        records = list(self.investigations.values())
        if status is not None:
            records = [item for item in records if item.status == status]
        return records

    def add_collector_run(self, run):
        saved = run.model_copy(update={"id": len(self.collector_runs) + 1})
        self.collector_runs.append(saved)
        return saved

    def update_collector_run(self, run):
        self.collector_runs = [run if item.id == run.id else item for item in self.collector_runs]
        return run

    def get_collector_runs(self, investigation_id):
        return [item for item in self.collector_runs if item.investigation_id == investigation_id]

    def add_evidence_item(self, evidence):
        saved = evidence.model_copy(update={"id": len(self.evidence) + 1})
        self.evidence.append(saved)
        return saved

    def get_evidence_items(self, investigation_id):
        return [item for item in self.evidence if item.investigation_id == investigation_id]

    def add_event(self, event):
        saved = event.model_copy(update={"id": len(self.events) + 1})
        self.events.append(saved)
        return saved

    def get_events(self, investigation_id):
        return [item for item in self.events if item.investigation_id == investigation_id]

    def commit(self):
        return None


class FakeContextProvider:
    def capture_context(self, hotspot_id):
        return {
            "hotspot_id": hotspot_id,
            "ward_code": "BLR-W-001",
            "latest_aqi": 225,
            "weather": {"wind_speed_kmh": 13.5},
        }


class StaticCollector(EvidenceCollector):
    def __init__(self, name, enabled=True, fail=False, items=None):
        self.name = name
        self.enabled = enabled
        self.fail = fail
        self.items = items or [{"metric": "traffic_volume", "value": 1820}]

    def collect(self, investigation, context):
        if self.fail:
            raise RuntimeError(f"{self.name} unavailable")
        return [
            CollectorResult(
                evidence_type=f"{self.name}.signal",
                source=self.name,
                payload=item,
                observed_at=NOW,
                confidence=0.82,
            )
            for item in self.items
        ]


def hotspot_created_event() -> HotspotEventRecord:
    return HotspotEventRecord(
        id=1,
        hotspot_id=42,
        event_type="hotspot.created",
        payload={"hotspot_uid": "hs-test", "candidate": {"ward_code": "BLR-W-001"}},
        published_at=NOW,
    )


def test_hotspot_created_starts_collectors_preserves_partial_results_and_publishes_events() -> None:
    repository = FakeInvestigationRepository()
    service = InvestigationOrchestrator(
        repository=repository,
        context_provider=FakeContextProvider(),
        collectors=[
            StaticCollector("traffic"),
            StaticCollector("construction", fail=True),
            StaticCollector("industrial", enabled=False),
        ],
    )

    investigation = service.handle_hotspot_created(hotspot_created_event(), now=NOW)

    assert investigation.hotspot_id == 42
    assert investigation.status == InvestigationStatus.PARTIALLY_COMPLETE
    assert investigation.environmental_context["latest_aqi"] == 225
    assert len(repository.evidence) == 1
    assert repository.evidence[0].source == "traffic"
    assert [run.status for run in repository.collector_runs] == [
        CollectionStatus.SUCCEEDED,
        CollectionStatus.FAILED,
    ]
    assert [event.event_type for event in repository.events] == [
        "evidence.collected",
        "investigation.initial_collection_completed",
    ]


def test_hotspot_created_resumes_existing_investigation_instead_of_restarting() -> None:
    repository = FakeInvestigationRepository()
    service = InvestigationOrchestrator(
        repository=repository,
        context_provider=FakeContextProvider(),
        collectors=[StaticCollector("traffic")],
    )

    first = service.handle_hotspot_created(hotspot_created_event(), now=NOW)
    resumed = service.handle_hotspot_created(hotspot_created_event(), now=NOW)

    assert resumed.id == first.id
    assert len(repository.investigations) == 1
    assert len(repository.evidence) == 2


def test_marks_waiting_for_evidence_when_no_enabled_collector_returns_evidence() -> None:
    repository = FakeInvestigationRepository()
    service = InvestigationOrchestrator(
        repository=repository,
        context_provider=FakeContextProvider(),
        collectors=[StaticCollector("traffic", enabled=False)],
    )

    investigation = service.handle_hotspot_created(hotspot_created_event(), now=NOW)

    assert investigation.status == InvestigationStatus.WAITING_FOR_EVIDENCE
    assert repository.evidence == []
    assert repository.events[-1].event_type == "investigation.initial_collection_completed"


def test_supports_additional_evidence_collection_on_existing_investigation() -> None:
    repository = FakeInvestigationRepository()
    service = InvestigationOrchestrator(
        repository=repository,
        context_provider=FakeContextProvider(),
        collectors=[StaticCollector("traffic"), StaticCollector("permits")],
    )
    investigation = service.handle_hotspot_created(hotspot_created_event(), now=NOW)

    updated = service.collect_additional_evidence(
        investigation.id,
        requested_collectors=["permits"],
        reason="next_best_evidence",
        now=NOW,
    )

    assert updated.id == investigation.id
    assert len(repository.evidence) == 3
    assert repository.events[-1].event_type == "investigation.initial_collection_completed"
    assert repository.events[-1].payload["reason"] == "next_best_evidence"
