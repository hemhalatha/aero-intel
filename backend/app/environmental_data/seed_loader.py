import json
from pathlib import Path
from typing import Any

from .schemas import (
    AirQualityReadingSeed,
    ControlledScenarioSeed,
    EnvironmentalDataSourceSeed,
    PreparedEnvironmentalSeed,
    WeatherObservationSeed,
)

FIXTURE_PATH = Path(__file__).resolve().parents[2] / "data" / "environmental_seed.json"

POLLUTANT_FIELDS = {
    "PM2.5": ("pm25_ug_m3", "ug/m3"),
    "PM10": ("pm10_ug_m3", "ug/m3"),
    "NO": ("no_ug_m3", "ug/m3"),
    "NO2": ("no2_ug_m3", "ug/m3"),
    "NOx": ("nox_ppb", "ppb"),
    "NH3": ("nh3_ug_m3", "ug/m3"),
    "SO2": ("so2_ug_m3", "ug/m3"),
    "CO": ("co_mg_m3", "mg/m3"),
    "Ozone": ("ozone_ug_m3", "ug/m3"),
    "Benzene": ("benzene_ug_m3", "ug/m3"),
}


def load_seed_fixture(path: Path = FIXTURE_PATH) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def build_seed_records(fixture: dict[str, Any]) -> PreparedEnvironmentalSeed:
    sources = [EnvironmentalDataSourceSeed.model_validate(source) for source in fixture["sources"]]
    air_quality_readings = _build_air_quality_readings(fixture["air_quality_observations"])
    weather_observations = _build_weather_observations(fixture["weather_observations"])
    controlled_scenarios = [
        ControlledScenarioSeed.model_validate(scenario) for scenario in fixture["controlled_scenarios"]
    ]
    return PreparedEnvironmentalSeed(
        sources=sources,
        air_quality_readings=air_quality_readings,
        weather_observations=weather_observations,
        controlled_scenarios=controlled_scenarios,
    )


def _build_air_quality_readings(rows: list[dict[str, Any]]) -> list[AirQualityReadingSeed]:
    readings: list[AirQualityReadingSeed] = []
    for row in rows:
        for pollutant, (field_name, unit) in POLLUTANT_FIELDS.items():
            value = row.get(field_name)
            if value is None:
                continue
            readings.append(
                AirQualityReadingSeed(
                    source_code=row["source_code"],
                    station_code=row["station_code"],
                    station_name=row["station_name"],
                    city=row["city"],
                    state=row["state"],
                    observed_at=row["observed_at"],
                    pollutant=pollutant,
                    value=value,
                    unit=unit,
                    averaging_period=row.get("averaging_period", "15min"),
                    raw_payload=row,
                )
            )
    return readings


def _build_weather_observations(rows: list[dict[str, Any]]) -> list[WeatherObservationSeed]:
    return [WeatherObservationSeed.model_validate(row) for row in rows]
