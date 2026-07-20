from datetime import UTC, datetime, timedelta

from app.environmental_data.time_series_schemas import PollutantReading
from app.investigations.schemas import InvestigationRecord, InvestigationStatus
from app.investigations.traffic import (
    RoadSegmentTrafficProfile,
    TrafficDensityReading,
    TrafficEvidenceCollector,
    TrafficEvidenceRules,
)


NOW = datetime(2025, 1, 15, 9, tzinfo=UTC)


class NearbyRoad:
    def __init__(self, code, name, road_class, distance_meters):
        self.code = code
        self.name = name
        self.road_class = road_class
        self.distance_meters = distance_meters


class FakeGeoService:
    def find_entities_within_radius(self, entity_type, point, radius_meters):
        assert entity_type == "road_segments"
        return [
            NearbyRoad("ORR-01", "Outer Ring Road", "arterial", 180),
            NearbyRoad("RES-09", "Residential 9th Main", "local", 780),
        ]


class FakeTrafficProvider:
    def get_current_density(self, road_segment_code, observed_at):
        densities = {"ORR-01": 185.0, "RES-09": 42.0}
        return TrafficDensityReading(
            road_segment_code=road_segment_code,
            observed_at=observed_at,
            density_index=densities[road_segment_code],
            average_speed_kmph=18.0 if road_segment_code == "ORR-01" else 34.0,
            provenance="test_fixture",
        )

    def get_historical_baseline(self, road_segment_code, observed_at, comparison_days):
        baselines = {"ORR-01": 100.0, "RES-09": 45.0}
        return RoadSegmentTrafficProfile(
            road_segment_code=road_segment_code,
            comparable_hour=observed_at.hour,
            average_density_index=baselines[road_segment_code],
            sample_count=12,
            provenance="test_fixture",
        )


class FakeEnvironmentalService:
    def get_readings_for_time_window(self, station_code=None, ward_code=None, pollutant=None, start_at=None, end_at=None):
        values = {"NO2": 92.0, "CO": 3.8}
        return [
            PollutantReading(
                station_code="BLR-CBD-AQ",
                station_name="CBD",
                ward_code=ward_code,
                observed_at=NOW - timedelta(minutes=10),
                pollutant=pollutant,
                value=values[pollutant],
                unit="ug/m3",
                data_quality_status="valid",
            )
        ]


def investigation() -> InvestigationRecord:
    return InvestigationRecord(
        id=1,
        investigation_uid="inv-test",
        hotspot_id=42,
        hotspot_uid="hs-test",
        ward_code="BLR-W-001",
        station_code="BLR-CBD-AQ",
        status=InvestigationStatus.WAITING_FOR_EVIDENCE,
        environmental_context={},
        created_at=NOW,
    )


def context():
    return {
        "hotspot": {"ward_code": "BLR-W-001", "station_code": "BLR-CBD-AQ"},
        "latest_observation": {
            "observed_at": NOW.isoformat(),
            "ward_code": "BLR-W-001",
            "station_code": "BLR-CBD-AQ",
            "latitude": 12.9716,
            "longitude": 77.5946,
            "pollutant_snapshot": {"AQI": 225, "NO2": 94, "CO": 3.9},
        },
    }


def test_traffic_collector_detects_supporting_traffic_evidence_with_pollutant_patterns() -> None:
    collector = TrafficEvidenceCollector(
        geo_service=FakeGeoService(),
        traffic_provider=FakeTrafficProvider(),
        environmental_service=FakeEnvironmentalService(),
        rules=TrafficEvidenceRules(deviation_threshold_pct=25, proximity_threshold_meters=500),
    )

    results = collector.collect(investigation(), context())

    assert len(results) == 1
    result = results[0]
    assert result.source_type == "traffic"
    assert result.evidence_type == "traffic.density_anomaly"
    assert result.detected is True
    assert result.support_direction == "SUPPORTS"
    assert result.confidence == 0.86
    assert result.payload["max_density_deviation_pct"] == 85.0
    assert result.payload["rush_hour_correlated"] is True
    assert result.payload["nearest_road_distance_meters"] == 180
    assert result.payload["pollutant_patterns"]["NO2"]["elevated"] is True
    assert result.observed_at == NOW


def test_traffic_collector_returns_neutral_evidence_when_density_matches_baseline() -> None:
    class BaselineTrafficProvider(FakeTrafficProvider):
        def get_current_density(self, road_segment_code, observed_at):
            return TrafficDensityReading(
                road_segment_code=road_segment_code,
                observed_at=observed_at,
                density_index=50.0,
                average_speed_kmph=30.0,
                provenance="test_fixture",
            )

        def get_historical_baseline(self, road_segment_code, observed_at, comparison_days):
            return RoadSegmentTrafficProfile(
                road_segment_code=road_segment_code,
                comparable_hour=observed_at.hour,
                average_density_index=50.0,
                sample_count=12,
                provenance="test_fixture",
            )

    collector = TrafficEvidenceCollector(
        geo_service=FakeGeoService(),
        traffic_provider=BaselineTrafficProvider(),
        environmental_service=None,
    )

    result = collector.collect(investigation(), context())[0]

    assert result.detected is False
    assert result.support_direction == "NEUTRAL"
    assert result.confidence < 0.5
    assert result.payload["max_density_deviation_pct"] == 0.0


def test_traffic_collector_uses_seeded_data_when_live_dependencies_are_unavailable() -> None:
    collector = TrafficEvidenceCollector(geo_service=None, traffic_provider=None, environmental_service=None)

    result = collector.collect(investigation(), context())[0]

    assert result.source_type == "traffic"
    assert result.payload["traffic_data_provenance"] == "seeded_demo"
    assert result.payload["road_segments"]
