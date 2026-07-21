from datetime import UTC, datetime
from statistics import mean

from app.investigations.schemas import AdditionalEvidenceRequest
from app.schemas import SourceRanking

from .schemas import (
    NextBestEvidenceRequest,
    NextBestEvidenceType,
    UncertaintyAssessmentInput,
    UncertaintyAssessmentResult,
    UncertaintyLevel,
    UncertaintySignal,
    UncertaintySignalSeverity,
)

SOURCE_ALIASES = {
    "vehicular pollution": "Vehicular Pollution",
    "vehicular emissions": "Vehicular Pollution",
    "traffic": "Vehicular Pollution",
    "construction dust": "Construction Dust",
    "construction": "Construction Dust",
    "industrial emission": "Industrial Emission",
    "industrial emissions": "Industrial Emission",
    "industrial": "Industrial Emission",
    "road dust": "Road Dust",
    "biomass burning": "Biomass Burning",
    "biomass or waste burning": "Biomass Burning",
    "waste burning": "Biomass Burning",
}

COLLECTORS_BY_SOURCE = {
    "Vehicular Pollution": ["traffic"],
    "Construction Dust": ["construction_land_use"],
    "Industrial Emission": ["industrial"],
    "Road Dust": ["traffic"],
    "Biomass Burning": ["biomass"],
}


class UncertaintyEngine:
    def __init__(self, next_best_engine: "NextBestEvidenceEngine | None" = None) -> None:
        self.next_best_engine = next_best_engine or NextBestEvidenceEngine()

    def evaluate(self, data: UncertaintyAssessmentInput) -> UncertaintyAssessmentResult:
        rankings = _normalized_rankings(data.attribution_rankings)
        top_two = rankings[:2]
        score_gap = round(abs(top_two[0].score - top_two[1].score), 2) if len(top_two) >= 2 else None
        leading_sources = [item.source for item in top_two]
        missing_collectors = sorted(set(data.expected_collectors) - set(data.completed_collectors))
        missing_features = sorted(set(data.fingerprint.missing_fingerprint_features))
        signals = self._signals(data, score_gap, missing_collectors, missing_features)
        level = self._level(signals)
        confidence = self._quality_confidence(data)
        next_request = None
        if level in {UncertaintyLevel.MEDIUM, UncertaintyLevel.HIGH}:
            next_request = self.next_best_engine.recommend(data, leading_sources, missing_collectors, missing_features, level)
        return UncertaintyAssessmentResult(
            generated_at=datetime.now(UTC),
            hotspot_id=data.hotspot_id,
            investigation_id=data.investigation_id,
            level=level,
            score_gap=score_gap,
            leading_sources=leading_sources,
            signals=signals,
            missing_collectors=missing_collectors,
            missing_fingerprint_features=missing_features,
            data_quality_confidence=confidence,
            next_best_evidence_request=next_request,
        )

    @staticmethod
    def _signals(
        data: UncertaintyAssessmentInput,
        score_gap: float | None,
        missing_collectors: list[str],
        missing_features: list[str],
    ) -> list[UncertaintySignal]:
        signals = []
        if score_gap is None:
            signals.append(_signal("score_gap", UncertaintySignalSeverity.HIGH, None, "Fewer than two attribution candidates were available."))
        elif score_gap < 8:
            signals.append(_signal("score_gap", UncertaintySignalSeverity.HIGH, score_gap, "Top attribution scores are very close."))
        elif score_gap < 18:
            signals.append(_signal("score_gap", UncertaintySignalSeverity.MEDIUM, score_gap, "Top attribution scores are moderately close."))
        else:
            signals.append(_signal("score_gap", UncertaintySignalSeverity.LOW, score_gap, "Top attribution scores are well separated."))

        if data.supporting_evidence_count < 2:
            signals.append(_signal("supporting_evidence", UncertaintySignalSeverity.HIGH, data.supporting_evidence_count, "Too few supporting evidence items are available."))
        elif data.supporting_evidence_count < 4:
            signals.append(_signal("supporting_evidence", UncertaintySignalSeverity.MEDIUM, data.supporting_evidence_count, "Supporting evidence is present but limited."))
        else:
            signals.append(_signal("supporting_evidence", UncertaintySignalSeverity.LOW, data.supporting_evidence_count, "Supporting evidence quantity is adequate."))

        if data.contradictory_evidence_count > 1:
            signals.append(_signal("contradictory_evidence", UncertaintySignalSeverity.HIGH, data.contradictory_evidence_count, "Multiple contradictory evidence items were found."))
        elif data.contradictory_evidence_count == 1:
            signals.append(_signal("contradictory_evidence", UncertaintySignalSeverity.MEDIUM, data.contradictory_evidence_count, "One contradictory evidence item was found."))
        else:
            signals.append(_signal("contradictory_evidence", UncertaintySignalSeverity.LOW, 0, "No contradictory evidence was found."))

        quality = data.evidence_quality_score if data.evidence_quality_score is not None else data.fingerprint.data_quality_confidence
        if quality < 0.6:
            signals.append(_signal("evidence_quality", UncertaintySignalSeverity.HIGH, round(quality, 2), "Evidence quality is low."))
        elif quality < 0.8:
            signals.append(_signal("evidence_quality", UncertaintySignalSeverity.MEDIUM, round(quality, 2), "Evidence quality is mixed."))
        else:
            signals.append(_signal("evidence_quality", UncertaintySignalSeverity.LOW, round(quality, 2), "Evidence quality is acceptable."))

        if len(missing_collectors) > 2:
            signals.append(_signal("missing_collectors", UncertaintySignalSeverity.HIGH, missing_collectors, "Multiple expected evidence collectors are missing."))
        elif missing_collectors:
            signals.append(_signal("missing_collectors", UncertaintySignalSeverity.MEDIUM, missing_collectors, "One expected evidence collector is missing."))
        else:
            signals.append(_signal("missing_collectors", UncertaintySignalSeverity.LOW, [], "All expected collectors completed."))

        if len(missing_features) >= 4:
            signals.append(_signal("missing_fingerprint_features", UncertaintySignalSeverity.HIGH, missing_features, "Many fingerprint features are missing."))
        elif len(missing_features) >= 1:
            signals.append(_signal("missing_fingerprint_features", UncertaintySignalSeverity.MEDIUM, missing_features, "Some fingerprint features are missing."))
        else:
            signals.append(_signal("missing_fingerprint_features", UncertaintySignalSeverity.LOW, [], "Fingerprint features are complete."))
        return signals

    @staticmethod
    def _level(signals: list[UncertaintySignal]) -> UncertaintyLevel:
        points = sum(2 if signal.severity == UncertaintySignalSeverity.HIGH else 1 if signal.severity == UncertaintySignalSeverity.MEDIUM else 0 for signal in signals)
        if points >= 6 or sum(1 for signal in signals if signal.severity == UncertaintySignalSeverity.HIGH) >= 3:
            return UncertaintyLevel.HIGH
        if points >= 2:
            return UncertaintyLevel.MEDIUM
        return UncertaintyLevel.LOW

    @staticmethod
    def _quality_confidence(data: UncertaintyAssessmentInput) -> float:
        values = [data.fingerprint.data_quality_confidence]
        if data.evidence_quality_score is not None:
            values.append(data.evidence_quality_score)
        coverage = len(data.completed_collectors) / len(data.expected_collectors) if data.expected_collectors else 1
        values.append(coverage)
        return round(max(min(mean(values), 1), 0), 2)


