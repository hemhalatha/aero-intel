from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db

from .time_series import EnvironmentalTimeSeriesService
from .time_series_repository import EnvironmentalTimeSeriesRepository
from .time_series_schemas import (
    HistoricalBaseline,
    PollutantReading,
    StationLatestState,
    WeatherForecastReading,
    WeatherReading,
    WindReading,
)

router = APIRouter(prefix="/api/v1/environmental", tags=["environmental-data"])


def get_time_series_service(db: Session = Depends(get_db)) -> EnvironmentalTimeSeriesService:
    return EnvironmentalTimeSeriesService(EnvironmentalTimeSeriesRepository(db))


@router.get("/stations/latest", response_model=list[StationLatestState])
async def get_latest_station_readings(
    service: EnvironmentalTimeSeriesService = Depends(get_time_series_service),
) -> list[StationLatestState]:
    return service.get_latest_station_readings()


@router.get("/stations/{station_code}/history", response_model=list[PollutantReading])
async def get_station_history(
    station_code: str,
    start_at: datetime,
    end_at: datetime,
    service: EnvironmentalTimeSeriesService = Depends(get_time_series_service),
) -> list[PollutantReading]:
    return service.get_station_history(station_code, start_at, end_at)


@router.get("/wards/{ward_code}/aqi/history", response_model=list[PollutantReading])
async def get_ward_aqi_history(
    ward_code: str,
    start_at: datetime,
    end_at: datetime,
    service: EnvironmentalTimeSeriesService = Depends(get_time_series_service),
) -> list[PollutantReading]:
    return service.get_ward_aqi_history(ward_code, start_at, end_at)


@router.get("/wards/{ward_code}/pollutants/{pollutant}/history", response_model=list[PollutantReading])
async def get_ward_pollutant_history(
    ward_code: str,
    pollutant: str,
    start_at: datetime,
    end_at: datetime,
    service: EnvironmentalTimeSeriesService = Depends(get_time_series_service),
) -> list[PollutantReading]:
    return service.get_ward_pollutant_history(ward_code, pollutant, start_at, end_at)


@router.get("/wards/{ward_code}/pollutants/{pollutant}/baseline", response_model=HistoricalBaseline)
async def get_historical_baseline(
    ward_code: str,
    pollutant: str,
    start_at: datetime,
    end_at: datetime,
    comparison_days: int = Query(default=28, ge=7, le=365),
    service: EnvironmentalTimeSeriesService = Depends(get_time_series_service),
) -> HistoricalBaseline:
    return service.get_historical_baseline(ward_code, pollutant, start_at, end_at, comparison_days)


@router.get("/weather/current", response_model=WeatherReading | None)
async def get_current_weather(
    location_code: str | None = None,
    service: EnvironmentalTimeSeriesService = Depends(get_time_series_service),
) -> WeatherReading | None:
    return service.get_current_weather(location_code)


@router.get("/wind/current", response_model=WindReading | None)
async def get_current_wind(
    location_code: str | None = None,
    service: EnvironmentalTimeSeriesService = Depends(get_time_series_service),
) -> WindReading | None:
    return service.get_current_wind(location_code)


@router.get("/weather/forecast", response_model=list[WeatherForecastReading])
async def get_weather_forecast(
    location_code: str,
    start_at: datetime,
    end_at: datetime,
    service: EnvironmentalTimeSeriesService = Depends(get_time_series_service),
) -> list[WeatherForecastReading]:
    return service.get_weather_forecast(location_code, start_at, end_at)


@router.get("/readings/window", response_model=list[PollutantReading])
async def get_readings_for_time_window(
    station_code: str | None = None,
    ward_code: str | None = None,
    pollutant: str | None = None,
    start_at: datetime | None = None,
    end_at: datetime | None = None,
    service: EnvironmentalTimeSeriesService = Depends(get_time_series_service),
) -> list[PollutantReading]:
    return service.get_readings_for_time_window(station_code, ward_code, pollutant, start_at, end_at)
