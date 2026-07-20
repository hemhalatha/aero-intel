from collections import defaultdict
from typing import Protocol

from app.aqi import classify_aqi

from .idw import AQIInterpolator
from .schemas import BoundingBox, GeoJSONFeatureCollection, HeatmapRequest, StationAQISample, WardAQISummary


class AQIHeatmapRepositoryProtocol(Protocol):
    def get_latest_station_aqi_samples(self, bbox: BoundingBox | None = None) -> list[StationAQISample]:
        ...


class AQIHeatmapService:
    def __init__(self, repository: AQIHeatmapRepositoryProtocol, interpolator: AQIInterpolator) -> None:
        self.repository = repository
        self.interpolator = interpolator

    def get_current_heatmap(self, request: HeatmapRequest) -> GeoJSONFeatureCollection:
        samples = self.repository.get_latest_station_aqi_samples(request.bbox)
        return self.interpolator.interpolate(samples, request)

    def get_ward_aqi_summaries(self, bbox: BoundingBox | None = None) -> list[WardAQISummary]:
        samples = self.repository.get_latest_station_aqi_samples(bbox)
        grouped: dict[str, list[StationAQISample]] = defaultdict(list)
        for sample in samples:
            if sample.ward_code:
                grouped[sample.ward_code].append(sample)

        summaries: list[WardAQISummary] = []
        for ward_code, ward_samples in sorted(grouped.items()):
            average = round(sum(sample.aqi for sample in ward_samples) / len(ward_samples), 2)
            classification = classify_aqi(min(average, 500))
            summaries.append(
                WardAQISummary(
                    ward_code=ward_code,
                    average_aqi=average,
                    station_count=len(ward_samples),
                    band=classification.band,
                    severity_rank=classification.severity_rank,
                    display_label=classification.display_label,
                    health_severity_category=classification.health_severity_category,
                )
            )
        return summaries
