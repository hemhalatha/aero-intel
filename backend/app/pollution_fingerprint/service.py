from datetime import UTC, datetime
from statistics import mean

from app.intelligence_contract.schemas import IntelligenceModuleContract
from app.investigations.evidence import EvidenceRecord, EvidenceSupportDirection

from .config import DEFAULT_FINGERPRINT_PATTERNS
from .schemas import (
    ExtractedFingerprintFeatures,
    FeatureKind,
    FingerprintFeatureValue,
    FingerprintPatternConfig,
    FingerprintPatternRule,
    FingerprintPatternScore,
    PollutionFingerprintResult,
)

FEATURE_ORDER = [
    "pm10_pm25_ratio",
    "no2_level",
    "co_level",
    "so2_level",
    "traffic_anomaly",
    "rush_hour_correlation",
    "construction_proximity",
    "industrial_proximity",
    "wind_alignment",
    "temporal_persistence",
    "biomass_burning_marker",
]


class PollutionFingerprintService:
    def __init__(self, patterns: list[FingerprintPatternConfig] | None = None) -> None:
        self.patterns = patterns or DEFAULT_FINGERPRINT_PATTERNS

    def generate(self, contract: IntelligenceModuleContract) -> PollutionFingerprintResult:
        features = self._extract_features(contract)
        scores = self._score_patterns(features)
        ranked = sorted(scores.values(), key=lambda item: item.score, reverse=True)
        for rank, score in enumerate(ranked, start=1):
            scores[score.source] = score.model_copy(update={"rank": rank})

        missing = [name for name in FEATURE_ORDER if not getattr(features, name).available]
        quality = self._data_quality_confidence(contract, features)
        notes = [
            "Pattern scores are fingerprint evidence only; final source attribution must be performed by the attribution module."
        ]
        if missing:
            notes.append("Some fingerprint features were unavailable and reduced confidence.")

        return PollutionFingerprintResult(
            generated_at=datetime.now(UTC),
            hotspot_id=contract.hotspot_id,
            investigation_id=contract.investigation_id,
            ward_code=contract.ward_code,
            station_code=contract.station_code,
            features=features,
            pattern_scores=scores,
            missing_fingerprint_features=missing,
            data_quality_confidence=quality,
            notes=notes,
        )

    def _extract_features(self, contract: IntelligenceModuleContract) -> ExtractedFingerprintFeatures:
        snapshot = contract.pollutant_snapshot
        pm10 = _pollutant(snapshot, "PM10")
        pm25 = _pollutant(snapshot, "PM2.5", "PM25")
        no2 = _pollutant(snapshot, "NO2")
        co = _pollutant(snapshot, "CO")
        so2 = _pollutant(snapshot, "SO2")
        traffic = _best_evidence(contract.evidence_bundle.all_evidence, "traffic")
        construction = _best_evidence(contract.evidence_bundle.all_evidence, "construction_land_use")
        industrial = _best_evidence(contract.evidence_bundle.all_evidence, "industrial")

        return ExtractedFingerprintFeatures(
            pm10_pm25_ratio=_feature(
                "pm10_pm25_ratio",
                FeatureKind.RATIO,
                round(pm10 / pm25, 2) if pm10 is not None and pm25 not in {None, 0} else None,
                None,
                "pollutant_snapshot",
            ),
            no2_level=_feature("no2_level", FeatureKind.CONCENTRATION, no2, "ug/m3", "pollutant_snapshot"),
            co_level=_feature("co_level", FeatureKind.CONCENTRATION, co, "mg/m3", "pollutant_snapshot"),
            so2_level=_feature("so2_level", FeatureKind.CONCENTRATION, so2, "ug/m3", "pollutant_snapshot"),
            traffic_anomaly=_feature(
                "traffic_anomaly",
                FeatureKind.PERCENT,
                _numeric_from_evidence(traffic, ["max_density_deviation_pct", "density_deviation_pct"]),
                "percent",
                "traffic_evidence",
                _evidence_quality(traffic),
            ),
            rush_hour_correlation=_feature(
                "rush_hour_correlation",
                FeatureKind.BOOLEAN,
                _bool_from_evidence(traffic, ["rush_hour_correlated"]),
                None,
                "traffic_evidence",
                _evidence_quality(traffic),
            ),
            construction_proximity=_feature(
                "construction_proximity",
                FeatureKind.DISTANCE_METERS,
                _numeric_from_evidence(construction, ["nearest_site_distance_meters", "distance_meters"]),
                "meters",
                "construction_evidence",
                _evidence_quality(construction),
            ),
            industrial_proximity=_feature(
                "industrial_proximity",
                FeatureKind.DISTANCE_METERS,
                _numeric_from_evidence(industrial, ["nearest_unit_distance_meters", "distance_meters"]),
                "meters",
                "industrial_evidence",
                _evidence_quality(industrial),
            ),
            wind_alignment=_feature(
                "wind_alignment",
                FeatureKind.BOOLEAN,
                _wind_alignment(contract.evidence_bundle.all_evidence),
                None,
                "evidence_bundle",
                _average_evidence_quality(contract.evidence_bundle.all_evidence),
            ),
            temporal_persistence=_feature(
                "temporal_persistence",
                FeatureKind.SCORE,
                _temporal_persistence(contract),
                "ratio",
                "historical_ward_aqi",
            ),
            biomass_burning_marker=_feature(
                "biomass_burning_marker",
                FeatureKind.BOOLEAN,
                _bool_from_evidence(_best_evidence(contract.evidence_bundle.all_evidence, "biomass"), ["burning_detected", "fire_detected"]),
                None,
                "biomass_or_waste_evidence",
            ),
        )

    def _score_patterns(self, features: ExtractedFingerprintFeatures) -> dict:
        scores = {}
        for pattern in self.patterns:
            total_weight = sum(rule.weight for rule in pattern.rules)
            weighted = 0.0
            matched: list[str] = []
            weak: list[str] = []
            breakdown: dict[str, float] = {}
            for rule in pattern.rules:
                feature = getattr(features, rule.feature_name)
                score = _score_rule(feature, rule)
                contribution = round((score * rule.weight) / total_weight, 3) if total_weight else 0
                weighted += score * rule.weight
                breakdown[rule.feature_name] = contribution
                if score >= 0.75:
                    matched.append(rule.feature_name)
                else:
                    weak.append(rule.feature_name)
            final = round(weighted / total_weight, 3) if total_weight else 0.0
            scores[pattern.source] = FingerprintPatternScore(
                source=pattern.source,
                score=final,
                rank=1,
                matched_features=matched,
                weak_or_missing_features=weak,
                contribution_breakdown=breakdown,
            )
        return scores

    @staticmethod
    def _data_quality_confidence(contract: IntelligenceModuleContract, features: ExtractedFingerprintFeatures) -> float:
        values = [contract.data_quality.hotspot_confidence]
        if contract.data_quality.evidence_quality_score is not None:
            values.append(contract.data_quality.evidence_quality_score)
        available = [getattr(features, name).data_quality_score for name in FEATURE_ORDER if getattr(features, name).available]
        if available:
            values.append(mean(available))
        coverage = sum(1 for name in FEATURE_ORDER if getattr(features, name).available) / len(FEATURE_ORDER)
        values.append(coverage)
        return round(max(min(mean(values), 1), 0), 2)


