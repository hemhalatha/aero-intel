from datetime import UTC, datetime
from typing import Any, Protocol

from pydantic import BaseModel, Field


class CollectorResult(BaseModel):
    evidence_type: str
    source: str
    payload: dict[str, Any]
    observed_at: datetime
    confidence: float = Field(ge=0, le=1)


class EvidenceCollector(Protocol):
    name: str
    enabled: bool

    def collect(self, investigation, context: dict[str, Any]) -> list[CollectorResult]:
        ...


class SeededEvidenceCollector:
    def __init__(self, name: str, evidence_type: str, payload: dict[str, Any], enabled: bool = True) -> None:
        self.name = name
        self.evidence_type = evidence_type
        self.payload = payload
        self.enabled = enabled

    def collect(self, investigation, context: dict[str, Any]) -> list[CollectorResult]:
        observed_at = investigation.created_at or investigation.last_collection_completed_at
        if observed_at is None:
            observed_at = context.get("observed_at") or datetime.now(UTC)
        return [
            CollectorResult(
                evidence_type=self.evidence_type,
                source=self.name,
                payload={**self.payload, "ward_code": investigation.ward_code},
                observed_at=observed_at,
                confidence=0.7,
            )
        ]


def default_collectors() -> list[EvidenceCollector]:
    return [
        SeededEvidenceCollector(
            name="traffic_demo",
            evidence_type="traffic.anomaly",
            payload={"traffic_index": 0.74, "provenance": "controlled_demo"},
        ),
        SeededEvidenceCollector(
            name="construction_demo",
            evidence_type="construction.activity",
            payload={"active_permits_nearby": 2, "provenance": "controlled_demo"},
        ),
        SeededEvidenceCollector(
            name="industrial_demo",
            evidence_type="industrial.activity",
            payload={"reported_activity_level": "moderate", "provenance": "controlled_demo"},
        ),
    ]
