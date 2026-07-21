from datetime import UTC, datetime, timedelta

from app.environmental_data.time_series_schemas import HistoricalBaseline, PollutantReading, StationLatestState
from app.hotspots.schemas import AlertLevel, HotspotSeverity, HotspotTrigger
from app.hotspots.service import HotspotDetectionRules, HotspotDetectionService
from app.sensor_health.schemas import SensorHealthSnapshot, SensorHealthStatus


NOW = datetime(2025, 1, 15, 12, tzinfo=UTC)


def reading(
    station_code: str,
    ward_code: str,
    pollutant: str,
    value: float,
    observed_at: datetime = NOW,
    quality: str = "valid",
) -> PollutantReading:
    return PollutantReading(
        station_code=station_code,
        station_name=f"{station_code} Station",
        ward_code=ward_code,
        observed_at=observed_at,
        pollutant=pollutant,
        value=value,
        unit="index" if pollutant == "AQI" else "ug/m3",
        data_quality_status=quality,
    )


class FakeTimeSeriesService:
    def __init__(self, states: list[StationLatestState], baselines: dict[tuple[str, str], float]) -> None:
        self.states = states
        self.baselines = baselines

    def get_latest_station_readings(self) -> list[StationLatestState]:
        return self.states

    def get_historical_baseline(
        self,
        ward_code: str,
        pollutant: str,
        start_at: datetime,
        end_at: datetime,
        comparison_days: int = 28,
    ) -> HistoricalBaseline:
        return HistoricalBaseline(
            ward_code=ward_code,
            pollutant=pollutant,
            comparison_days=comparison_days,
            readings=[],
            average_value=self.baselines.get((ward_code, pollutant)),
        )


class FakeSensorHealthService:
    def __init__(self, statuses: dict[str, SensorHealthSnapshot]) -> None:
        self.statuses = statuses

    def get_station_health(self, station_code: str) -> SensorHealthSnapshot | None:
        return self.statuses.get(station_code)

    def is_reading_reliable(self, status: SensorHealthStatus | str, data_quality_score: float) -> bool:
        return SensorHealthStatus(status) == SensorHealthStatus.ONLINE and data_quality_score >= 0.75


def health(station_code: str, score: float = 0.92, status: SensorHealthStatus = SensorHealthStatus.ONLINE):
    return SensorHealthSnapshot(
        station_code=station_code,
        station_name=f"{station_code} Station",
        ward_code="BLR-W-001",
        status=status,
        data_quality_score=score,
        last_reading_at=NOW,
        evaluated_at=NOW,
        is_reliable=status == SensorHealthStatus.ONLINE and score >= 0.75,
    )


def state(station_code: str, ward_code: str, readings: list[PollutantReading], quality: str = "valid") -> StationLatestState:
    return StationLatestState(
        station_code=station_code,
        station_name=f"{station_code} Station",
        ward_code=ward_code,
        observed_at=NOW,
        readings=readings,
        data_quality_status=quality,
    )


def test_detects_threshold_and_baseline_hotspot_candidate() -> None:
    station_state = state(
        "BLR-CBD-AQ",
        "BLR-W-001",
        [
            reading("BLR-CBD-AQ", "BLR-W-001", "AQI", 235),
            reading("BLR-CBD-AQ", "BLR-W-001", "PM2.5", 118),
            reading("BLR-CBD-AQ", "BLR-W-001", "NO2", 44),
        ],
    )
    service = HotspotDetectionService(
        time_series_service=FakeTimeSeriesService(
            [station_state],
            {("BLR-W-001", "AQI"): 125, ("BLR-W-001", "PM2.5"): 72},
        ),
        sensor_health_service=FakeSensorHealthService({"BLR-CBD-AQ": health("BLR-CBD-AQ", score=0.88)}),
        rules=HotspotDetectionRules(aqi_threshold=200, baseline_deviation_ratio=0.5),
    )

    candidates = service.detect_hotspot_candidates(now=NOW)

    assert len(candidates) == 1
    candidate = candidates[0]
    assert candidate.ward_code == "BLR-W-001"
    assert candidate.station_code == "BLR-CBD-AQ"
    assert candidate.aqi == 235
    assert candidate.pollutant_snapshot["PM2.5"] == 118
    assert candidate.severity == HotspotSeverity.HIGH
    assert candidate.alert_level == AlertLevel.WARNING
    assert HotspotTrigger.AQI_THRESHOLD in candidate.trigger_reasons
    assert HotspotTrigger.BASELINE_DEVIATION in candidate.trigger_reasons
    assert candidate.anomaly_score == 1.88
    assert candidate.observed_at == NOW
    assert candidate.data_quality_confidence == 0.88


def test_detects_pollutant_specific_spike_without_aqi_threshold_crossing() -> None:
    station_state = state(
        "BLR-NORTH-AQ",
        "BLR-W-009",
        [
            reading("BLR-NORTH-AQ", "BLR-W-009", "AQI", 160),
            reading("BLR-NORTH-AQ", "BLR-W-009", "NO2", 140),
        ],
    )
    service = HotspotDetectionService(
        time_series_service=FakeTimeSeriesService(
            [station_state],
            {("BLR-W-009", "AQI"): 145, ("BLR-W-009", "NO2"): 55},
        ),
        sensor_health_service=FakeSensorHealthService({"BLR-NORTH-AQ": health("BLR-NORTH-AQ")}),
    )

    candidates = service.detect_hotspot_candidates(now=NOW)

    assert len(candidates) == 1
    assert candidates[0].trigger_reasons == [HotspotTrigger.POLLUTANT_SPIKE]
    assert candidates[0].severity == HotspotSeverity.HIGH
    assert candidates[0].alert_level == AlertLevel.WARNING


def test_ignores_unreliable_or_suspect_station_observations() -> None:
    reliable_state = state(
        "BLR-GOOD-AQ",
        "BLR-W-003",
        [reading("BLR-GOOD-AQ", "BLR-W-003", "AQI", 130), reading("BLR-GOOD-AQ", "BLR-W-003", "PM10", 120)],
    )
    unreliable_state = state(
        "BLR-BAD-AQ",
        "BLR-W-004",
        [reading("BLR-BAD-AQ", "BLR-W-004", "AQI", 450), reading("BLR-BAD-AQ", "BLR-W-004", "PM2.5", 300)],
    )
    suspect_state = state(
        "BLR-SUSPECT-AQ",
        "BLR-W-005",
        [reading("BLR-SUSPECT-AQ", "BLR-W-005", "AQI", 430, quality="suspect")],
        quality="suspect",
    )
    service = HotspotDetectionService(
        time_series_service=FakeTimeSeriesService([reliable_state, unreliable_state, suspect_state], {}),
        sensor_health_service=FakeSensorHealthService(
            {
                "BLR-GOOD-AQ": health("BLR-GOOD-AQ"),
                "BLR-BAD-AQ": health("BLR-BAD-AQ", score=0.4, status=SensorHealthStatus.DEGRADED),
                "BLR-SUSPECT-AQ": health("BLR-SUSPECT-AQ"),
            }
        ),
    )

    candidates = service.detect_hotspot_candidates(now=NOW)

    assert candidates == []
