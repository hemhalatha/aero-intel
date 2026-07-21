from datetime import datetime
from typing import Protocol

from .time_series_schemas import (
    HistoricalBaseline,
    PollutantReading,
    StationLatestState,
    WeatherForecastReading,
    WeatherReading,
    WindReading,
)


class EnvironmentalTimeSeriesRepositoryProtocol(Protocol):
    def get_latest_station_readings(self) -> list[StationLatestState]:
        ...

    def get_station_history(self, station_code: str, start_at: datetime, end_at: datetime) -> list[PollutantReading]:
        ...

    def get_ward_aqi_history(self, ward_code: str, start_at: datetime, end_at: datetime) -> list[PollutantReading]:
        ...

    def get_ward_pollutant_history(
        self,
        ward_code: str,
        pollutant: str,
        start_at: datetime,
        end_at: datetime,
    ) -> list[PollutantReading]:
        ...

    def get_historical_baseline(
        self,
        ward_code: str,
        pollutant: str,
        start_at: datetime,
        end_at: datetime,
        comparison_days: int,
    ) -> list[PollutantReading]:
        ...

    def get_current_weather(self, location_code: str | None = None) -> WeatherReading | None:
        ...

    def get_current_wind(self, location_code: str | None = None) -> WindReading | None:
        ...

    def get_weather_forecast(
        self,
        location_code: str,
        start_at: datetime,
        end_at: datetime,
    ) -> list[WeatherForecastReading]:
        ...

    def get_readings_for_time_window(
        self,
        station_code: str | None = None,
        ward_code: str | None = None,
        pollutant: str | None = None,
        start_at: datetime | None = None,
        end_at: datetime | None = None,
    ) -> list[PollutantReading]:
        ...


class EnvironmentalTimeSeriesService:
    def __init__(self, repository: EnvironmentalTimeSeriesRepositoryProtocol) -> None:
        self.repository = repository

    def get_latest_station_readings(self) -> list[StationLatestState]:
        return self.repository.get_latest_station_readings()

    def get_station_history(self, station_code: str, start_at: datetime, end_at: datetime) -> list[PollutantReading]:
        return self.repository.get_station_history(station_code, start_at, end_at)

    def get_ward_aqi_history(self, ward_code: str, start_at: datetime, end_at: datetime) -> list[PollutantReading]:
        return self.repository.get_ward_aqi_history(ward_code, start_at, end_at)

    def get_ward_pollutant_history(
        self,
        ward_code: str,
        pollutant: str,
        start_at: datetime,
        end_at: datetime,
    ) -> list[PollutantReading]:
        return self.repository.get_ward_pollutant_history(ward_code, pollutant, start_at, end_at)

    def get_historical_baseline(
        self,
        ward_code: str,
        pollutant: str,
        start_at: datetime,
        end_at: datetime,
        comparison_days: int = 28,
    ) -> HistoricalBaseline:
        readings = self.repository.get_historical_baseline(ward_code, pollutant, start_at, end_at, comparison_days)
        average = round(sum(reading.value for reading in readings) / len(readings), 2) if readings else None
        return HistoricalBaseline(
            ward_code=ward_code,
            pollutant=pollutant,
            comparison_days=comparison_days,
            readings=readings,
            average_value=average,
        )

    def get_current_weather(self, location_code: str | None = None) -> WeatherReading | None:
        return self.repository.get_current_weather(location_code)

    def get_current_wind(self, location_code: str | None = None) -> WindReading | None:
        return self.repository.get_current_wind(location_code)

    def get_weather_forecast(
        self,
        location_code: str,
        start_at: datetime,
        end_at: datetime,
    ) -> list[WeatherForecastReading]:
        return self.repository.get_weather_forecast(location_code, start_at, end_at)

    def get_readings_for_time_window(
        self,
        station_code: str | None = None,
        ward_code: str | None = None,
        pollutant: str | None = None,
        start_at: datetime | None = None,
        end_at: datetime | None = None,
    ) -> list[PollutantReading]:
        return self.repository.get_readings_for_time_window(station_code, ward_code, pollutant, start_at, end_at)
