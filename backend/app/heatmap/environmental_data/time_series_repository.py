from datetime import datetime, timedelta

from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session

from .models import AirQualityReading, WeatherForecast, WeatherObservation
from .time_series_schemas import (
    PollutantReading,
    StationLatestState,
    WeatherForecastReading,
    WeatherReading,
    WindReading,
)


class EnvironmentalTimeSeriesRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_latest_station_readings(self) -> list[StationLatestState]:
        latest_by_station_pollutant = (
            select(
                AirQualityReading.station_code,
                AirQualityReading.pollutant,
                func.max(AirQualityReading.observed_at).label("observed_at"),
            )
            .group_by(AirQualityReading.station_code, AirQualityReading.pollutant)
            .subquery()
        )
        statement = (
            select(AirQualityReading)
            .join(
                latest_by_station_pollutant,
                (AirQualityReading.station_code == latest_by_station_pollutant.c.station_code)
                & (AirQualityReading.pollutant == latest_by_station_pollutant.c.pollutant)
                & (AirQualityReading.observed_at == latest_by_station_pollutant.c.observed_at),
            )
            .order_by(AirQualityReading.station_code, AirQualityReading.pollutant)
        )
        grouped: dict[str, list[PollutantReading]] = {}
        station_meta: dict[str, AirQualityReading] = {}
        for row in self.db.scalars(statement):
            grouped.setdefault(row.station_code, []).append(self._pollutant_reading(row))
            station_meta[row.station_code] = row

        states: list[StationLatestState] = []
        for station_code, readings in grouped.items():
            meta = station_meta[station_code]
            observed_at = max(reading.observed_at for reading in readings)
            quality = "valid" if all(reading.data_quality_status == "valid" for reading in readings) else "incomplete"
            states.append(
                StationLatestState(
                    station_code=station_code,
                    station_name=meta.station_name,
                    ward_code=meta.ward_code,
                    observed_at=observed_at,
                    readings=readings,
                    data_quality_status=quality,
                )
            )
        return states

    def get_station_history(self, station_code: str, start_at: datetime, end_at: datetime) -> list[PollutantReading]:
        statement = self._reading_window_statement(start_at, end_at).where(AirQualityReading.station_code == station_code)
        return self._readings(statement)

    def get_ward_aqi_history(self, ward_code: str, start_at: datetime, end_at: datetime) -> list[PollutantReading]:
        statement = (
            self._reading_window_statement(start_at, end_at)
            .where(AirQualityReading.ward_code == ward_code)
            .where(AirQualityReading.pollutant == "AQI")
        )
        return self._readings(statement)

    def get_ward_pollutant_history(
        self,
        ward_code: str,
        pollutant: str,
        start_at: datetime,
        end_at: datetime,
    ) -> list[PollutantReading]:
        statement = (
            self._reading_window_statement(start_at, end_at)
            .where(AirQualityReading.ward_code == ward_code)
            .where(AirQualityReading.pollutant == pollutant)
        )
        return self._readings(statement)

    def get_historical_baseline(
        self,
        ward_code: str,
        pollutant: str,
        start_at: datetime,
        end_at: datetime,
        comparison_days: int,
    ) -> list[PollutantReading]:
        duration = end_at - start_at
        statements = []
        for days_back in range(7, comparison_days + 1, 7):
            baseline_start = start_at - timedelta(days=days_back)
            baseline_end = baseline_start + duration
            statements.append(
                self._reading_window_statement(baseline_start, baseline_end)
                .where(AirQualityReading.ward_code == ward_code)
                .where(AirQualityReading.pollutant == pollutant)
            )
        readings: list[PollutantReading] = []
        for statement in statements:
            readings.extend(self._readings(statement))
        return readings

    def get_current_weather(self, location_code: str | None = None) -> WeatherReading | None:
        statement = select(WeatherObservation).where(
            WeatherObservation.temperature_c.is_not(None)
            | WeatherObservation.relative_humidity_pct.is_not(None)
        )
        if location_code:
            statement = statement.where(WeatherObservation.location_code == location_code)
        row = self.db.scalars(statement.order_by(WeatherObservation.observed_at.desc()).limit(1)).first()
        return self._weather_reading(row) if row else None

    def get_current_wind(self, location_code: str | None = None) -> WindReading | None:
        statement = select(WeatherObservation).where(
            WeatherObservation.wind_speed_kmh.is_not(None)
            | WeatherObservation.wind_direction_degrees.is_not(None)
        )
        if location_code:
            statement = statement.where(WeatherObservation.location_code == location_code)
        row = self.db.scalars(statement.order_by(WeatherObservation.observed_at.desc()).limit(1)).first()
        return self._wind_reading(row) if row else None

    def get_weather_forecast(
        self,
        location_code: str,
        start_at: datetime,
        end_at: datetime,
    ) -> list[WeatherForecastReading]:
        statement = (
            select(WeatherForecast)
            .where(WeatherForecast.location_code == location_code)
            .where(WeatherForecast.forecast_for >= start_at)
            .where(WeatherForecast.forecast_for <= end_at)
            .order_by(WeatherForecast.forecast_for)
        )
        return [self._forecast_reading(row) for row in self.db.scalars(statement)]

    def get_readings_for_time_window(
        self,
        station_code: str | None = None,
        ward_code: str | None = None,
        pollutant: str | None = None,
        start_at: datetime | None = None,
        end_at: datetime | None = None,
    ) -> list[PollutantReading]:
        statement = select(AirQualityReading)
        if station_code:
            statement = statement.where(AirQualityReading.station_code == station_code)
        if ward_code:
            statement = statement.where(AirQualityReading.ward_code == ward_code)
        if pollutant:
            statement = statement.where(AirQualityReading.pollutant == pollutant)
        if start_at:
            statement = statement.where(AirQualityReading.observed_at >= start_at)
        if end_at:
            statement = statement.where(AirQualityReading.observed_at <= end_at)
        return self._readings(statement.order_by(AirQualityReading.observed_at))

    def _reading_window_statement(self, start_at: datetime, end_at: datetime) -> Select[tuple[AirQualityReading]]:
        return (
            select(AirQualityReading)
            .where(AirQualityReading.observed_at >= start_at)
            .where(AirQualityReading.observed_at <= end_at)
            .order_by(AirQualityReading.observed_at)
        )

    def _readings(self, statement: Select[tuple[AirQualityReading]]) -> list[PollutantReading]:
        return [self._pollutant_reading(row) for row in self.db.scalars(statement)]

    @staticmethod
    def _pollutant_reading(row: AirQualityReading) -> PollutantReading:
        return PollutantReading(
            station_code=row.station_code,
            station_name=row.station_name,
            ward_code=row.ward_code,
            observed_at=row.observed_at,
            pollutant=row.pollutant,
            value=row.value,
            unit=row.unit,
            data_quality_status=row.data_quality_status,
        )

    @staticmethod
    def _weather_reading(row: WeatherObservation) -> WeatherReading:
        return WeatherReading(
            location_code=row.location_code,
            city=row.city,
            observed_at=row.observed_at,
            temperature_c=row.temperature_c,
            relative_humidity_pct=row.relative_humidity_pct,
        )

    @staticmethod
    def _wind_reading(row: WeatherObservation) -> WindReading:
        return WindReading(
            location_code=row.location_code,
            city=row.city,
            observed_at=row.observed_at,
            wind_speed_kmh=row.wind_speed_kmh,
            wind_direction_degrees=row.wind_direction_degrees,
        )

    @staticmethod
    def _forecast_reading(row: WeatherForecast) -> WeatherForecastReading:
        return WeatherForecastReading(
            location_code=row.location_code,
            forecast_for=row.forecast_for,
            generated_at=row.generated_at,
            temperature_c=row.temperature_c,
            relative_humidity_pct=row.relative_humidity_pct,
            wind_speed_kmh=row.wind_speed_kmh,
            wind_direction_degrees=row.wind_direction_degrees,
            provider=row.provider,
            data_quality_status=row.data_quality_status,
        )
