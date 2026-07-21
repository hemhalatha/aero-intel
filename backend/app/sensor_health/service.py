from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Protocol

from app.environmental_data.time_series_schemas import PollutantReading, StationLatestState

from .schemas import SensorHealthSnapshot, SensorHealthStatus


class SensorHealthRepositoryProtocol(Protocol):
    def get_current_statuses(self) -> list[SensorHealthSnapshot]:
        ...

    def get_current_status(self, station_code: str) -> SensorHealthSnapshot | None:
        ...

    def get_health_history(self, station_code: str) -> list[SensorHealthSnapshot]:
        ...

    def save_health_snapshot(self, snapshot: SensorHealthSnapshot) -> None:
        ...


@dataclass(frozen=True)
class SensorHealthRules:
    online_after_minutes: int = 30
    delayed_after_minutes: int = 90
    repeated_identical_count: int = 4
    reliable_score_threshold: float = 0.75
    required_pollutants: set[str] = field(
        default_factory=lambda: {"PM2.5", "PM10", "NO2", "SO2", "CO", "Ozone"}
    )
    pollutant_max_values: dict[str, float] = field(
        default_factory=lambda: {
            "AQI": 500,
            "PM2.5": 1000,
            "PM10": 1500,
            "NO2": 1000,
            "SO2": 1000,
            "CO": 50,
            "Ozone": 1000,
        }
    )


class SensorHealthService:
    def __init__(
        self,
        repository: SensorHealthRepositoryProtocol | None,
        rules: SensorHealthRules | None = None,
    ) -> None:
        self.repository = repository
        self.rules = rules or SensorHealthRules()

    def get_all_station_health(self) -> list[SensorHealthSnapshot]:
        if self.repository is None:
            raise RuntimeError("Sensor health repository is required for stored status lookup.")
        return self.repository.get_current_statuses()

    def get_station_health(self, station_code: str) -> SensorHealthSnapshot | None:
        if self.repository is None:
            raise RuntimeError("Sensor health repository is required for stored status lookup.")
        return self.repository.get_current_status(station_code)

    def get_station_health_history(self, station_code: str) -> list[SensorHealthSnapshot]:
        if self.repository is None:
            raise RuntimeError("Sensor health repository is required for history lookup.")
        return self.repository.get_health_history(station_code)

    def evaluate_station(
        self,
        station_state: StationLatestState,
        recent_history: list[PollutantReading],
        evaluated_at: datetime | None = None,
    ) -> SensorHealthSnapshot:
        evaluated_at = evaluated_at or datetime.now(UTC)
        age_minutes = self._age_minutes(station_state.observed_at, evaluated_at)
        latest_by_pollutant = {reading.pollutant: reading for reading in station_state.readings}
        missing = sorted(self.rules.required_pollutants - set(latest_by_pollutant))
        invalid = self._invalid_pollutants(station_state.readings)
        repeated = self._repeated_pollutants(recent_history)
        abnormal = self._abnormal_signals(station_state.readings, age_minutes)
        reasons = self._reasons(age_minutes, missing, invalid, repeated, abnormal)
        score = self._data_quality_score(age_minutes, missing, invalid, repeated, abnormal)
        status = self._status(age_minutes, missing, invalid, repeated, abnormal)
        reliable = self.is_reading_reliable(status, score)

        return SensorHealthSnapshot(
            station_code=station_state.station_code,
            station_name=station_state.station_name,
            ward_code=station_state.ward_code,
            status=status,
            data_quality_score=score,
            last_reading_at=station_state.observed_at,
            evaluated_at=evaluated_at,
            missing_pollutants=missing,
            invalid_pollutants=invalid,
            repeated_pollutants=repeated,
            abnormal_signals=abnormal,
            reasons=reasons,
            is_reliable=reliable,
        )

    def is_reading_reliable(self, status: SensorHealthStatus | str, data_quality_score: float) -> bool:
        normalized_status = SensorHealthStatus(status)
        return normalized_status == SensorHealthStatus.ONLINE and data_quality_score >= self.rules.reliable_score_threshold

    def _status(
        self,
        age_minutes: float,
        missing: list[str],
        invalid: list[str],
        repeated: list[str],
        abnormal: list[str],
    ) -> SensorHealthStatus:
        if age_minutes > self.rules.delayed_after_minutes:
            return SensorHealthStatus.OFFLINE
        if missing or invalid or repeated or abnormal:
            return SensorHealthStatus.DEGRADED
        if age_minutes > self.rules.online_after_minutes:
            return SensorHealthStatus.DELAYED
        return SensorHealthStatus.ONLINE

    def _data_quality_score(
        self,
        age_minutes: float,
        missing: list[str],
        invalid: list[str],
        repeated: list[str],
        abnormal: list[str],
    ) -> float:
        score = 1.0
        if age_minutes > self.rules.online_after_minutes:
            score -= 0.2
        if age_minutes > self.rules.delayed_after_minutes:
            score -= 0.45
        score -= min(len(missing) * 0.08, 0.4)
        score -= min(len(invalid) * 0.2, 0.5)
        score -= min(len(repeated) * 0.15, 0.3)
        score -= min(len(abnormal) * 0.15, 0.3)
        return round(max(score, 0), 2)

    def _invalid_pollutants(self, readings: list[PollutantReading]) -> list[str]:
        invalid: list[str] = []
        for reading in readings:
            max_value = self.rules.pollutant_max_values.get(reading.pollutant)
            if reading.value < 0:
                invalid.append(reading.pollutant)
            elif max_value is not None and reading.value > max_value:
                invalid.append(reading.pollutant)
            elif reading.data_quality_status != "valid":
                invalid.append(reading.pollutant)
        return sorted(set(invalid))

    def _repeated_pollutants(self, history: list[PollutantReading]) -> list[str]:
        by_pollutant: dict[str, list[PollutantReading]] = {}
        for reading in history:
            by_pollutant.setdefault(reading.pollutant, []).append(reading)

        repeated: list[str] = []
        for pollutant, readings in by_pollutant.items():
            ordered = sorted(readings, key=lambda item: item.observed_at, reverse=True)
            recent = ordered[: self.rules.repeated_identical_count]
            if len(recent) == self.rules.repeated_identical_count and len({item.value for item in recent}) == 1:
                repeated.append(pollutant)
        return sorted(repeated)

    def _abnormal_signals(self, readings: list[PollutantReading], age_minutes: float) -> list[str]:
        signals: list[str] = []
        if not readings:
            signals.append("no_recent_readings")
        return signals

    def _reasons(
        self,
        age_minutes: float,
        missing: list[str],
        invalid: list[str],
        repeated: list[str],
        abnormal: list[str],
    ) -> list[str]:
        reasons: list[str] = []
        if age_minutes > self.rules.delayed_after_minutes:
            reasons.append("offline_threshold_exceeded")
        elif age_minutes > self.rules.online_after_minutes:
            reasons.append("delayed_threshold_exceeded")
        if missing:
            reasons.append("missing_pollutants")
        if invalid:
            reasons.append("invalid_or_suspect_values")
        if repeated:
            reasons.append("repeated_identical_readings")
        reasons.extend(abnormal)
        return reasons

    @staticmethod
    def _age_minutes(last_reading_at: datetime, evaluated_at: datetime) -> float:
        if last_reading_at.tzinfo is None:
            last_reading_at = last_reading_at.replace(tzinfo=UTC)
        if evaluated_at.tzinfo is None:
            evaluated_at = evaluated_at.replace(tzinfo=UTC)
        return (evaluated_at - last_reading_at).total_seconds() / 60


