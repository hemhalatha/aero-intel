from math import isclose
from typing import Protocol

from app.aqi import classify_aqi

from .schemas import GeoJSONFeatureCollection, HeatmapRequest, StationAQISample


class AQIInterpolator(Protocol):
    def interpolate(self, samples: list[StationAQISample], request: HeatmapRequest) -> GeoJSONFeatureCollection:
        ...


class IDWInterpolator:
    def __init__(self, power: float = 2.0) -> None:
        self.power = power

    def interpolate(self, samples: list[StationAQISample], request: HeatmapRequest) -> GeoJSONFeatureCollection:
        usable_samples = [
            sample for sample in samples if request.include_unreliable_sensors or sample.is_reliable
        ]
        features = []
        for latitude in _grid_values(request.bbox.min_latitude, request.bbox.max_latitude, request.grid_resolution):
            for longitude in _grid_values(request.bbox.min_longitude, request.bbox.max_longitude, request.grid_resolution):
                aqi = self._interpolate_point(latitude, longitude, usable_samples, request)
                if aqi is None:
                    continue
                classification = classify_aqi(min(round(aqi, 2), 500))
                features.append(
                    {
                        "type": "Feature",
                        "geometry": {"type": "Point", "coordinates": [round(longitude, 6), round(latitude, 6)]},
                        "properties": {
                            "aqi": round(aqi, 2),
                            "band": classification.band,
                            "severity_rank": classification.severity_rank,
                            "display_label": classification.display_label,
                            "health_severity_category": classification.health_severity_category,
                        },
                    }
                )
        return {"type": "FeatureCollection", "features": features}

    def _interpolate_point(
        self,
        latitude: float,
        longitude: float,
        samples: list[StationAQISample],
        request: HeatmapRequest,
    ) -> float | None:
        if not samples:
            return None

        weighted_sum = 0.0
        total_weight = 0.0
        for sample in samples:
            distance = ((latitude - sample.latitude) ** 2 + (longitude - sample.longitude) ** 2) ** 0.5
            distance_weight = 1_000_000.0 if isclose(distance, 0.0, abs_tol=1e-12) else 1 / (distance**self.power)
            health_weight = sample.data_quality_score if sample.is_reliable else request.unhealthy_sensor_weight * sample.data_quality_score
            weight = distance_weight * health_weight
            weighted_sum += sample.aqi * weight
            total_weight += weight

        if total_weight == 0:
            return None
        return weighted_sum / total_weight


def _grid_values(start: float, end: float, step: float) -> list[float]:
    values: list[float] = []
    current = start
    while current <= end + (step / 10):
        values.append(round(current, 10))
        current += step
    return values