class NextBestEvidenceEngine:
    def recommend(
        self,
        data: UncertaintyAssessmentInput,
        leading_sources: list[str],
        missing_collectors: list[str],
        missing_features: list[str],
        level: UncertaintyLevel,
    ) -> NextBestEvidenceRequest:
        source_pair = set(leading_sources[:2])
        if source_pair == {"Vehicular Pollution", "Construction Dust"} or "pm10_pm25_ratio" in missing_features:
            return _request(
                data.investigation_id,
                NextBestEvidenceType.PM_RATIO_FINGERPRINT_ANALYSIS,
                ["construction_land_use"],
                "pm10_pm25_fingerprint_analysis",
                leading_sources,
                "Compare PM10/PM2.5 ratio and nearby construction activity against traffic signals.",
                level,
                {"missing_features": missing_features},
            )
        if source_pair == {"Industrial Emission", "Vehicular Pollution"} or "wind_alignment" in missing_features:
            return _request(
                data.investigation_id,
                NextBestEvidenceType.WIND_SOURCE_ALIGNMENT_ANALYSIS,
                ["industrial", "traffic"],
                "wind_source_alignment_analysis",
                leading_sources,
                "Check whether wind direction aligns emissions transport from candidate sources to the hotspot.",
                level,
                {"missing_features": missing_features},
            )
        if missing_collectors:
            return _request(
                data.investigation_id,
                NextBestEvidenceType.MISSING_COLLECTOR_CHECK,
                missing_collectors,
                "missing_collector_check",
                leading_sources,
                "Run missing collectors before comparing source hypotheses.",
                level,
                {"missing_collectors": missing_collectors},
            )
        if "Biomass Burning" in source_pair or "biomass_burning_marker" in missing_features:
            return _request(
                data.investigation_id,
                NextBestEvidenceType.BIOMASS_BURNING_MARKER_CHECK,
                ["biomass"],
                "biomass_burning_marker_check",
                leading_sources,
                "Look for fire, waste-burning, or fine particulate combustion markers.",
                level,
                {"missing_features": missing_features},
            )
        collectors = sorted({collector for source in leading_sources for collector in COLLECTORS_BY_SOURCE.get(source, [])}) or ["traffic", "construction_land_use", "industrial"]
        return _request(
            data.investigation_id,
            NextBestEvidenceType.TRAFFIC_BASELINE_RECHECK,
            collectors,
            "source_disambiguation_recheck",
            leading_sources,
            "Re-run source-specific checks for the leading candidate sources.",
            level,
            {},
        )


def _request(
    investigation_id: int,
    evidence_type: NextBestEvidenceType,
    collectors: list[str],
    reason: str,
    sources: list[str],
    expected_signal: str,
    level: UncertaintyLevel,
    metadata: dict,
) -> NextBestEvidenceRequest:
    unique_collectors = sorted(set(collectors))
    orchestrator_reason = f"next_best_evidence:{reason}"
    return NextBestEvidenceRequest(
        investigation_id=investigation_id,
        evidence_type=evidence_type,
        requested_collectors=unique_collectors,
        reason=orchestrator_reason,
        discriminator_sources=sources[:2],
        expected_signal=expected_signal,
        priority=level,
        orchestrator_payload=AdditionalEvidenceRequest(
            requested_collectors=unique_collectors,
            reason=orchestrator_reason,
        ),
        metadata=metadata,
    )


def _normalized_rankings(rankings: list[SourceRanking]) -> list[SourceRanking]:
    normalized = [ranking.model_copy(update={"source": _normalize_source(ranking.source)}) for ranking in rankings]
    return sorted(normalized, key=lambda item: item.score, reverse=True)


def _normalize_source(source: str) -> str:
    return SOURCE_ALIASES.get(source.strip().lower(), source)


def _signal(name: str, severity: UncertaintySignalSeverity, value, explanation: str) -> UncertaintySignal:
    return UncertaintySignal(name=name, severity=severity, value=value, explanation=explanation)
