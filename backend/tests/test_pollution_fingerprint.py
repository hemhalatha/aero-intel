from datetime import UTC, datetime

from app.environmental_data.time_series_schemas import PollutantReading
from app.intelligence_contract.schemas import (
    DataQualityContract,
    IntelligenceModuleContract,
    StandardizedEvidenceBundle,
)
from app.investigations.evidence import EvidenceRecord, EvidenceSupportDirection
from app.pollution_fingerprint.schemas import FingerprintSource
from app.pollution_fingerprint.service import PollutionFingerprintService

NOW = datetime(2025, 1, 15, 18, tzinfo=UTC)


def evidence(source_type, support_direction, raw_details, confidence=0.82, quality=0.9):
    return EvidenceRecord(
        evidence_id=len(str(source_type)),
        investigation_id=17,
        source_type=source_type,
        evidence_type=f"{source_type}.signal",
        detected=support_direction != EvidenceSupportDirection.CONTRADICTS,
        confidence=confidence,
        support_direction=support_direction,
        raw_details=raw_details,
        data_quality_score=quality,
        collector_name=f"{source_type}_collector",
        checked_at=NOW,
        source=f"{source_type}_collector",
        collected_at=NOW,
    )


def historical_aqi(values):
    return [
        PollutantReading(
            station_code="BLR-SB-AQ",
            station_name="Silk Board",
            ward_code="BLR-W-014",
            observed_at=NOW,
            pollutant="AQI",
            value=value,
            unit="index",
            data_quality_status="valid",
        )
        for value in values
    ]


def contract(snapshot, evidence_items, historical=None, quality=None):
    all_evidence = evidence_items
    supporting = [item for item in all_evidence if item.support_direction == EvidenceSupportDirection.SUPPORTS]
    contradictory = [item for item in all_evidence if item.support_direction == EvidenceSupportDirection.CONTRADICTS]
    neutral = [item for item in all_evidence if item.support_direction == EvidenceSupportDirection.NEUTRAL]
    return IntelligenceModuleContract(
        generated_at=NOW,
        hotspot_id=101,
        investigation_id=17,
        ward_code="BLR-W-014",
        station_code="BLR-SB-AQ",
        current_aqi=snapshot.get("AQI", 220),
        pollutant_snapshot=snapshot,
        historical_ward_aqi=historical or historical_aqi([162, 188, 215]),
        data_quality=quality or DataQualityContract(
            hotspot_confidence=0.91,
            latest_station_quality="valid",
            evidence_quality_score=0.86,
            wind_quality="valid",
        ),
        evidence_bundle=StandardizedEvidenceBundle(
            investigation_id=17,
            all_evidence=all_evidence,
            supporting_evidence=supporting,
            contradictory_evidence=contradictory,
            neutral_evidence=neutral,
        ),
    )


def test_generates_vehicular_fingerprint_without_final_attribution() -> None:
    source = contract(
        {"AQI": 232, "PM2.5": 78, "PM10": 136, "NO2": 118, "CO": 4.4, "SO2": 16},
        [
            evidence(
                "traffic",
                EvidenceSupportDirection.SUPPORTS,
                {
                    "max_density_deviation_pct": 76,
                    "rush_hour_correlated": True,
                    "nearest_road_distance_meters": 220,
                    "wind_context": {"transport_supported": False},
                },
            ),
            evidence("construction_land_use", EvidenceSupportDirection.CONTRADICTS, {"nearest_site_distance_meters": None}),
            evidence("industrial", EvidenceSupportDirection.CONTRADICTS, {"nearest_unit_distance_meters": None}),
        ],
    )

    result = PollutionFingerprintService().generate(source)

    assert result.hotspot_id == 101
    assert result.investigation_id == 17
    assert result.is_final_attribution is False
    assert result.features.pm10_pm25_ratio.value == 1.74
    assert result.features.no2_level.value == 118
    assert result.features.traffic_anomaly.value == 76
    assert result.features.rush_hour_correlation.value is True
    assert result.pattern_scores[FingerprintSource.VEHICULAR_EMISSIONS].score >= 0.8
    assert result.pattern_scores[FingerprintSource.VEHICULAR_EMISSIONS].rank == 1
    assert result.pattern_scores[FingerprintSource.CONSTRUCTION_DUST].score < result.pattern_scores[FingerprintSource.VEHICULAR_EMISSIONS].score
    assert "biomass_burning_marker" in result.missing_fingerprint_features
    assert result.data_quality_confidence == 0.86


def test_generates_construction_and_industrial_pattern_scores_from_structured_evidence() -> None:
    construction = contract(
        {"AQI": 248, "PM2.5": 96, "PM10": 242, "NO2": 44, "CO": 1.1, "SO2": 12},
        [
            evidence("traffic", EvidenceSupportDirection.CONTRADICTS, {"max_density_deviation_pct": 0, "rush_hour_correlated": False}),
            evidence(
                "construction_land_use",
                EvidenceSupportDirection.SUPPORTS,
                {"nearest_site_distance_meters": 260, "wind_transport_supported": True},
            ),
        ],
    )
    industrial = contract(
        {"AQI": 256, "PM2.5": 72, "PM10": 128, "NO2": 112, "CO": 4.2, "SO2": 126},
        [
            evidence("industrial", EvidenceSupportDirection.SUPPORTS, {"nearest_unit_distance_meters": 320, "upwind_supported": True}),
            evidence("traffic", EvidenceSupportDirection.NEUTRAL, {"max_density_deviation_pct": 12, "rush_hour_correlated": False}),
        ],
    )

    construction_result = PollutionFingerprintService().generate(construction)
    industrial_result = PollutionFingerprintService().generate(industrial)

    assert construction_result.pattern_scores[FingerprintSource.CONSTRUCTION_DUST].rank == 1
    assert construction_result.features.construction_proximity.value == 260
    assert construction_result.features.wind_alignment.value is True
    assert industrial_result.pattern_scores[FingerprintSource.INDUSTRIAL_EMISSIONS].rank == 1
    assert industrial_result.features.industrial_proximity.value == 320
    assert industrial_result.features.so2_level.value == 126


def test_reports_missing_features_and_lower_quality_when_contract_is_sparse() -> None:
    sparse = contract(
        {"AQI": 180, "PM2.5": 64},
        [],
        historical=[],
        quality=DataQualityContract(hotspot_confidence=0.55, latest_station_quality="incomplete"),
    )

    result = PollutionFingerprintService().generate(sparse)

    assert result.features.pm10_pm25_ratio.available is False
    assert "pm10_pm25_ratio" in result.missing_fingerprint_features
    assert "traffic_anomaly" in result.missing_fingerprint_features
    assert result.data_quality_confidence < 0.6
    assert all(score.score <= 0.5 for score in result.pattern_scores.values())
