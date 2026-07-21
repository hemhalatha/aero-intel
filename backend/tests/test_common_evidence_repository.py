from datetime import UTC, datetime, timedelta

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.investigations.evidence import (
    EvidenceCreate,
    EvidenceRepository,
    EvidenceService,
    EvidenceSupportDirection,
    EvidenceUpdate,
)
from app.investigations.models import EvidenceCollectionRun, EvidenceItem, EvidenceItemVersion, Investigation, InvestigationEvent


NOW = datetime(2025, 1, 15, 12, tzinfo=UTC)


def make_service():
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(
        engine,
        tables=[
            Investigation.__table__,
            EvidenceCollectionRun.__table__,
            EvidenceItem.__table__,
            EvidenceItemVersion.__table__,
            InvestigationEvent.__table__,
        ],
    )
    session = sessionmaker(bind=engine)()
    repository = EvidenceRepository(session)
    return EvidenceService(repository), session


def evidence(
    investigation_id: int = 1,
    source_type: str = "traffic",
    evidence_type: str = "traffic.density_anomaly",
    support_direction: EvidenceSupportDirection = EvidenceSupportDirection.SUPPORTS,
    checked_at: datetime = NOW,
) -> EvidenceCreate:
    return EvidenceCreate(
        investigation_id=investigation_id,
        source_type=source_type,
        evidence_type=evidence_type,
        detected=support_direction != EvidenceSupportDirection.CONTRADICTS,
        confidence=0.81,
        support_direction=support_direction,
        raw_details={"deviation_pct": 42.5, "source_type": source_type},
        data_quality_score=0.9,
        collector_name=f"{source_type}_collector",
        checked_at=checked_at,
    )


def test_retrieves_and_filters_standardized_evidence() -> None:
    service, _ = make_service()
    service.add_followup_evidence(evidence(source_type="traffic", evidence_type="traffic.density_anomaly"))
    service.add_followup_evidence(
        evidence(
            source_type="industrial",
            evidence_type="industrial.activity_signal",
            support_direction=EvidenceSupportDirection.CONTRADICTS,
            checked_at=NOW + timedelta(minutes=5),
        )
    )
    service.add_followup_evidence(
        evidence(
            source_type="construction_land_use",
            evidence_type="construction.land_use_activity",
            support_direction=EvidenceSupportDirection.NEUTRAL,
            checked_at=NOW + timedelta(minutes=10),
        )
    )

    all_evidence = service.get_investigation_evidence(1)
    traffic = service.get_investigation_evidence(1, source_type="traffic")
    construction = service.get_evidence_by_type(1, "construction.land_use_activity")
    supporting = service.get_supporting_evidence(1)
    contradictory = service.get_contradictory_evidence(1)

    assert [item.source_type for item in all_evidence] == ["traffic", "industrial", "construction_land_use"]
    assert [item.evidence_type for item in traffic] == ["traffic.density_anomaly"]
    assert [item.source_type for item in construction] == ["construction_land_use"]
    assert [item.support_direction for item in supporting] == [EvidenceSupportDirection.SUPPORTS]
    assert [item.source_type for item in contradictory] == ["industrial"]


def test_add_followup_evidence_returns_common_contract() -> None:
    service, _ = make_service()

    saved = service.add_followup_evidence(evidence())

    assert saved.evidence_id == 1
    assert saved.investigation_id == 1
    assert saved.source_type == "traffic"
    assert saved.detected is True
    assert saved.confidence == 0.81
    assert saved.data_quality_score == 0.9
    assert saved.collector_name == "traffic_collector"
    assert saved.checked_at == NOW
    assert saved.raw_details["deviation_pct"] == 42.5


def test_update_preserves_previous_evidence_version() -> None:
    service, _ = make_service()
    saved = service.add_followup_evidence(evidence())

    updated = service.update_evidence(
        saved.evidence_id,
        EvidenceUpdate(
            confidence=0.62,
            support_direction=EvidenceSupportDirection.NEUTRAL,
            raw_details={"deviation_pct": 12.0, "note": "follow-up weaker"},
            data_quality_score=0.74,
            checked_at=NOW + timedelta(hours=1),
        ),
        reason="next_best_evidence_followup",
    )
    versions = service.get_evidence_versions(saved.evidence_id)

    assert updated.confidence == 0.62
    assert updated.support_direction == EvidenceSupportDirection.NEUTRAL
    assert updated.raw_details["note"] == "follow-up weaker"
    assert len(versions) == 1
    assert versions[0].version_number == 1
    assert versions[0].confidence == 0.81
    assert versions[0].support_direction == EvidenceSupportDirection.SUPPORTS
    assert versions[0].change_reason == "next_best_evidence_followup"