from datetime import UTC, datetime, timedelta

from app.environmental_data.time_series import EnvironmentalTimeSeriesService
from app.environmental_data.time_series_schemas import (
    PollutantReading,
    StationLatestState,
    WeatherForecastReading,
    WeatherReading,
    WindReading,
)


NOW = datetime(2025, 1, 15, 12, tzinfo=UTC)


class FakeTimeSeriesRepository:
    def __init__(self) -> None:
        self.pm25 = PollutantReading(
            station_code="BLR-CBD-AQ",
            station_name="CBD Air Quality Station",
            ward_code="BLR-W-001",
            observed_at=NOW,
            pollutant="PM2.5",
            value=72.4,
            unit="ug/m3",
            data_quality_status="valid",
        )
        self.no2 = self.pm25.model_copy(update={"pollutant": "NO2", "value": 32.8})
        self.weather = WeatherReading(
            location_code="BLR-CENTRE",
            city="Bengaluru",
            observed_at=NOW,
            temperature_c=24.2,
            relative_humidity_pct=54,
            data_quality_status="valid",
        )
        self.wind = WindReading(
            location_code="BLR-CENTRE",
            city="Bengaluru",
            observed_at=NOW,
            wind_speed_kmh=13.7,
            wind_direction_degrees=92,
            data_quality_status="valid",
        )

    def get_latest_station_readings(self):
        return [
            StationLatestState(
                station_code="BLR-CBD-AQ",
                station_name="CBD Air Quality Station",
                ward_code="BLR-W-001",
                observed_at=NOW,
                readings=[self.pm25, self.no2],
                data_quality_status="valid",
            )
        ]

    def get_station_history(self, station_code, start_at, end_at):
        return [self.pm25, self.no2]

    def get_ward_aqi_history(self, ward_code, start_at, end_at):
        return [self.pm25.model_copy(update={"pollutant": "AQI", "value": 154})]

    def get_ward_pollutant_history(self, ward_code, pollutant, start_at, end_at):
        return [self.pm25] if pollutant == "PM2.5" else []

    def get_historical_baseline(self, ward_code, pollutant, start_at, end_at, comparison_days):
        return [
            self.pm25.model_copy(update={"observed_at": start_at - timedelta(days=7), "value": 48.1}),
            self.pm25.model_copy(update={"observed_at": start_at - timedelta(days=14), "value": 51.3}),
        ]

    def get_current_weather(self, location_code=None):
        return self.weather

    def get_current_wind(self, location_code=None):
        return self.wind

    def get_weather_forecast(self, location_code, start_at, end_at):
        return [
            WeatherForecastReading(
                location_code=location_code,
                forecast_for=NOW + timedelta(hours=1),
                generated_at=NOW,
                temperature_c=25.0,
                relative_humidity_pct=52,
                wind_speed_kmh=14.2,
                wind_direction_degrees=95,
                provider="seeded",
            )
        ]

    def get_readings_for_time_window(self, station_code=None, ward_code=None, pollutant=None, start_at=None, end_at=None):
        return [self.pm25, self.no2]


def test_time_series_service_exposes_latest_station_state_with_quality_metadata() -> None:
    service = EnvironmentalTimeSeriesService(FakeTimeSeriesRepository())

    latest = service.get_latest_station_readings()

    assert latest[0].station_code == "BLR-CBD-AQ"
    assert latest[0].data_quality_status == "valid"
    assert [reading.pollutant for reading in latest[0].readings] == ["PM2.5", "NO2"]


def test_time_series_service_exposes_requested_history_methods() -> None:
    service = EnvironmentalTimeSeriesService(FakeTimeSeriesRepository())

    assert service.get_station_history("BLR-CBD-AQ", NOW - timedelta(hours=1), NOW)
    assert service.get_ward_aqi_history("BLR-W-001", NOW - timedelta(hours=1), NOW)[0].pollutant == "AQI"
    assert service.get_ward_pollutant_history("BLR-W-001", "PM2.5", NOW - timedelta(hours=1), NOW)[0].pollutant == "PM2.5"
    baseline = service.get_historical_baseline("BLR-W-001", "PM2.5", NOW - timedelta(hours=1), NOW)
    assert len(baseline.readings) == 2
    assert baseline.average_value == 49.7
    assert service.get_readings_for_time_window(ward_code="BLR-W-001", start_at=NOW - timedelta(hours=1), end_at=NOW)


def test_time_series_service_exposes_weather_wind_and_forecast() -> None:
    service = EnvironmentalTimeSeriesService(FakeTimeSeriesRepository())

    assert service.get_current_weather().temperature_c == 24.2
    assert service.get_current_wind().wind_direction_degrees == 92
    assert service.get_weather_forecast("BLR-CENTRE", NOW, NOW + timedelta(hours=2))[0].provider == "seeded"

