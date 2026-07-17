import pytest
from pydantic import ValidationError

from app.geo_master.schemas import GeoPoint, MonitoringStationRead
from app.geo_master.services import GeoMasterService, calculate_distance_meters


def test_calculates_distance_between_geographic_points() -> None:
    indiranagar = GeoPoint(latitude=12.9784, longitude=77.6408)
    mg_road = GeoPoint(latitude=12.9758, longitude=77.6068)

    distance = calculate_distance_meters(indiranagar, mg_road)

    assert distance == pytest.approx(3696, abs=75)


def test_rejects_invalid_coordinates() -> None:
    with pytest.raises(ValidationError):
        GeoPoint(latitude=95.0, longitude=77.5946)

    with pytest.raises(ValidationError):
        GeoPoint(latitude=12.9716, longitude=190.0)


def test_filters_entities_within_radius_from_service_results() -> None:
    service = GeoMasterService(repository=None)
    origin = GeoPoint(latitude=12.9716, longitude=77.5946)
    stations = [
        MonitoringStationRead(
            id=1,
            city_id=1,
            ward_id=1,
            code="BLR-CBD",
            name="CBD Monitor",
            latitude=12.972,
            longitude=77.595,
            is_active=True,
        ),
        MonitoringStationRead(
            id=2,
            city_id=1,
            ward_id=2,
            code="BLR-OUTER",
            name="Outer Ring Monitor",
            latitude=13.0358,
            longitude=77.597,
            is_active=True,
        ),
    ]

    nearby = service.filter_entities_within_radius(origin, stations, radius_meters=500)

    assert [station.code for station in nearby] == ["BLR-CBD"]
