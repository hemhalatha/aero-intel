from datetime import UTC, datetime, timedelta

from app.environmental_data.time_series_schemas import PollutantReading, WindReading
from app.investigations.construction import (
    ConstructionEvidenceCollector,
    ConstructionEvidenceRules,
    ConstructionPermit,
)
from app.investigations.schemas import InvestigationRecord, InvestigationStatus


NOW = datetime(2025, 1, 15, 10, tzinfo=UTC)


class LandUseZone:
    def __init__(self, code, name, category, distance_meters):
        self.code = code
        self.name = name
        self.category = category
        self.distance_meters = distance_meters


class FakeConstructionProvider:
    def find_active_permits_within_radius(self, point, radius_meters, observed_at):
        return [
            ConstructionPermit(
                permit_id="BLR-CON-101",
                site_name="Metro cut-and-cover works",
                category="infrastructure",
                latitude=12.9721,
                longitude=77.5929,
                distance_meters=210,
                valid_from=NOW - timedelta(days=20),
                valid_until=NOW + timedelta(days=50),
                activity_start=NOW - timedelta(days=10),
                activity_end=NOW + timedelta(days=20),
                activity_status="active",
                dust_control_declared=True,
                provenance="test_postgis",
            ),
            ConstructionPermit(
                permit_id="BLR-CON-102",
                site_name="Commercial tower excavation",
                category="commercial",
                latitude=12.9723,
                longitude=77.5931,
                distance_meters=260,
                valid_from=NOW - timedelta(days=45),
                valid_until=NOW + timedelta(days=70),
                activity_start=NOW - timedelta(days=2),
                activity_end=NOW + timedelta(days=30),
                activity_status="active",
                dust_control_declared=False,
                provenance="test_postgis",
            ),
        ]


class FakeGeoService:
    def find_entities_within_radius(self, entity_type, point, radius_meters):
        assert entity_type == "land_use_zones"
        return [
            LandUseZone("LU-MIX-1", "Transit Mixed Use", "mixed_use", 120),
            LandUseZone("LU-RES-4", "Residences East", "residential", 420),
        ]


class FakeEnvironmentalService:
    def get_readings_for_time_window(self, station_code=None, ward_code=None, pollutant=None, start_at=None, end_at=None):
        values = {"PM10": 248.0, "PM2.5": 92.0}
        return [
            PollutantReading(
                station_code=station_code or "BLR-CBD-AQ",
                station_name="CBD",
                ward_code=ward_code,
                observed_at=NOW - timedelta(minutes=15),
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
            wind_speed_kmh=14,
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
            "pollutant_snapshot": {"AQI": 225, "PM10": 240, "PM2.5": 91},
        }
    }


def test_construction_collector_supports_when_active_nearby_cluster_pm_and_wind_align() -> None:
    collector = ConstructionEvidenceCollector(
        construction_provider=FakeConstructionProvider(),
        geo_service=FakeGeoService(),
        environmental_service=FakeEnvironmentalService(),
        rules=ConstructionEvidenceRules(search_radius_meters=800, cluster_radius_meters=150),
    )

    result = collector.collect(investigation(), context())[0]

    assert result.source_type == "construction_land_use"
    assert result.evidence_type == "construction.land_use_activity"
    assert result.detected is True
    assert result.support_direction == "SUPPORTS"
    assert result.confidence == 0.9
    assert result.payload["active_permit_count"] == 2
    assert result.payload["construction_cluster_count"] == 1
    assert result.payload["nearest_site_distance_meters"] == 210
    assert result.payload["wind_transport_supported"] is True
    assert result.payload["pm_context"]["PM10"]["elevated"] is True
    assert result.payload["land_use_context"][0]["category"] == "mixed_use"
    assert result.observed_at == NOW


def test_construction_collector_returns_neutral_when_no_active_permits_are_nearby() -> None:
    class EmptyConstructionProvider:
        def find_active_permits_within_radius(self, point, radius_meters, observed_at):
            return []

    collector = ConstructionEvidenceCollector(
        construction_provider=EmptyConstructionProvider(),
        geo_service=FakeGeoService(),
        environmental_service=None,
    )

    result = collector.collect(investigation(), context())[0]

    assert result.detected is False
    assert result.support_direction == "NEUTRAL"
    assert result.confidence < 0.5
    assert result.payload["active_permit_count"] == 0


def test_construction_collector_uses_seeded_permits_when_provider_is_unavailable() -> None:
    collector = ConstructionEvidenceCollector(construction_provider=None, geo_service=None, environmental_service=None)

    result = collector.collect(investigation(), context())[0]

    assert result.source_type == "construction_land_use"
    assert result.payload["permit_data_provenance"] == "seeded_demo"
    assert result.payload["active_permit_count"] >= 1
