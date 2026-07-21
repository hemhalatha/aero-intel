from datetime import UTC, datetime, timedelta

from app.environmental_data.time_series_schemas import PollutantReading, StationLatestState
from app.sensor_health.schemas import SensorHealthStatus
from app.sensor_health.service import SensorHealthRules, SensorHealthService


NOW = datetime(2025, 1, 15, 12, tzinfo=UTC)


def reading(pollutant: str, value: float, observed_at: datetime = NOW, quality: str = "valid") -> PollutantReading:
    return PollutantReading(
        station_code="BLR-CBD-AQ",
        station_name="CBD Air Quality Station",
        ward_code="BLR-W-001",
        observed_at=observed_at,
        pollutant=pollutant,
        value=value,
        unit="ug/m3",
        data_quality_status=quality,
    )


def state(readings: list[PollutantReading], observed_at: datetime = NOW) -> StationLatestState:
    return StationLatestState(
        station_code="BLR-CBD-AQ",
        station_name="CBD Air Quality Station",
        ward_code="BLR-W-001",
        observed_at=observed_at,
        readings=readings,
        data_quality_status="valid",
    )



def complete_readings(observed_at: datetime = NOW) -> list[PollutantReading]:
    return [
        reading("PM2.5", 42, observed_at),
        reading("PM10", 88, observed_at),
        reading("NO2", 21, observed_at),
        reading("SO2", 8, observed_at),
        reading("CO", 0.9, observed_at),
        reading("Ozone", 34, observed_at),
    ]

def service() -> SensorHealthService:
    return SensorHealthService(
        repository=None,
        rules=SensorHealthRules(
            online_after_minutes=30,
            delayed_after_minutes=90,
            repeated_identical_count=3,
        ),
    )


def test_classifies_online_station_with_complete_recent_valid_readings() -> None:
    result = service().evaluate_station(
        state([
            reading("PM2.5", 42),
            reading("PM10", 88),
            reading("NO2", 21),
            reading("SO2", 8),
            reading("CO", 0.9, quality="valid"),
            reading("Ozone", 34),
        ]),
        recent_history=[],
        evaluated_at=NOW + timedelta(minutes=10),
    )

    assert result.status == SensorHealthStatus.ONLINE
    assert result.data_quality_score == 1.0
    assert result.is_reliable is True


def test_classifies_delayed_and_offline_by_last_reading_age() -> None:
    delayed = service().evaluate_station(
        state(complete_readings(NOW - timedelta(minutes=45)), observed_at=NOW - timedelta(minutes=45)),
        recent_history=[],
        evaluated_at=NOW,
    )
    offline = service().evaluate_station(
        state(complete_readings(NOW - timedelta(hours=3)), observed_at=NOW - timedelta(hours=3)),
        recent_history=[],
        evaluated_at=NOW,
    )

    assert delayed.status == SensorHealthStatus.DELAYED
    assert offline.status == SensorHealthStatus.OFFLINE


def test_classifies_degraded_for_missing_pollutants_invalid_quality_and_repeated_values() -> None:
    result = service().evaluate_station(
        state([reading("PM2.5", 99, quality="suspect")]),
        recent_history=[reading("PM2.5", 99, NOW - timedelta(minutes=i * 5)) for i in range(3)],
        evaluated_at=NOW,
    )

    assert result.status == SensorHealthStatus.DEGRADED
    assert "missing_pollutants" in result.reasons
    assert "invalid_or_suspect_values" in result.reasons
    assert "repeated_identical_readings" in result.reasons
    assert result.data_quality_score < 0.7


def test_reliability_gate_rejects_unreliable_statuses_and_low_scores() -> None:
    health_service = service()

    assert health_service.is_reading_reliable(SensorHealthStatus.ONLINE, 0.9) is True
    assert health_service.is_reading_reliable(SensorHealthStatus.DEGRADED, 0.9) is False
    assert health_service.is_reading_reliable(SensorHealthStatus.ONLINE, 0.5) is False

