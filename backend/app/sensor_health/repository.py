from sqlalchemy import select
from sqlalchemy.orm import Session

from .models import SensorHealthCurrent, SensorHealthHistory
from .schemas import SensorHealthSnapshot, SensorHealthStatus


class SensorHealthRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_current_statuses(self) -> list[SensorHealthSnapshot]:
        try:
            rows = self.db.scalars(select(SensorHealthCurrent).order_by(SensorHealthCurrent.station_code))
            return [self._snapshot(row) for row in rows]
        except Exception:
            from app.command_center.fallback import FallbackSensorHealthService
            return FallbackSensorHealthService().get_all_station_health()

    def get_current_status(self, station_code: str) -> SensorHealthSnapshot | None:
        try:
            row = self.db.get(SensorHealthCurrent, station_code)
            return self._snapshot(row) if row else None
        except Exception:
            from app.command_center.fallback import FallbackSensorHealthService
            return FallbackSensorHealthService().get_current_status(station_code)

    def get_health_history(self, station_code: str) -> list[SensorHealthSnapshot]:
        try:
            statement = (
                select(SensorHealthHistory)
                .where(SensorHealthHistory.station_code == station_code)
                .order_by(SensorHealthHistory.changed_at.desc())
            )
            return [self._snapshot(row) for row in self.db.scalars(statement)]
        except Exception:
            from app.command_center.fallback import FallbackSensorHealthService
            return FallbackSensorHealthService().get_health_history(station_code)


    def save_health_snapshot(self, snapshot: SensorHealthSnapshot) -> None:
        current = self.db.get(SensorHealthCurrent, snapshot.station_code)
        should_log_history = (
            current is None
            or current.status != snapshot.status.value
            or round(current.data_quality_score, 2) != round(snapshot.data_quality_score, 2)
        )
        values = self._values(snapshot)
        if current is None:
            current = SensorHealthCurrent(**values)
            self.db.add(current)
        else:
            for key, value in values.items():
                setattr(current, key, value)

        if should_log_history:
            self.db.add(SensorHealthHistory(**values))

    @staticmethod
    def _values(snapshot: SensorHealthSnapshot) -> dict:
        return {
            "station_code": snapshot.station_code,
            "station_name": snapshot.station_name,
            "ward_code": snapshot.ward_code,
            "status": snapshot.status.value,
            "data_quality_score": snapshot.data_quality_score,
            "last_reading_at": snapshot.last_reading_at,
            "evaluated_at": snapshot.evaluated_at,
            "missing_pollutants": snapshot.missing_pollutants,
            "invalid_pollutants": snapshot.invalid_pollutants,
            "repeated_pollutants": snapshot.repeated_pollutants,
            "abnormal_signals": snapshot.abnormal_signals,
            "reasons": snapshot.reasons,
            "is_reliable": snapshot.is_reliable,
        }

    @staticmethod
    def _snapshot(row: SensorHealthCurrent | SensorHealthHistory) -> SensorHealthSnapshot:
        return SensorHealthSnapshot(
            station_code=row.station_code,
            station_name=row.station_name,
            ward_code=row.ward_code,
            status=SensorHealthStatus(row.status),
            data_quality_score=row.data_quality_score,
            last_reading_at=row.last_reading_at,
            evaluated_at=row.evaluated_at,
            missing_pollutants=row.missing_pollutants,
            invalid_pollutants=row.invalid_pollutants,
            repeated_pollutants=row.repeated_pollutants,
            abnormal_signals=row.abnormal_signals,
            reasons=row.reasons,
            is_reliable=row.is_reliable,
        )
