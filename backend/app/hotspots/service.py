from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta

from app.aqi.classifier import AQIClassifier
from app.aqi.config import CPCB_AQI_BANDS
from app.environmental_data.time_series_schemas import HistoricalBaseline, StationLatestState
from app.sensor_health.schemas import SensorHealthSnapshot

from .schemas import AlertLevel, HotspotCandidate, HotspotSeverity, HotspotTrigger


@dataclass(frozen=True)
class HotspotDetectionRules:
    aqi_threshold: float = 200
    baseline_deviation_ratio: float = 0.35
    pollutant_spike_ratio: float = 1.5
    min_pollutant_spike_value: dict[str, float] = field(
        default_factory=lambda: {
            "PM2.5": 90,
            "PM10": 180,
            "NO2": 100,
            "SO2": 80,
            "CO": 4,
            "O3": 120,
            "Ozone": 120,
        }
    )
    baseline_window_hours: int = 24
    baseline_comparison_days: int = 28
    min_data_quality_confidence: float = 0.75


class HotspotDetectionService:
    def __init__(
        self,
        time_series_service,
        sensor_health_service,
        rules: HotspotDetectionRules | None = None,
        aqi_classifier: AQIClassifier | None = None,
    ) -> None:
        self.time_series_service = time_series_service
        self.sensor_health_service = sensor_health_service
        self.rules = rules or HotspotDetectionRules()
        self.aqi_classifier = aqi_classifier or AQIClassifier(CPCB_AQI_BANDS)

    def detect_hotspot_candidates(self, now: datetime | None = None) -> list[HotspotCandidate]:
        evaluated_at = now or datetime.now(UTC)
        candidates: list[HotspotCandidate] = []

        for station_state in self.time_series_service.get_latest_station_readings():
            if not station_state.ward_code or not self._station_state_is_valid(station_state):
                continue

            sensor_health = self.sensor_health_service.get_station_health(station_state.station_code)
            if not self._sensor_is_reliable(sensor_health):
                continue

            candidate = self._candidate_for_station(station_state, sensor_health, evaluated_at)
            if candidate is not None:
                candidates.append(candidate)

        return sorted(candidates, key=lambda item: (item.anomaly_score, item.aqi), reverse=True)

    def _candidate_for_station(
        self,
        station_state: StationLatestState,
        sensor_health: SensorHealthSnapshot,
        evaluated_at: datetime,
    ) -> HotspotCandidate | None:
        snapshot = {
            reading.pollutant: reading.value
            for reading in station_state.readings
            if reading.data_quality_status == "valid"
        }
        aqi = snapshot.get("AQI")
        if aqi is None:
            return None

        trigger_reasons: list[HotspotTrigger] = []
        trigger_scores: list[float] = []

        if aqi >= self.rules.aqi_threshold:
            trigger_reasons.append(HotspotTrigger.AQI_THRESHOLD)
            trigger_scores.append(aqi / self.rules.aqi_threshold)

        baseline = self._baseline(station_state.ward_code, "AQI", evaluated_at)
        if baseline.average_value and baseline.average_value > 0:
            deviation_score = aqi / baseline.average_value
            if deviation_score >= 1 + self.rules.baseline_deviation_ratio:
                trigger_reasons.append(HotspotTrigger.BASELINE_DEVIATION)
                trigger_scores.append(deviation_score)

        pollutant_spike_score = self._pollutant_spike_score(station_state.ward_code, snapshot, evaluated_at)
        if pollutant_spike_score is not None:
            trigger_reasons.append(HotspotTrigger.POLLUTANT_SPIKE)
            trigger_scores.append(pollutant_spike_score)

        if not trigger_reasons:
            return None

        anomaly_score = round(max(trigger_scores), 2)
        severity = self._severity(aqi, trigger_reasons, anomaly_score)
        return HotspotCandidate(
            ward_code=station_state.ward_code,
            station_code=station_state.station_code,
            station_name=station_state.station_name,
            aqi=aqi,
            pollutant_snapshot=snapshot,
            severity=severity,
            alert_level=self._alert_level(severity),
            trigger_reasons=trigger_reasons,
            anomaly_score=anomaly_score,
            observed_at=station_state.observed_at,
            data_quality_confidence=sensor_health.data_quality_score,
        )

    def _pollutant_spike_score(
        self,
        ward_code: str,
        snapshot: dict[str, float],
        evaluated_at: datetime,
    ) -> float | None:
        spike_scores: list[float] = []
        for pollutant, minimum_value in self.rules.min_pollutant_spike_value.items():
            value = snapshot.get(pollutant)
            if value is None or value < minimum_value:
                continue

            baseline = self._baseline(ward_code, pollutant, evaluated_at)
            if not baseline.average_value or baseline.average_value <= 0:
                continue

            spike_score = value / baseline.average_value
            if spike_score >= self.rules.pollutant_spike_ratio:
                spike_scores.append(spike_score)

        if not spike_scores:
            return None
        return max(spike_scores)

    def _baseline(self, ward_code: str, pollutant: str, evaluated_at: datetime) -> HistoricalBaseline:
        return self.time_series_service.get_historical_baseline(
            ward_code=ward_code,
            pollutant=pollutant,
            start_at=evaluated_at - timedelta(hours=self.rules.baseline_window_hours),
            end_at=evaluated_at,
            comparison_days=self.rules.baseline_comparison_days,
        )

    def _sensor_is_reliable(self, sensor_health: SensorHealthSnapshot | None) -> bool:
        if sensor_health is None:
            return False
        return self.sensor_health_service.is_reading_reliable(
            sensor_health.status,
            sensor_health.data_quality_score,
        ) and sensor_health.data_quality_score >= self.rules.min_data_quality_confidence

    @staticmethod
    def _station_state_is_valid(station_state: StationLatestState) -> bool:
        return station_state.data_quality_status == "valid" and any(
            reading.data_quality_status == "valid" for reading in station_state.readings
        )

    def _severity(
        self,
        aqi: float,
        trigger_reasons: list[HotspotTrigger],
        anomaly_score: float,
    ) -> HotspotSeverity:
        classification = self.aqi_classifier.classify(aqi)
        if classification.severity_rank >= 6 or anomaly_score >= 2.75:
            return HotspotSeverity.CRITICAL
        if classification.severity_rank >= 4 or len(trigger_reasons) >= 2 or anomaly_score >= 2:
            return HotspotSeverity.HIGH
        if classification.severity_rank >= 3 or anomaly_score >= 1.5:
            return HotspotSeverity.MEDIUM
        return HotspotSeverity.LOW

    @staticmethod
    def _alert_level(severity: HotspotSeverity) -> AlertLevel:
        if severity == HotspotSeverity.CRITICAL:
            return AlertLevel.EMERGENCY
        if severity == HotspotSeverity.HIGH:
            return AlertLevel.WARNING
        return AlertLevel.WATCH
