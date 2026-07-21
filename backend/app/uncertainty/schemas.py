from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.investigations.schemas import AdditionalEvidenceRequest
from app.pollution_fingerprint.schemas import PollutionFingerprintResult
from app.schemas import SourceRanking


class UncertaintyLevel(StrEnum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class UncertaintySignalSeverity(StrEnum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class NextBestEvidenceType(StrEnum):
    PM_RATIO_FINGERPRINT_ANALYSIS = "pm10_pm25_fingerprint_analysis"
    WIND_SOURCE_ALIGNMENT_ANALYSIS = "wind_source_alignment_analysis"
    CONSTRUCTION_ACTIVITY_RECHECK = "construction_activity_recheck"
    INDUSTRIAL_COMPLIANCE_RECHECK = "industrial_compliance_recheck"
    TRAFFIC_BASELINE_RECHECK = "traffic_baseline_recheck"
    MISSING_COLLECTOR_CHECK = "missing_collector_check"
    BIOMASS_BURNING_MARKER_CHECK = "biomass_burning_marker_check"


class EvidenceCompletenessSummary(BaseModel):
    supporting_evidence_count: int = Field(ge=0)
    contradictory_evidence_count: int = Field(ge=0)
    evidence_quality_score: float | None = Field(default=None, ge=0, le=1)
    expected_collectors: list[str] = Field(default_factory=list)
    completed_collectors: list[str] = Field(default_factory=list)


class UncertaintyAssessmentInput(EvidenceCompletenessSummary):
    hotspot_id: int = Field(gt=0)
    investigation_id: int = Field(gt=0)
    attribution_rankings: list[SourceRanking]
    fingerprint: PollutionFingerprintResult


class UncertaintySignal(BaseModel):
    name: str
    severity: UncertaintySignalSeverity
    value: float | int | str | list[str] | None = None
    explanation: str


class NextBestEvidenceRequest(BaseModel):
    investigation_id: int
    evidence_type: NextBestEvidenceType
    requested_collectors: list[str]
    reason: str
    discriminator_sources: list[str]
    expected_signal: str
    priority: UncertaintyLevel
    orchestrator_payload: AdditionalEvidenceRequest
    metadata: dict[str, Any] = Field(default_factory=dict)


class UncertaintyAssessmentResult(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "hotspot_id": 101,
                "investigation_id": 17,
                "level": "HIGH",
                "score_gap": 4.0,
                "leading_sources": ["Vehicular Pollution", "Construction Dust"],
                "next_best_evidence_request": {
                    "evidence_type": "pm10_pm25_fingerprint_analysis",
                    "requested_collectors": ["construction_land_use"],
                },
            }
        }
    )

    contract_version: str = "v1"
    generated_at: datetime
    hotspot_id: int
    investigation_id: int
    level: UncertaintyLevel
    score_gap: float | None = None
    leading_sources: list[str] = Field(default_factory=list)
    signals: list[UncertaintySignal] = Field(default_factory=list)
    missing_collectors: list[str] = Field(default_factory=list)
    missing_fingerprint_features: list[str] = Field(default_factory=list)
    data_quality_confidence: float = Field(ge=0, le=1)
    next_best_evidence_request: NextBestEvidenceRequest | None = None
