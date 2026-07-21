import json
from collections.abc import Callable, Iterable
from datetime import datetime
from typing import Any, Protocol
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from .schemas import (
    AirQualityReadingDTO,
    ControlledScenarioDTO,
    EnvironmentalIngestionBatch,
    WeatherObservationDTO,
    WindObservationDTO,
)
from .seed_loader import build_seed_records, load_seed_fixture

JsonFetcher = Callable[[str, dict[str, str] | None], dict[str, Any]]


class EnvironmentalDataAdapter(Protocol):
    provider_name: str

    def fetch(self) -> EnvironmentalIngestionBatch:
        ...


def fetch_json(url: str, headers: dict[str, str] | None = None, timeout_seconds: int = 15) -> dict[str, Any]:
    request = Request(url, headers=headers or {})
    with urlopen(request, timeout=timeout_seconds) as response:
        return json.loads(response.read().decode("utf-8"))


def _parse_datetime(value: str) -> datetime:
    normalized = value.replace("Z", "+00:00")
    return datetime.fromisoformat(normalized)


def _normalize_pollutant(value: str) -> str:
    mapping = {
        "pm25": "PM2.5",
        "pm2.5": "PM2.5",
        "pm10": "PM10",
        "no2": "NO2",
        "nox": "NOx",
        "so2": "SO2",
        "co": "CO",
        "o3": "Ozone",
    }
    return mapping.get(value.lower(), value)


def _normalize_unit(value: str | None) -> str:
    if not value:
        return "unknown"
    return value.replace("µ", "u").replace("³", "3")


class OpenAQReadingsAdapter:
    provider_name = "openaq"

    def __init__(
        self,
        url: str | None = None,
        api_key: str | None = None,
        payload: dict[str, Any] | None = None,
        fetcher: JsonFetcher = fetch_json,
    ) -> None:
        self.url = url
        self.api_key = api_key
        self.payload = payload
        self.fetcher = fetcher

    def fetch(self) -> EnvironmentalIngestionBatch:
        payload = self.payload or self._fetch_payload()
        readings = [self._to_reading(result) for result in payload.get("results", [])]
        return EnvironmentalIngestionBatch(provider=self.provider_name, air_quality_readings=readings)

    def _fetch_payload(self) -> dict[str, Any]:
        if self.url is None:
            raise RuntimeError("OpenAQ adapter requires a URL or injected payload.")
        headers = {"X-API-Key": self.api_key} if self.api_key else None
        return self.fetcher(self.url, headers)

    def _to_reading(self, result: dict[str, Any]) -> AirQualityReadingDTO:
        parameter = result.get("parameter") or {}
        coordinates = result.get("coordinates") or {}
        location = result.get("location") or {}
        timestamp = result.get("datetime", {}).get("utc") or result.get("date", {}).get("utc") or result["datetime"]
        return AirQualityReadingDTO(
            provider=self.provider_name,
            provider_station_id=str(result.get("locationsId") or result.get("locationId") or result.get("location_id")),
            station_name=location.get("name") or result.get("location") or "Unknown OpenAQ station",
            observed_at=_parse_datetime(timestamp),
            pollutant=_normalize_pollutant(str(parameter.get("name") or result.get("parameter"))),
            value=float(result["value"]),
            unit=_normalize_unit(parameter.get("units") or result.get("unit")),
            latitude=coordinates.get("latitude"),
            longitude=coordinates.get("longitude"),
            raw_payload=result,
        )


class OpenMeteoWeatherAdapter:
    provider_name = "open_meteo"

    def __init__(
        self,
        latitude: float | None = None,
        longitude: float | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
        payload: dict[str, Any] | None = None,
        fetcher: JsonFetcher = fetch_json,
    ) -> None:
        self.latitude = latitude
        self.longitude = longitude
        self.start_date = start_date
        self.end_date = end_date
        self.payload = payload
        self.fetcher = fetcher

    def fetch(self) -> EnvironmentalIngestionBatch:
        payload = self.payload or self._fetch_payload()
        observations = [
            WeatherObservationDTO(
                provider=self.provider_name,
                location_code=self._location_code(payload),
                observed_at=_parse_datetime(timestamp),
                temperature_c=_value_at(payload, "temperature_2m", index),
                relative_humidity_pct=_value_at(payload, "relative_humidity_2m", index),
                latitude=float(payload["latitude"]),
                longitude=float(payload["longitude"]),
                raw_payload={"time": timestamp, "timezone": payload.get("timezone")},
            )
            for index, timestamp in enumerate(payload.get("hourly", {}).get("time", []))
        ]
        return EnvironmentalIngestionBatch(provider=self.provider_name, weather_observations=observations)

    def _fetch_payload(self) -> dict[str, Any]:
        if self.latitude is None or self.longitude is None or self.start_date is None or self.end_date is None:
            raise RuntimeError("Open-Meteo weather adapter requires coordinates and date range or injected payload.")
        query = urlencode(
            {
                "latitude": self.latitude,
                "longitude": self.longitude,
                "start_date": self.start_date,
                "end_date": self.end_date,
                "hourly": "temperature_2m,relative_humidity_2m,wind_speed_10m,wind_direction_10m",
                "timezone": "Asia/Kolkata",
            }
        )
        return self.fetcher(f"https://archive-api.open-meteo.com/v1/archive?{query}", None)

    @staticmethod
    def _location_code(payload: dict[str, Any]) -> str:
        return f"open_meteo:{payload['latitude']}:{payload['longitude']}"


