from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any, Protocol

from pydantic import BaseModel, Field

from app.environmental_data.time_series_schemas import PollutantReading
from app.geo_master.schemas import GeoPoint

from .collectors import CollectorResult


class TrafficDensityReading(BaseModel):
    road_segment_code: str
    observed_at: datetime
    density_index: float = Field(ge=0)
    average_speed_kmph: float | None = Field(default=None, ge=0)
    provenance: str


class RoadSegmentTrafficProfile(BaseModel):
    road_segment_code: str
    comparable_hour: int = Field(ge=0, le=23)
    average_density_index: float = Field(ge=0)
    sample_count: int = Field(ge=0)
    provenance: str


class TrafficDataProvider(Protocol):
    def get_current_density(self, road_segment_code: str, observed_at: datetime) -> TrafficDensityReading:
        ...

    def get_historical_baseline(
        self,
        road_segment_code: str,
        observed_at: datetime,
        comparison_days: int,
    ) -> RoadSegmentTrafficProfile:
        ...


@dataclass(frozen=True)
class TrafficEvidenceRules:
    search_radius_meters: float = 1_000
    proximity_threshold_meters: float = 500
    deviation_threshold_pct: float = 30
    comparison_days: int = 28
    pollutant_window_minutes: int = 90
    no2_elevated_threshold: float = 80
    co_elevated_threshold: float = 3
    rush_hours: tuple[int, ...] = (7, 8, 9, 17, 18, 19)


