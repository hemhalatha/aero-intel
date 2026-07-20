from datetime import UTC, datetime, timedelta

from app.command_center.service import CommandCenterAggregationService, EmptyHotspotSummaryProvider
from app.environmental_data.time_series_schemas import PollutantReading, StationLatestState, WeatherReading, WindReading
from app.heatmap.schemas import WardAQISummary
from app.sensor_health.schemas import SensorHealthSnapshot, SensorHealthStatus


NOW = datetime(2025, 1, 15, 12, tzinfo=UTC)


class FakeHeatmapService:
    def get_ward_aqi_summaries(self):
        return [
            WardAQISummary(
                ward_code="BLR-W-001",
                average_aqi=110,
                station_count=2,
                band="MODERATELY_POLLUTED",
                severity_rank=3,
                display_label="Moderately Polluted",
                health_severity_category="unhealthy_for_sensitive_groups",
            ),
            WardAQISummary(
                ward_code="BLR-W-002",
                average_aqi=240,
                station_count=1,
                band="POOR",
                severity_rank=4,
                display_label="Poor",
                health_severity_category="unhealthy",
            ),
        ]


class FakeSensorHealthService:
    def get_all_station_health(self):
        return [
            SensorHealthSnapshot(
                station_code="BLR-CBD-AQ",
                station_name="CBD",
                ward_code="BLR-W-001",
                status=SensorHealthStatus.ONLINE,
                data_quality_score=0.95,
                last_reading_at=NOW,
                evaluated_at=NOW,
                is_reliable=True,
            ),
            SensorHealthSnapshot(
                station_code="BLR-IND-AQ",
                station_name="Indiranagar",
                ward_code="BLR-W-002",
                status=SensorHealthStatus.DEGRADED,
                data_quality_score=0.55,
                last_reading_at=NOW,
                evaluated_at=NOW,
                reasons=["missing_pollutants"],
                is_reliable=False,
            ),
        ]


class FakeTimeSeriesService:
    def get_latest_station_readings(self):
        reading = PollutantReading(
            station_code="BLR-CBD-AQ",
            station_name="CBD",
            ward_code="BLR-W-001",
            observed_at=NOW,
            pollutant="AQI",
            value=118,
            unit="index",
            data_quality_status="valid",
        )
        unreliable = reading.model_copy(update={"station_code": "BLR-IND-AQ", "station_name": "Indiranagar"})
        return [
            StationLatestState(
                station_code="BLR-CBD-AQ",
                station_name="CBD",
                ward_code="BLR-W-001",
                observed_at=NOW,
                readings=[reading],
                data_quality_status="valid",
            ),
            StationLatestState(
                station_code="BLR-IND-AQ",
                station_name="Indiranagar",
                ward_code="BLR-W-002",
                observed_at=NOW,
                readings=[unreliable],
                data_quality_status="suspect",
            ),
        ]

    def get_current_weather(self, location_code=None):
        return WeatherReading(
            location_code="BLR-CENTRE",
            city="Bengaluru",
            observed_at=NOW,
            temperature_c=24.2,
            relative_humidity_pct=54,
            data_quality_status="valid",
        )

    def get_current_wind(self, location_code=None):
        return WindReading(
            location_code="BLR-CENTRE",
            city="Bengaluru",
            observed_at=NOW,
            wind_speed_kmh=13.7,
            wind_direction_degrees=92,
            data_quality_status="valid",
        )

    def get_readings_for_time_window(self, station_code=None, ward_code=None, pollutant=None, start_at=None, end_at=None):
        return [
            PollutantReading(
                station_code="BLR-CBD-AQ",
                station_name="CBD",
                ward_code="BLR-W-001",
                observed_at=NOW - timedelta(hours=1),
                pollutant="AQI",
                value=100,
                unit="index",
                data_quality_status="valid",
            ),
            PollutantReading(
                station_code="BLR-CBD-AQ",
                station_name="CBD",
                ward_code="BLR-W-001",
                observed_at=NOW,
                pollutant="AQI",
                value=118,
                unit="index",
                data_quality_status="valid",
            ),
        ]


def test_command_center_aggregates_existing_service_outputs_for_initial_dashboard() -> None:
    service = CommandCenterAggregationService(
        heatmap_service=FakeHeatmapService(),
        sensor_health_service=FakeSensorHealthService(),
        time_series_service=FakeTimeSeriesService(),
        hotspot_provider=EmptyHotspotSummaryProvider(),
    )

    dashboard = service.get_initial_dashboard(now=NOW)

    assert dashboard.city_average_aqi == 153.33
    assert dashboard.worst_affected_ward.ward_code == "BLR-W-002"
    assert dashboard.active_hotspot_count == 0
    assert dashboard.offline_or_degraded_station_count == 1
    assert [state.station_code for state in dashboard.latest_reliable_station_readings] == ["BLR-CBD-AQ"]
    assert dashboard.weather_summary.temperature_c == 24.2
    assert dashboard.wind_information.wind_direction_degrees == 92
    assert dashboard.current_hotspot_summaries == []
    assert [point.average_aqi for point in dashboard.city_pollution_trend] == [100, 118]
