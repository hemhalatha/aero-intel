from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Protocol

from app.geo_master.schemas import GeoPoint

from .schemas import (
    AirQualityReadingDTO,
    EnvironmentalIngestionBatch,
    EnvironmentalNormalizationResult,
    NormalizedAirQualityReading,
    RejectedEnvironmentalRecord,
)


@dataclass(frozen=True)
class StationMapping:
    provider: str
    external_station_id: str
    internal_station_code: str
    station_name: str
    city: str
    state: str
    latitude: float | None = None
    longitude: float | None = None
    ward_code: str | None = None


class WardResolver(Protocol):
    def resolve_ward_code(
        self,
        *,
        station_code: str,
        point: GeoPoint | None,
        mapping: StationMapping | None,
    ) -> str | None:
        ...


class StaticWardResolver:
    def __init__(self, ward_codes_by_station: dict[str, str]) -> None:
        self.ward_codes_by_station = ward_codes_by_station

    def resolve_ward_code(
        self,
        *,
        station_code: str,
        point: GeoPoint | None,
        mapping: StationMapping | None,
    ) -> str | None:
        if mapping and mapping.ward_code:
            return mapping.ward_code
        return self.ward_codes_by_station.get(station_code)


class GeoMasterWardResolver:
    def __init__(self, geo_service) -> None:
        self.geo_service = geo_service

    def resolve_ward_code(
        self,
        *,
        station_code: str,
        point: GeoPoint | None,
        mapping: StationMapping | None,
    ) -> str | None:
        if mapping and mapping.ward_code:
            return mapping.ward_code
        if point is None:
            return None
        ward = self.geo_service.find_ward_containing_point(point)
        return getattr(ward, "code", None) if ward else None


class EnvironmentalDataNormalizer:
    def __init__(
        self,
        station_mappings: list[StationMapping],
        ward_resolver: WardResolver,
        default_timezone=UTC,
    ) -> None:
        self.station_mappings = {
            (mapping.provider, mapping.external_station_id): mapping
            for mapping in station_mappings
        }
        self.ward_resolver = ward_resolver
        self.default_timezone = default_timezone

    def normalize(self, batch: EnvironmentalIngestionBatch) -> EnvironmentalNormalizationResult:
        result = EnvironmentalNormalizationResult()
        seen: set[tuple[str, datetime, str, str]] = set()
        for reading in batch.air_quality_readings:
            rejected = self._validate_reading(reading)
            if rejected is not None:
                result.rejected_records.append(rejected)
                continue

            normalized = self._normalize_reading(reading)
            duplicate_key = (
                normalized.station_code,
                normalized.observed_at,
                normalized.pollutant,
                normalized.source_code,
            )
            if duplicate_key in seen:
                result.rejected_records.append(self._reject(reading, "duplicate_reading"))
                continue

            seen.add(duplicate_key)
            result.accepted_air_quality_readings.append(normalized)
        return result

    def _validate_reading(self, reading: AirQualityReadingDTO) -> RejectedEnvironmentalRecord | None:
        if not reading.pollutant:
            return self._reject(reading, "missing_pollutant")
        if reading.value is None:
            return self._reject(reading, "missing_pollutant_value")
        if reading.value < 0:
            return self._reject(reading, "negative_pollutant_value")
        if reading.latitude is not None and not -90 <= reading.latitude <= 90:
            return self._reject(reading, "invalid_latitude")
        if reading.longitude is not None and not -180 <= reading.longitude <= 180:
            return self._reject(reading, "invalid_longitude")
        return None

    def _normalize_reading(self, reading: AirQualityReadingDTO) -> NormalizedAirQualityReading:
        mapping = self.station_mappings.get((reading.provider, reading.provider_station_id))
        station_code = mapping.internal_station_code if mapping else reading.provider_station_id
        latitude = reading.latitude if reading.latitude is not None else (mapping.latitude if mapping else None)
        longitude = reading.longitude if reading.longitude is not None else (mapping.longitude if mapping else None)
        point = GeoPoint(latitude=latitude, longitude=longitude) if latitude is not None and longitude is not None else None
        ward_code = self.ward_resolver.resolve_ward_code(
            station_code=station_code,
            point=point,
            mapping=mapping,
        )

        return NormalizedAirQualityReading(
            source_code=reading.provider,
            provider=reading.provider,
            external_station_id=reading.provider_station_id,
            station_code=station_code,
            station_name=mapping.station_name if mapping else reading.station_name,
            city=mapping.city if mapping else "Unknown",
            state=mapping.state if mapping else "Unknown",
            ward_code=ward_code,
            observed_at=self._to_utc(reading.observed_at),
            pollutant=self._normalize_pollutant(reading.pollutant),
            value=float(reading.value),
            unit=self._normalize_unit(reading.unit),
            data_quality_status=self._quality_status(reading, mapping, ward_code),
            raw_payload=reading.raw_payload,
        )

    def _quality_status(
        self,
        reading: AirQualityReadingDTO,
        mapping: StationMapping | None,
        ward_code: str | None,
    ) -> str:
        if mapping is None or ward_code is None or reading.latitude is None or reading.longitude is None:
            return "incomplete"
        if self._normalize_pollutant(reading.pollutant) == "AQI" and reading.value > 500:
            return "suspect"
        return "valid"

    def _to_utc(self, value: datetime) -> datetime:
        if value.tzinfo is None:
            value = value.replace(tzinfo=self.default_timezone)
        return value.astimezone(UTC)

    @staticmethod
    def _normalize_pollutant(value: str) -> str:
        mapping = {
            "aqi": "AQI",
            "pm25": "PM2.5",
            "pm2.5": "PM2.5",
            "pm10": "PM10",
            "no": "NO",
            "no2": "NO2",
            "nox": "NOx",
            "nh3": "NH3",
            "so2": "SO2",
            "co": "CO",
            "o3": "Ozone",
            "ozone": "Ozone",
            "benzene": "Benzene",
        }
        return mapping.get(value.strip().lower(), value.strip())

    @staticmethod
    def _normalize_unit(value: str) -> str:
        return value.replace("µ", "u").replace("³", "3").strip()

    @staticmethod
    def _reject(reading: AirQualityReadingDTO, reason: str) -> RejectedEnvironmentalRecord:
        return RejectedEnvironmentalRecord(
            provider=reading.provider,
            external_station_id=reading.provider_station_id,
            observed_at=reading.observed_at,
            pollutant=reading.pollutant,
            reason=reason,
            raw_payload=reading.raw_payload,
        )
