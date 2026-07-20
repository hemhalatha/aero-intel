from datetime import UTC, datetime, timedelta

from app.environmental_data.time_series_schemas import PollutantReading, WindReading
from app.investigations.industrial import IndustrialEvidenceCollector, IndustrialEvidenceRules, IndustrialUnit
from app.investigations.schemas import InvestigationRecord, InvestigationStatus


NOW = datetime(2025, 1, 15, 11, tzinfo=UTC)


class FakeIndustrialProvider:
    def find_units_within_radius(self, point, radius_meters):
        return [
            IndustrialUnit(
                unit_id="IND-001",
                name="Peenya Boilers",
                industry_type="boiler_operations",
                pollution_category="red",
                latitude=12.9731,
                longitude=77.5926,
                distance_meters=290,
                consent_status="valid",
                compliance_status="non_compliant",
                consent_valid_until=NOW + timedelta(days=120),
                last_reported_activity_at=NOW - timedelta(minutes=35),
                activity_status="operational",
                regulated_pollutants=["SO2", "NO2", "CO"],
                provenance="test_postgis",
            ),
            IndustrialUnit(
                unit_id="IND-002",
                name="Small Fabrication Yard",
                industry_type="fabrication",
                pollution_category="orange",
                latitude=12.9750,
                longitude=77.5910,
                distance_meters=620,
                consent_status="valid",
                compliance_status="compliant",
                consent_valid_until=NOW + timedelta(days=200),
                last_reported_activity_at=NOW - timedelta(hours=3),
                activity_status="operational",
                regulated_pollutants=["NO2"],
                provenance="test_postgis",
            ),
        ]


class FakeEnvironmentalService:
    def get_readings_for_time_window(self, station_code=None, ward_code=None, pollutant=None, start_at=None, end_at=None):
        values = {"SO2": 86.0, "NO2": 104.0, "CO": 4.1}
        return [
            PollutantReading(
                station_code=station_code or "BLR-CBD-AQ",
                station_name="CBD",
                ward_code=ward_code,
                observed_at=NOW - timedelta(minutes=20),
                pollutant=pollutant,
                value=values[pollutant],
                unit="ug/m3",
                data_quality_status="valid",
            )
        ]

    def get_current_wind(self, location_code=None):
        return WindReading(
            location_code="BLR-CENTRE",
            city="Bengaluru",
            observed_at=NOW,
            wind_speed_kmh=12,
            wind_direction_degrees=270,
            data_quality_status="valid",
        )


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
        "latest_observation": {
            "observed_at": NOW.isoformat(),
            "ward_code": "BLR-W-001",
            "station_code": "BLR-CBD-AQ",
            "latitude": 12.9716,
            "longitude": 77.5946,
            "pollutant_snapshot": {"AQI": 245, "SO2": 84, "NO2": 100, "CO": 4.2},
        }
    }


def test_industrial_collector_supports_when_units_pollutants_wind_and_activity_align() -> None:
    collector = IndustrialEvidenceCollector(
        industrial_provider=FakeIndustrialProvider(),
        environmental_service=FakeEnvironmentalService(),
        rules=IndustrialEvidenceRules(search_radius_meters=1_000, near_unit_threshold_meters=500),
    )

    result = collector.collect(investigation(), context())[0]

    assert result.source_type == "industrial"
    assert result.evidence_type == "industrial.activity_signal"
    assert result.detected is True
    assert result.support_direction == "SUPPORTS"
    assert result.confidence == 0.95
    assert result.payload["nearby_industrial_unit_count"] == 2
    assert result.payload["highest_pollution_category"] == "red"
    assert result.payload["compliance_risk_count"] == 1
    assert result.payload["nearest_unit_distance_meters"] == 290
    assert result.payload["upwind_supported"] is True
    assert result.payload["temporal_alignment"]["recent_activity_count"] == 1
    assert result.payload["pollutant_anomalies"]["SO2"]["elevated"] is True
    assert result.observed_at == NOW


def test_industrial_collector_returns_neutral_when_no_units_are_nearby() -> None:
    class EmptyIndustrialProvider:
        def find_units_within_radius(self, point, radius_meters):
            return []

    collector = IndustrialEvidenceCollector(
        industrial_provider=EmptyIndustrialProvider(),
        environmental_service=None,
    )

    result = collector.collect(investigation(), context())[0]

    assert result.detected is False
    assert result.support_direction == "NEUTRAL"
    assert result.confidence < 0.5
    assert result.payload["nearby_industrial_unit_count"] == 0


def test_industrial_collector_uses_seeded_units_when_provider_is_unavailable() -> None:
    collector = IndustrialEvidenceCollector(industrial_provider=None, environmental_service=None)

    result = collector.collect(investigation(), context())[0]

    assert result.source_type == "industrial"
    assert result.payload["industrial_data_provenance"] == "seeded_demo"
    assert result.payload["nearby_industrial_unit_count"] >= 1
