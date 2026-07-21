from datetime import UTC, datetime

from app.environmental_data.normalization import (
    EnvironmentalDataNormalizer,
    StationMapping,
    StaticWardResolver,
)
from app.environmental_data.schemas import AirQualityReadingDTO, EnvironmentalIngestionBatch


def reading(**overrides):
    payload = {
        "provider": "openaq",
        "provider_station_id": "external-cbd",
        "station_name": "External CBD Station",
        "observed_at": datetime.fromisoformat("2025-01-15T11:30:00+05:30"),
        "pollutant": "pm25",
        "value": 72.4,
        "unit": "µg/m³",
        "latitude": 12.9716,
        "longitude": 77.5946,
        "raw_payload": {"provider_record_id": "abc-1"},
    }
    payload.update(overrides)
    return AirQualityReadingDTO.model_construct(**payload)


def test_normalizes_timestamp_station_ward_quality_and_units() -> None:
    normalizer = EnvironmentalDataNormalizer(
        station_mappings=[
            StationMapping(
                provider="openaq",
                external_station_id="external-cbd",
                internal_station_code="BLR-CBD-AQ",
                station_name="CBD Air Quality Station",
                city="Bengaluru",
                state="Karnataka",
            )
        ],
        ward_resolver=StaticWardResolver({"BLR-CBD-AQ": "BLR-W-001"}),
    )

    result = normalizer.normalize(EnvironmentalIngestionBatch(provider="openaq", air_quality_readings=[reading()]))

    assert len(result.accepted_air_quality_readings) == 1
    normalized = result.accepted_air_quality_readings[0]
    assert normalized.station_code == "BLR-CBD-AQ"
    assert normalized.external_station_id == "external-cbd"
    assert normalized.ward_code == "BLR-W-001"
    assert normalized.observed_at == datetime(2025, 1, 15, 6, 0, tzinfo=UTC)
    assert normalized.pollutant == "PM2.5"
    assert normalized.unit == "ug/m3"
    assert normalized.data_quality_status == "valid"


def test_rejects_negative_and_missing_pollutant_values() -> None:
    normalizer = EnvironmentalDataNormalizer(
        station_mappings=[],
        ward_resolver=StaticWardResolver({}),
    )
    batch = EnvironmentalIngestionBatch(
        provider="openaq",
        air_quality_readings=[
            reading(value=-1),
            reading(provider_station_id="missing-pollutant", pollutant=""),
            reading(provider_station_id="missing-value", value=None),
        ],
    )

    result = normalizer.normalize(batch)

    assert result.accepted_air_quality_readings == []
    assert [record.reason for record in result.rejected_records] == [
        "negative_pollutant_value",
        "missing_pollutant",
        "missing_pollutant_value",
    ]


def test_prevents_duplicate_readings_within_batch() -> None:
    normalizer = EnvironmentalDataNormalizer(
        station_mappings=[
            StationMapping(
                provider="openaq",
                external_station_id="external-cbd",
                internal_station_code="BLR-CBD-AQ",
                station_name="CBD Air Quality Station",
                city="Bengaluru",
                state="Karnataka",
            )
        ],
        ward_resolver=StaticWardResolver({"BLR-CBD-AQ": "BLR-W-001"}),
    )
    batch = EnvironmentalIngestionBatch(provider="openaq", air_quality_readings=[reading(), reading()])

    result = normalizer.normalize(batch)

    assert len(result.accepted_air_quality_readings) == 1
    assert len(result.rejected_records) == 1
    assert result.rejected_records[0].reason == "duplicate_reading"
