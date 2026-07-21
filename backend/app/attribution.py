from dataclasses import dataclass

from .schemas import EvidenceBundle, EvidenceFactor, SourceRanking


@dataclass(frozen=True)
class SourceRule:
    name: str
    signal_weights: dict[str, float]
    history_field: str


RULES = (
    SourceRule("Construction Dust", {"construction": 0.60, "satellite": 0.18, "wind": 0.10, "history": 0.12}, "construction_match"),
    SourceRule("Vehicular Pollution", {"traffic": 0.68, "wind": 0.10, "history": 0.17, "pm25": 0.05}, "traffic_match"),
    SourceRule("Industrial Emission", {"industry": 0.65, "satellite": 0.15, "wind": 0.08, "history": 0.12}, "industry_match"),
    SourceRule("Road Dust", {"road_dust": 0.60, "traffic": 0.15, "satellite": 0.08, "wind": 0.07, "history": 0.10}, "road_dust_match"),
    SourceRule("Biomass Burning", {"biomass_burning": 0.70, "satellite": 0.12, "wind": 0.06, "history": 0.12}, "biomass_match"),
)


def _active_confidence(detected: bool, confidence: float) -> float:
    return confidence if detected else 0.0


def _wind_factor(wind_speed: float) -> float:
    """Moderate-to-high wind can transport particulate pollution; cap at 25 km/h."""
    return min(wind_speed, 25) / 25


def _pm25_factor(pm25: float | None) -> float:
    # 150 µg/m³ is treated as a high-pollution reference level for this MVP.
    return min(pm25 or 0, 150) / 150


def attribute_sources(bundle: EvidenceBundle) -> list[SourceRanking]:
    signals = {
        "traffic": _active_confidence(bundle.traffic.detected, bundle.traffic.confidence),
        "construction": _active_confidence(bundle.construction.detected, bundle.construction.confidence),
        "industry": _active_confidence(bundle.industry.detected, bundle.industry.confidence),
        "satellite": _active_confidence(bundle.satellite.detected, bundle.satellite.confidence),
        "road_dust": _active_confidence(bundle.road_dust.detected, bundle.road_dust.confidence),
        "biomass_burning": _active_confidence(bundle.biomass_burning.detected, bundle.biomass_burning.confidence),
        "wind": _wind_factor(bundle.wind_speed),
        "pm25": _pm25_factor(bundle.pm25),
    }
    label_map = {
        "traffic": "Traffic activity detected",
        "construction": "Construction activity detected",
        "industry": "Industrial activity detected",
        "satellite": "Satellite particulate indication",
        "road_dust": "Road dust indication",
        "biomass_burning": "Biomass-burning indication",
        "wind": f"Wind transport ({bundle.wind_speed:g} km/h, {bundle.wind_direction})",
        "history": "Historical hotspot pattern",
        "pm25": "Elevated PM2.5 reading",
    }
    calculated: list[tuple[SourceRule, float, list[EvidenceFactor]]] = []
    for rule in RULES:
        factors: list[EvidenceFactor] = []
        raw_score = 0.0
        for signal, weight in rule.signal_weights.items():
            value = getattr(bundle.historical_patterns, rule.history_field) if signal == "history" else signals[signal]
            contribution = value * weight
            raw_score += contribution
            if contribution > 0:
                factors.append(EvidenceFactor(label=label_map[signal], contribution=round(contribution * 100, 1)))
        calculated.append((rule, raw_score, factors))

    total = sum(score for _, score, _ in calculated)
    if total == 0:
        # A transparent fallback for evidence bundles that contain no detected source signals.
        return [SourceRanking(source=rule.name, score=20.0, evidence=[]) for rule in RULES]

    rankings = [
        SourceRanking(source=rule.name, score=round((score / total) * 100, 1), evidence=factors)
        for rule, score, factors in calculated
    ]
    return sorted(rankings, key=lambda item: item.score, reverse=True)


def generate_explanation(bundle: EvidenceBundle) -> tuple[SourceRanking, str, str]:
    """Create a human-readable explanation from the same traceable rule output."""
    primary = attribute_sources(bundle)[0]
    evidence_labels = [factor.label for factor in primary.evidence]
    headline = f"{primary.source} is the most likely pollution source ({primary.score}%)."

    if evidence_labels:
        joined_evidence = ", ".join(evidence_labels[:-1])
        if len(evidence_labels) > 1:
            joined_evidence += f" and {evidence_labels[-1]}"
        else:
            joined_evidence = evidence_labels[0]
        summary = (
            f"This conclusion is supported by {joined_evidence}. "
            "The confidence reflects the weighted evidence available for this hotspot."
        )
    else:
        summary = (
            "No individual source signal was detected, so the result is an equal-confidence fallback "
            "that should be reviewed with additional evidence."
        )
    return primary, headline, summary
