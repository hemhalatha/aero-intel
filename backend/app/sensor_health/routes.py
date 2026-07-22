from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db_optional

from .repository import SensorHealthRepository
from .schemas import SensorHealthSnapshot, SensorHealthStatus
from .service import SensorHealthService

router = APIRouter(prefix="/api/v1/sensor-health", tags=["sensor-health"])


def get_sensor_health_service(db: Session | None = Depends(get_db_optional)) -> SensorHealthService:
    from app.command_center.fallback import FallbackSensorHealthService
    return FallbackSensorHealthService()






import json

@router.get("/stations")
async def get_all_station_health():
    from app.command_center.fallback import FallbackSensorHealthService
    items = FallbackSensorHealthService().get_all_station_health()
    return [json.loads(item.model_dump_json()) for item in items]


@router.get("/stations/{station_code}")
async def get_station_health(station_code: str):
    from app.command_center.fallback import FallbackSensorHealthService
    snapshot = FallbackSensorHealthService().get_station_health(station_code)
    if snapshot is None:
        raise HTTPException(status_code=404, detail="Station health status not found.")
    return json.loads(snapshot.model_dump_json())





@router.get("/stations/{station_code}/history")
async def get_station_health_history(
    station_code: str,
    service: SensorHealthService = Depends(get_sensor_health_service),
):
    try:
        return service.get_station_health_history(station_code)
    except Exception:
        from app.command_center.fallback import FallbackSensorHealthService
        return FallbackSensorHealthService().get_station_health_history(station_code)




@router.get("/reliability")
async def check_reading_reliability(
    status: SensorHealthStatus,
    data_quality_score: float,
    service: SensorHealthService = Depends(get_sensor_health_service),
) -> dict[str, bool]:
    return {"reliable": service.is_reading_reliable(status, data_quality_score)}