def _feature(
    name: str,
    kind: FeatureKind,
    value: float | bool | None,
    unit: str | None,
    source: str,
    quality: float = 1.0,
) -> FingerprintFeatureValue:
    return FingerprintFeatureValue(
        name=name,
        kind=kind,
        value=value,
        available=value is not None,
        unit=unit,
        source=source,
        data_quality_score=quality,
    )


def _pollutant(snapshot: dict[str, float], *names: str) -> float | None:
    normalized = {key.upper(): value for key, value in snapshot.items()}
    for name in names:
        value = normalized.get(name.upper())
        if value is not None:
            return float(value)
    return None


def _best_evidence(evidence: list[EvidenceRecord], source_type: str) -> EvidenceRecord | None:
    matches = [item for item in evidence if source_type in item.source_type]
    if not matches:
        return None
    return max(matches, key=lambda item: item.confidence * item.data_quality_score)


def _numeric_from_evidence(evidence: EvidenceRecord | None, keys: list[str]) -> float | None:
    if evidence is None:
        return None
    for key in keys:
        value = _deep_find(evidence.raw_details, key)
        if isinstance(value, (int, float)):
            return float(value)
    return None


def _bool_from_evidence(evidence: EvidenceRecord | None, keys: list[str]) -> bool | None:
    if evidence is None:
        return None
    for key in keys:
        value = _deep_find(evidence.raw_details, key)
        if isinstance(value, bool):
            return value
    if evidence.support_direction == EvidenceSupportDirection.SUPPORTS:
        return True
    if evidence.support_direction == EvidenceSupportDirection.CONTRADICTS:
        return False
    return None


def _deep_find(value, key: str):
    if isinstance(value, dict):
        if key in value:
            return value[key]
        for child in value.values():
            found = _deep_find(child, key)
            if found is not None:
                return found
    if isinstance(value, list):
        for child in value:
            found = _deep_find(child, key)
            if found is not None:
                return found
    return None


def _wind_alignment(evidence: list[EvidenceRecord]) -> bool | None:
    values = []
    for item in evidence:
        for key in ["wind_transport_supported", "upwind_supported", "transport_supported"]:
            found = _deep_find(item.raw_details, key)
            if isinstance(found, bool):
                values.append(found)
    if not values:
        return None
    return any(values)


def _temporal_persistence(contract: IntelligenceModuleContract) -> float | None:
    readings = [item for item in contract.historical_ward_aqi if item.data_quality_status == "valid"]
    if len(readings) < 2:
        return None
    persistent = sum(1 for item in readings if item.value >= 150)
    return round(persistent / len(readings), 2)


def _evidence_quality(evidence: EvidenceRecord | None) -> float:
    return evidence.data_quality_score if evidence else 0.0


def _average_evidence_quality(evidence: list[EvidenceRecord]) -> float:
    return round(mean([item.data_quality_score for item in evidence]), 3) if evidence else 0.0


def _score_rule(feature: FingerprintFeatureValue, rule: FingerprintPatternRule) -> float:
    if not feature.available:
        return rule.missing_penalty
    value = feature.value
    if isinstance(value, bool):
        return 1.0 if rule.expected_bool is None or value == rule.expected_bool else 0.0
    if not isinstance(value, (int, float)):
        return 0.0
    score = 1.0
    if rule.min_value is not None and value < rule.min_value:
        score = min(score, max(value / rule.min_value, 0)) if rule.min_value > 0 else 0.0
    if rule.max_value is not None and value > rule.max_value:
        score = min(score, max(rule.max_value / value, 0)) if value > 0 else 0.0
    return round(score, 3)
