from app.heatmap.idw import IDWInterpolator
from app.heatmap.schemas import BoundingBox, HeatmapRequest, StationAQISample
from app.heatmap.service import AQIHeatmapService


def sample(
    station_code: str,
    latitude: float,
    longitude: float,
    aqi: float,
    quality_score: float = 1.0,
    reliable: bool = True,
    ward_code: str = "BLR-W-001",
) -> StationAQISample:
    return StationAQISample(
        station_code=station_code,
        station_name=station_code,
        ward_code=ward_code,
        latitude=latitude,
        longitude=longitude,
        aqi=aqi,
        data_quality_score=quality_score,
        sensor_status="ONLINE" if reliable else "DEGRADED",
        is_reliable=reliable,
    )


def test_idw_generates_leaflet_mapbox_ready_geojson_grid() -> None:
    interpolator = IDWInterpolator(power=2)
    request = HeatmapRequest(
        bbox=BoundingBox(min_latitude=12.0, min_longitude=77.0, max_latitude=12.1, max_longitude=77.1),
        grid_resolution=0.1,
    )

    layer = interpolator.interpolate(
        samples=[
            sample("A", 12.0, 77.0, 50),
            sample("B", 12.1, 77.1, 150),
        ],
        request=request,
    )

    assert layer["type"] == "FeatureCollection"
    assert len(layer["features"]) == 4
    first = layer["features"][0]
    assert first["geometry"]["type"] == "Point"
    assert {"aqi", "band", "severity_rank", "display_label", "health_severity_category"} <= set(first["properties"])


def test_idw_reduces_weight_for_unhealthy_sensors() -> None:
    interpolator = IDWInterpolator(power=2)
    request = HeatmapRequest(
        bbox=BoundingBox(min_latitude=12.0, min_longitude=77.0, max_latitude=12.0, max_longitude=77.0),
        grid_resolution=0.1,
        unhealthy_sensor_weight=0.1,
    )

    layer = interpolator.interpolate(
        samples=[
            sample("healthy", 12.0, 77.0, 50),
            sample("unhealthy", 12.0, 77.0, 300, quality_score=0.2, reliable=False),
        ],
        request=request,
    )

    assert layer["features"][0]["properties"]["aqi"] < 100


def test_heatmap_service_returns_ward_average_aqi_with_classification() -> None:
    class Repository:
        def get_latest_station_aqi_samples(self, bbox):
            return [
                sample("A", 12.0, 77.0, 50, ward_code="BLR-W-001"),
                sample("B", 12.1, 77.1, 150, ward_code="BLR-W-001"),
                sample("C", 12.2, 77.2, 300, reliable=False, quality_score=0.3, ward_code="BLR-W-002"),
            ]

    service = AQIHeatmapService(repository=Repository(), interpolator=IDWInterpolator())

    summaries = service.get_ward_aqi_summaries()

    assert summaries[0].ward_code == "BLR-W-001"
    assert summaries[0].average_aqi == 100
    assert summaries[0].band == "SATISFACTORY"
    assert summaries[1].station_count == 1
