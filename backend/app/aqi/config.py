from .schemas import AQIBandConfig

CPCB_AQI_BANDS = (
    AQIBandConfig(
        band="GOOD",
        min_value=0,
        max_value=50,
        severity_rank=1,
        display_label="Good",
        health_severity_category="low",
    ),
    AQIBandConfig(
        band="SATISFACTORY",
        min_value=51,
        max_value=100,
        severity_rank=2,
        display_label="Satisfactory",
        health_severity_category="moderate",
    ),
    AQIBandConfig(
        band="MODERATELY_POLLUTED",
        min_value=101,
        max_value=200,
        severity_rank=3,
        display_label="Moderately Polluted",
        health_severity_category="unhealthy_for_sensitive_groups",
    ),
    AQIBandConfig(
        band="POOR",
        min_value=201,
        max_value=300,
        severity_rank=4,
        display_label="Poor",
        health_severity_category="unhealthy",
    ),
    AQIBandConfig(
        band="VERY_POOR",
        min_value=301,
        max_value=400,
        severity_rank=5,
        display_label="Very Poor",
        health_severity_category="very_unhealthy",
    ),
    AQIBandConfig(
        band="SEVERE",
        min_value=401,
        max_value=500,
        severity_rank=6,
        display_label="Severe",
        health_severity_category="hazardous",
    ),
)
