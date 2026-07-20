from collections.abc import Sequence

from .config import CPCB_AQI_BANDS
from .schemas import AQIBandConfig, AQIClassification


class AQIClassifier:
    def __init__(self, bands: Sequence[AQIBandConfig]) -> None:
        if not bands:
            raise ValueError("At least one AQI band is required.")
        self.bands = tuple(sorted(bands, key=lambda band: band.min_value))

    def classify(self, aqi: float) -> AQIClassification:
        if aqi < 0:
            raise ValueError("AQI value must be non-negative.")

        for band in self.bands:
            if band.min_value <= aqi <= band.max_value:
                return AQIClassification(
                    aqi=aqi,
                    band=band.band,
                    severity_rank=band.severity_rank,
                    display_label=band.display_label,
                    health_severity_category=band.health_severity_category,
                )

        raise ValueError("AQI value exceeds configured bands.")


def classify_aqi(aqi: float) -> AQIClassification:
    return AQIClassifier(CPCB_AQI_BANDS).classify(aqi)
