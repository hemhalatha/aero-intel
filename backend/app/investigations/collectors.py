from datetime import UTC, datetime
from typing import Any, Literal, Protocol

from pydantic import BaseModel, Field

SupportDirection = Literal["SUPPORTS", "CONTRADICTS", "NEUTRAL"]


class CollectorResult(BaseModel):
    evidence_type: str
    source: str
    payload: dict[str, Any]
    observed_at: datetime
    confidence: float = Field(ge=0, le=1)
    source_type: str = "controlled_demo"
    detected: bool = True
    support_direction: SupportDirection = "NEUTRAL"


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
                source_type="controlled_demo",
                detected=True,
                support_direction="NEUTRAL",
                payload={**self.payload, "ward_code": investigation.ward_code},
                observed_at=observed_at,
                confidence=0.7,
            )
        ]


def default_collectors() -> list[EvidenceCollector]:
    from .construction import ConstructionEvidenceCollector
    from .traffic import TrafficEvidenceCollector

    return [
        TrafficEvidenceCollector(),
        ConstructionEvidenceCollector(),
        SeededEvidenceCollector(
            name="industrial_demo",
            evidence_type="industrial.activity",
            payload={"reported_activity_level": "moderate", "provenance": "controlled_demo"},
        ),
    ]
