from datetime import datetime

from app.environmental_data.adapters import (
    EnvironmentalDataAdapter,
    EnvironmentalIngestionService,
    OpenAQReadingsAdapter,
    OpenMeteoWeatherAdapter,
    OpenMeteoWindAdapter,
    SeededEnvironmentalDataAdapter,
)
from app.environmental_data.schemas import AirQualityReadingDTO, WeatherObservationDTO, WindObservationDTO


class FailingAdapter:
    provider_name = "failing-provider"

    def fetch(self):
        raise RuntimeError("provider unavailable")


def test_openaq_adapter_normalizes_provider_payload_to_common_aq_dtos() -> None:
    payload = {
        "results": [
            {
                "datetime": {"utc": "2025-01-15T06:00:00Z"},
                "value": 72.4,
                "parameter": {"name": "pm25", "units": "µg/m³"},
                "coordinates": {"latitude": 12.9716, "longitude": 77.5946},
                "locationsId": 123,
                "sensorsId": 456,
                "location": {"name": "CBD Monitor"},
            }
        ]
    }

    adapter = OpenAQReadingsAdapter(payload=payload)
    batch = adapter.fetch()

    assert batch.provider == "openaq"
    assert batch.air_quality_readings == [
        AirQualityReadingDTO(
            provider="openaq",
            provider_station_id="123",
            station_name="CBD Monitor",
            observed_at=datetime.fromisoformat("2025-01-15T06:00:00+00:00"),
            pollutant="PM2.5",
            value=72.4,
            unit="ug/m3",
            latitude=12.9716,
            longitude=77.5946,
            raw_payload=payload["results"][0],
        )
    ]


def test_open_meteo_adapters_normalize_weather_and_wind_payloads() -> None:
    payload = {
        "latitude": 12.970123,
        "longitude": 77.56364,
        "timezone": "Asia/Kolkata",
        "hourly": {
            "time": ["2025-01-15T00:00"],
            "temperature_2m": [17.8],
            "relative_humidity_2m": [83],
            "wind_speed_10m": [13.6],
            "wind_direction_10m": [82],
        },
    }

    weather_batch = OpenMeteoWeatherAdapter(payload=payload).fetch()
    wind_batch = OpenMeteoWindAdapter(payload=payload).fetch()

    assert weather_batch.weather_observations == [
        WeatherObservationDTO(
            provider="open_meteo",
            location_code="open_meteo:12.970123:77.56364",
            observed_at=datetime.fromisoformat("2025-01-15T00:00:00"),
            temperature_c=17.8,
            relative_humidity_pct=83,
            latitude=12.970123,
            longitude=77.56364,
            raw_payload={"time": "2025-01-15T00:00", "timezone": "Asia/Kolkata"},
        )
    ]
    assert wind_batch.wind_observations == [
        WindObservationDTO(
            provider="open_meteo",
            location_code="open_meteo:12.970123:77.56364",
            observed_at=datetime.fromisoformat("2025-01-15T00:00:00"),
            wind_speed_kmh=13.6,
            wind_direction_degrees=82,
            latitude=12.970123,
            longitude=77.56364,
            raw_payload={"time": "2025-01-15T00:00", "timezone": "Asia/Kolkata"},
        )
    ]


def test_ingestion_service_falls_back_to_seeded_data_when_provider_fails() -> None:
    fallback = SeededEnvironmentalDataAdapter()
    service = EnvironmentalIngestionService(primary_adapters=[FailingAdapter()], fallback_adapter=fallback)

    batch = service.ingest()

    assert batch.provider == "seeded-fallback"
    assert batch.used_fallback is True
    assert batch.air_quality_readings
    assert batch.weather_observations
    assert batch.wind_observations
    assert batch.controlled_scenarios


def test_adapters_share_common_interface() -> None:
    adapters: list[EnvironmentalDataAdapter] = [
        SeededEnvironmentalDataAdapter(),
        OpenAQReadingsAdapter(payload={"results": []}),
        OpenMeteoWeatherAdapter(payload={"latitude": 0, "longitude": 0, "hourly": {"time": []}}),
        OpenMeteoWindAdapter(payload={"latitude": 0, "longitude": 0, "hourly": {"time": []}}),
    ]

    assert [adapter.fetch().provider for adapter in adapters]
