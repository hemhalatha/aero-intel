import pytest

from app.aqi.classifier import AQIClassifier, CPCB_AQI_BANDS
from app.aqi.schemas import AQIBandConfig


@pytest.mark.parametrize(
    ("aqi", "band", "rank", "label", "health_category"),
    [
        (0, "GOOD", 1, "Good", "low"),
        (50, "GOOD", 1, "Good", "low"),
        (51, "SATISFACTORY", 2, "Satisfactory", "moderate"),
        (100, "SATISFACTORY", 2, "Satisfactory", "moderate"),
        (101, "MODERATELY_POLLUTED", 3, "Moderately Polluted", "unhealthy_for_sensitive_groups"),
        (200, "MODERATELY_POLLUTED", 3, "Moderately Polluted", "unhealthy_for_sensitive_groups"),
        (201, "POOR", 4, "Poor", "unhealthy"),
        (300, "POOR", 4, "Poor", "unhealthy"),
        (301, "VERY_POOR", 5, "Very Poor", "very_unhealthy"),
        (400, "VERY_POOR", 5, "Very Poor", "very_unhealthy"),
        (401, "SEVERE", 6, "Severe", "hazardous"),
        (500, "SEVERE", 6, "Severe", "hazardous"),
    ],
)
def test_classifies_cpcb_aqi_bands(aqi, band, rank, label, health_category) -> None:
    result = AQIClassifier(CPCB_AQI_BANDS).classify(aqi)

    assert result.band == band
    assert result.severity_rank == rank
    assert result.display_label == label
    assert result.health_severity_category == health_category


def test_rejects_aqi_values_outside_configured_thresholds() -> None:
    classifier = AQIClassifier(CPCB_AQI_BANDS)

    with pytest.raises(ValueError, match="AQI value must be non-negative"):
        classifier.classify(-1)

    with pytest.raises(ValueError, match="AQI value exceeds configured bands"):
        classifier.classify(501)


def test_supports_custom_configured_bands_without_code_duplication() -> None:
    custom = [
        AQIBandConfig(
            band="LOW",
            min_value=0,
            max_value=10,
            severity_rank=1,
            display_label="Low",
            health_severity_category="low",
        ),
        AQIBandConfig(
            band="HIGH",
            min_value=11,
            max_value=20,
            severity_rank=2,
            display_label="High",
            health_severity_category="high",
        ),
    ]

    assert AQIClassifier(custom).classify(15).band == "HIGH"
