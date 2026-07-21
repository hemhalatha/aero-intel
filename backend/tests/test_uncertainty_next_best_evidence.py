from datetime import UTC, datetime

from app.pollution_fingerprint.schemas import (
    ExtractedFingerprintFeatures,
    FeatureKind,
    FingerprintFeatureValue,
    FingerprintPatternScore,
    FingerprintSource,
    PollutionFingerprintResult,
)
from app.schemas import EvidenceFactor, SourceRanking
from app.uncertainty.schemas import NextBestEvidenceType, UncertaintyAssessmentInput, UncertaintyLevel
from app.uncertainty.service import UncertaintyEngine

NOW = datetime(2025, 1, 15, 18, tzinfo=UTC)


def feature(name, value=True, available=True):
    return FingerprintFeatureValue(
        name=name,
        kind=FeatureKind.BOOLEAN if isinstance(value, bool) else FeatureKind.SCORE,
        value=value if available else None,
        available=available,
        source="test",
    )


def fingerprint(missing=None, quality=0.9):
    missing = missing or []
    features = ExtractedFingerprintFeatures(
        pm10_pm25_ratio=feature("pm10_pm25_ratio", 2.4, "pm10_pm25_ratio" not in missing),
        no2_level=feature("no2_level", 118, "no2_level" not in missing),
        co_level=feature("co_level", 4.2, "co_level" not in missing),
        so2_level=feature("so2_level", 18, "so2_level" not in missing),
        traffic_anomaly=feature("traffic_anomaly", 72, "traffic_anomaly" not in missing),
        rush_hour_correlation=feature("rush_hour_correlation", True, "rush_hour_correlation" not in missing),
        construction_proximity=feature("construction_proximity", 260, "construction_proximity" not in missing),
        industrial_proximity=feature("industrial_proximity", 1200, "industrial_proximity" not in missing),
        wind_alignment=feature("wind_alignment", True, "wind_alignment" not in missing),
        temporal_persistence=feature("temporal_persistence", 0.8, "temporal_persistence" not in missing),
        biomass_burning_marker=feature("biomass_burning_marker", False, "biomass_burning_marker" not in missing),
    )
    scores = {
        FingerprintSource.VEHICULAR_EMISSIONS: FingerprintPatternScore(source=FingerprintSource.VEHICULAR_EMISSIONS, score=0.84, rank=1),
        FingerprintSource.CONSTRUCTION_DUST: FingerprintPatternScore(source=FingerprintSource.CONSTRUCTION_DUST, score=0.42, rank=2),
        FingerprintSource.INDUSTRIAL_EMISSIONS: FingerprintPatternScore(source=FingerprintSource.INDUSTRIAL_EMISSIONS, score=0.18, rank=3),
    }
    return PollutionFingerprintResult(
        generated_at=NOW,
        hotspot_id=101,
        investigation_id=17,
        current_aqi=0,
        features=features,
        pattern_scores=scores,
        missing_fingerprint_features=missing,
        data_quality_confidence=quality,
    )


def ranking(source, score):
    return SourceRanking(source=source, score=score, evidence=[EvidenceFactor(label="test", contribution=score)])


def assessment_input(rankings, missing=None, supporting=4, contradictory=0, quality=0.9, completed=None, expected=None):
    return UncertaintyAssessmentInput(
        hotspot_id=101,
        investigation_id=17,
        attribution_rankings=rankings,
        fingerprint=fingerprint(missing=missing, quality=quality),
        supporting_evidence_count=supporting,
        contradictory_evidence_count=contradictory,
        evidence_quality_score=quality,
        expected_collectors=expected or ["traffic", "construction_land_use", "industrial"],
        completed_collectors=completed or ["traffic", "construction_land_use", "industrial"],
    )


def test_low_uncertainty_when_scores_are_separated_and_evidence_is_complete() -> None:
    result = UncertaintyEngine().evaluate(
        assessment_input([
            ranking("Vehicular Pollution", 72),
            ranking("Construction Dust", 18),
            ranking("Industrial Emission", 10),
        ])
    )

    assert result.level == UncertaintyLevel.LOW
    assert result.next_best_evidence_request is None
    assert result.score_gap == 54


def test_high_uncertainty_requests_pm_ratio_when_traffic_and_construction_are_close() -> None:
    result = UncertaintyEngine().evaluate(
        assessment_input(
            [ranking("Vehicular Pollution", 43), ranking("Construction Dust", 39), ranking("Industrial Emission", 18)],
            missing=["pm10_pm25_ratio", "construction_proximity", "biomass_burning_marker"],
            supporting=1,
            contradictory=2,
            quality=0.58,
            completed=["traffic"],
        )
    )

    assert result.level == UncertaintyLevel.HIGH
    assert result.next_best_evidence_request is not None
    assert result.next_best_evidence_request.evidence_type == NextBestEvidenceType.PM_RATIO_FINGERPRINT_ANALYSIS
    assert result.next_best_evidence_request.requested_collectors == ["construction_land_use"]
    assert result.next_best_evidence_request.orchestrator_payload.reason == "next_best_evidence:pm10_pm25_fingerprint_analysis"


def test_medium_uncertainty_requests_wind_alignment_for_industrial_and_traffic_tie() -> None:
    result = UncertaintyEngine().evaluate(
        assessment_input(
            [ranking("Industrial Emission", 46), ranking("Vehicular Pollution", 34), ranking("Construction Dust", 20)],
            missing=["wind_alignment"],
            supporting=3,
            contradictory=1,
            quality=0.76,
        )
    )

    assert result.level == UncertaintyLevel.MEDIUM
    assert result.next_best_evidence_request.evidence_type == NextBestEvidenceType.WIND_SOURCE_ALIGNMENT_ANALYSIS
    assert result.next_best_evidence_request.requested_collectors == ["industrial", "traffic"]
    assert set(result.next_best_evidence_request.discriminator_sources) == {"Industrial Emission", "Vehicular Pollution"}


def test_missing_collector_rule_falls_back_to_requested_collector_check() -> None:
    result = UncertaintyEngine().evaluate(
        assessment_input(
            [ranking("Biomass Burning", 36), ranking("Road Dust", 31), ranking("Construction Dust", 20)],
            missing=["biomass_burning_marker"],
            supporting=2,
            contradictory=0,
            quality=0.82,
            completed=["traffic", "construction_land_use"],
            expected=["traffic", "construction_land_use", "industrial", "biomass"],
        )
    )

    assert result.level == UncertaintyLevel.MEDIUM
    assert result.next_best_evidence_request.evidence_type == NextBestEvidenceType.MISSING_COLLECTOR_CHECK
    assert result.next_best_evidence_request.requested_collectors == ["biomass", "industrial"]