class SeededTrafficDataProvider:
    def get_current_density(self, road_segment_code: str, observed_at: datetime) -> TrafficDensityReading:
        seed = {
            "SEEDED-ARTERIAL-1": (176.0, 19.0),
            "SEEDED-COLLECTOR-1": (94.0, 28.0),
        }.get(road_segment_code, (72.0, 34.0))
        return TrafficDensityReading(
            road_segment_code=road_segment_code,
            observed_at=observed_at,
            density_index=seed[0],
            average_speed_kmph=seed[1],
            provenance="seeded_demo",
        )

    def get_historical_baseline(
        self,
        road_segment_code: str,
        observed_at: datetime,
        comparison_days: int,
    ) -> RoadSegmentTrafficProfile:
        baseline = {
            "SEEDED-ARTERIAL-1": 104.0,
            "SEEDED-COLLECTOR-1": 80.0,
        }.get(road_segment_code, 70.0)
        return RoadSegmentTrafficProfile(
            road_segment_code=road_segment_code,
            comparable_hour=observed_at.hour,
            average_density_index=baseline,
            sample_count=max(comparison_days // 7, 1) * 3,
            provenance="seeded_demo",
        )


class SeededRoadSegment:
    def __init__(self, code: str, name: str, road_class: str, distance_meters: float) -> None:
        self.code = code
        self.name = name
        self.road_class = road_class
        self.distance_meters = distance_meters


class TrafficEvidenceCollector:
    name = "traffic"
    enabled = True

    def __init__(
        self,
        geo_service=None,
        traffic_provider: TrafficDataProvider | None = None,
        environmental_service=None,
        rules: TrafficEvidenceRules | None = None,
    ) -> None:
        self.geo_service = geo_service
        self.traffic_provider = traffic_provider or SeededTrafficDataProvider()
        self.environmental_service = environmental_service
        self.rules = rules or TrafficEvidenceRules()

    def collect(self, investigation, context: dict[str, Any]) -> list[CollectorResult]:
        observed_at = self._observed_at(context)
        ward_code = self._ward_code(investigation, context)
        station_code = self._station_code(investigation, context)
        roads = self._nearby_roads(context)
        segment_details = [self._segment_evidence(road, observed_at) for road in roads]
        max_deviation = max((item["density_deviation_pct"] for item in segment_details), default=0.0)
        nearest_distance = min((item["distance_meters"] for item in segment_details), default=None)
        rush_hour_correlated = observed_at.hour in self.rules.rush_hours and max_deviation >= self.rules.deviation_threshold_pct
        pollutant_patterns = self._pollutant_patterns(ward_code, station_code, observed_at, context)
        detected = max_deviation >= self.rules.deviation_threshold_pct
        support_direction = self._support_direction(detected, pollutant_patterns)
        confidence = self._confidence(max_deviation, nearest_distance, rush_hour_correlated, pollutant_patterns)

        return [
            CollectorResult(
                source_type="traffic",
                evidence_type="traffic.density_anomaly",
                source="traffic_collector",
                detected=detected,
                support_direction=support_direction,
                confidence=confidence,
                payload={
                    "ward_code": ward_code,
                    "station_code": station_code,
                    "road_segments": segment_details,
                    "max_density_deviation_pct": round(max_deviation, 2),
                    "nearest_road_distance_meters": nearest_distance,
                    "rush_hour_correlated": rush_hour_correlated,
                    "pollutant_patterns": pollutant_patterns,
                    "traffic_data_provenance": self._traffic_provenance(segment_details),
                },
                observed_at=observed_at,
            )
        ]

    def _nearby_roads(self, context: dict[str, Any]) -> list[Any]:
        point = self._hotspot_point(context)
        if self.geo_service is not None and point is not None:
            roads = self.geo_service.find_entities_within_radius(
                "road_segments",
                point,
                self.rules.search_radius_meters,
            )
            if roads:
                return roads
        return [
            SeededRoadSegment("SEEDED-ARTERIAL-1", "Seeded arterial corridor", "arterial", 220),
            SeededRoadSegment("SEEDED-COLLECTOR-1", "Seeded collector road", "collector", 640),
        ]

    def _segment_evidence(self, road: Any, observed_at: datetime) -> dict[str, Any]:
        code = getattr(road, "code")
        current = self.traffic_provider.get_current_density(code, observed_at)
        baseline = self.traffic_provider.get_historical_baseline(code, observed_at, self.rules.comparison_days)
        deviation = self._percentage_deviation(current.density_index, baseline.average_density_index)
        return {
            "road_segment_code": code,
            "road_name": getattr(road, "name", code),
            "road_class": getattr(road, "road_class", "unknown"),
            "distance_meters": getattr(road, "distance_meters", None),
            "current_density_index": current.density_index,
            "baseline_density_index": baseline.average_density_index,
            "density_deviation_pct": round(deviation, 2),
            "average_speed_kmph": current.average_speed_kmph,
            "current_provenance": current.provenance,
            "baseline_provenance": baseline.provenance,
        }

    def _pollutant_patterns(
        self,
        ward_code: str | None,
        station_code: str | None,
        observed_at: datetime,
        context: dict[str, Any],
    ) -> dict[str, dict[str, Any]]:
        patterns = {}
        for pollutant, threshold in {"NO2": self.rules.no2_elevated_threshold, "CO": self.rules.co_elevated_threshold}.items():
            value = self._pollutant_value_from_repository(pollutant, ward_code, station_code, observed_at)
            if value is None:
                value = self._pollutant_value_from_context(pollutant, context)
            if value is not None:
                patterns[pollutant] = {"value": value, "threshold": threshold, "elevated": value >= threshold}
        return patterns

    def _pollutant_value_from_repository(
        self,
        pollutant: str,
        ward_code: str | None,
        station_code: str | None,
        observed_at: datetime,
    ) -> float | None:
        if self.environmental_service is None:
            return None
        readings: list[PollutantReading] = self.environmental_service.get_readings_for_time_window(
            station_code=station_code,
            ward_code=ward_code,
            pollutant=pollutant,
            start_at=observed_at - timedelta(minutes=self.rules.pollutant_window_minutes),
            end_at=observed_at,
        )
        valid = [reading.value for reading in readings if reading.data_quality_status == "valid"]
        return max(valid) if valid else None

    @staticmethod
    def _pollutant_value_from_context(pollutant: str, context: dict[str, Any]) -> float | None:
        snapshot = context.get("latest_observation", {}).get("pollutant_snapshot", {})
        value = snapshot.get(pollutant)
        return float(value) if value is not None else None

    def _confidence(
        self,
        max_deviation: float,
        nearest_distance: float | None,
        rush_hour_correlated: bool,
        pollutant_patterns: dict[str, dict[str, Any]],
    ) -> float:
        confidence = max(min(max_deviation / 100, 0.55), 0)
        if nearest_distance is not None and nearest_distance <= self.rules.proximity_threshold_meters:
            confidence += 0.18
        if rush_hour_correlated:
            confidence += 0.08
        if any(item["elevated"] for item in pollutant_patterns.values()):
            confidence += 0.05
        return round(min(confidence, 0.95), 2)

    @staticmethod
    def _support_direction(detected: bool, pollutant_patterns: dict[str, dict[str, Any]]) -> str:
        if detected:
            return "SUPPORTS"
        if pollutant_patterns and not any(item["elevated"] for item in pollutant_patterns.values()):
            return "CONTRADICTS"
        return "NEUTRAL"

    @staticmethod
    def _percentage_deviation(current: float, baseline: float) -> float:
        if baseline <= 0:
            return 0.0
        return ((current - baseline) / baseline) * 100

    @staticmethod
    def _traffic_provenance(segment_details: list[dict[str, Any]]) -> str:
        provenances = {item["current_provenance"] for item in segment_details}
        return "seeded_demo" if provenances == {"seeded_demo"} else "mixed_or_live"

    @staticmethod
    def _observed_at(context: dict[str, Any]) -> datetime:
        raw = context.get("latest_observation", {}).get("observed_at") or context.get("observed_at")
        if isinstance(raw, datetime):
            return raw
        if isinstance(raw, str):
            return datetime.fromisoformat(raw)
        return datetime.now(UTC)

    @staticmethod
    def _ward_code(investigation, context: dict[str, Any]) -> str | None:
        return investigation.ward_code or context.get("latest_observation", {}).get("ward_code") or context.get("hotspot", {}).get("ward_code")

    @staticmethod
    def _station_code(investigation, context: dict[str, Any]) -> str | None:
        return investigation.station_code or context.get("latest_observation", {}).get("station_code") or context.get("hotspot", {}).get("station_code")

    @staticmethod
    def _hotspot_point(context: dict[str, Any]) -> GeoPoint | None:
        latest = context.get("latest_observation", {})
        latitude = latest.get("latitude")
        longitude = latest.get("longitude")
        if latitude is None or longitude is None:
            return None
        return GeoPoint(latitude=latitude, longitude=longitude)
