from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db

from .repository import SensorHealthRepository
from .schemas import SensorHealthSnapshot, SensorHealthStatus
from .service import SensorHealthService

router = APIRouter(prefix="/api/v1/sensor-health", tags=["sensor-health"])


def get_sensor_health_service(db: Session = Depends(get_db)) -> SensorHealthService:
    return SensorHealthService(SensorHealthRepository(db))


@router.get("/stations", response_model=list[SensorHealthSnapshot])
async def get_all_station_health(
    service: SensorHealthService = Depends(get_sensor_health_service),
) -> list[SensorHealthSnapshot]:
    return service.get_all_station_health()


@router.get("/stations/{station_code}", response_model=SensorHealthSnapshot)
async def get_station_health(
    station_code: str,
    service: SensorHealthService = Depends(get_sensor_health_service),
) -> SensorHealthSnapshot:
    snapshot = service.get_station_health(station_code)
    if snapshot is None:
        raise HTTPException(status_code=404, detail="Station health status not found.")
    return snapshot


@router.get("/stations/{station_code}/history", response_model=list[SensorHealthSnapshot])
async def get_station_health_history(
    station_code: str,
    service: SensorHealthService = Depends(get_sensor_health_service),
) -> list[SensorHealthSnapshot]:
    return service.get_station_health_history(station_code)


@router.get("/reliability")
async def check_reading_reliability(
    status: SensorHealthStatus,
    data_quality_score: float,
    service: SensorHealthService = Depends(get_sensor_health_service),
) -> dict[str, bool]:
    return {"reliable": service.is_reading_reliable(status, data_quality_score)}