class OpenMeteoWindAdapter(OpenMeteoWeatherAdapter):
    def fetch(self) -> EnvironmentalIngestionBatch:
        payload = self.payload or self._fetch_payload()
        observations = [
            WindObservationDTO(
                provider=self.provider_name,
                location_code=self._location_code(payload),
                observed_at=_parse_datetime(timestamp),
                wind_speed_kmh=_value_at(payload, "wind_speed_10m", index),
                wind_direction_degrees=_value_at(payload, "wind_direction_10m", index),
                latitude=float(payload["latitude"]),
                longitude=float(payload["longitude"]),
                raw_payload={"time": timestamp, "timezone": payload.get("timezone")},
            )
            for index, timestamp in enumerate(payload.get("hourly", {}).get("time", []))
        ]
        return EnvironmentalIngestionBatch(provider=self.provider_name, wind_observations=observations)


class SeededEnvironmentalDataAdapter:
    provider_name = "seeded"

    def fetch(self) -> EnvironmentalIngestionBatch:
        records = build_seed_records(load_seed_fixture())
        return EnvironmentalIngestionBatch(
            provider=self.provider_name,
            air_quality_readings=[
                AirQualityReadingDTO(
                    provider=reading.source_code,
                    provider_station_id=reading.station_code,
                    station_name=reading.station_name,
                    observed_at=reading.observed_at,
                    pollutant=reading.pollutant,
                    value=reading.value,
                    unit=reading.unit,
                    raw_payload=reading.raw_payload,
                )
                for reading in records.air_quality_readings
            ],
            weather_observations=[
                WeatherObservationDTO(
                    provider=observation.source_code,
                    location_code=observation.location_code,
                    observed_at=observation.observed_at,
                    temperature_c=observation.temperature_c,
                    relative_humidity_pct=observation.relative_humidity_pct,
                    latitude=observation.latitude,
                    longitude=observation.longitude,
                    raw_payload=observation.raw_payload,
                )
                for observation in records.weather_observations
            ],
            wind_observations=[
                WindObservationDTO(
                    provider=observation.source_code,
                    location_code=observation.location_code,
                    observed_at=observation.observed_at,
                    wind_speed_kmh=observation.wind_speed_kmh,
                    wind_direction_degrees=observation.wind_direction_degrees,
                    latitude=observation.latitude,
                    longitude=observation.longitude,
                    raw_payload=observation.raw_payload,
                )
                for observation in records.weather_observations
                if observation.wind_speed_kmh is not None or observation.wind_direction_degrees is not None
            ],
            controlled_scenarios=[
                ControlledScenarioDTO(
                    provider=scenario.source_code,
                    scenario_key=scenario.scenario_key,
                    title=scenario.title,
                    category=scenario.category,
                    city=scenario.city,
                    ward_code=scenario.ward_code,
                    station_code=scenario.station_code,
                    starts_at=scenario.starts_at,
                    ends_at=scenario.ends_at,
                    severity=scenario.severity,
                    description=scenario.description,
                    evidence=scenario.evidence,
                )
                for scenario in records.controlled_scenarios
            ],
        )


class EnvironmentalIngestionService:
    def __init__(
        self,
        primary_adapters: Iterable[EnvironmentalDataAdapter],
        fallback_adapter: EnvironmentalDataAdapter,
    ) -> None:
        self.primary_adapters = list(primary_adapters)
        self.fallback_adapter = fallback_adapter

    def ingest(self) -> EnvironmentalIngestionBatch:
        errors: list[str] = []
        batches: list[EnvironmentalIngestionBatch] = []
        for adapter in self.primary_adapters:
            try:
                batches.append(adapter.fetch())
            except Exception as exc:
                errors.append(f"{adapter.provider_name}: {exc}")

        if batches:
            return _merge_batches(provider=";".join(batch.provider for batch in batches), batches=batches, errors=errors)

        fallback = self.fallback_adapter.fetch()
        fallback.provider = "seeded-fallback"
        fallback.used_fallback = True
        fallback.errors = errors
        return fallback


def _value_at(payload: dict[str, Any], key: str, index: int) -> float | None:
    values = payload.get("hourly", {}).get(key, [])
    value = values[index] if index < len(values) else None
    return None if value is None else float(value)


def _merge_batches(
    provider: str,
    batches: list[EnvironmentalIngestionBatch],
    errors: list[str],
) -> EnvironmentalIngestionBatch:
    merged = EnvironmentalIngestionBatch(provider=provider, errors=errors)
    for batch in batches:
        merged.air_quality_readings.extend(batch.air_quality_readings)
        merged.weather_observations.extend(batch.weather_observations)
        merged.wind_observations.extend(batch.wind_observations)
        merged.controlled_scenarios.extend(batch.controlled_scenarios)
    return merged
