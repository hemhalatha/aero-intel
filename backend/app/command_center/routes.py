from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.environmental_data.time_series import EnvironmentalTimeSeriesService
from app.heatmap.idw import IDWInterpolator
from app.heatmap.service import AQIHeatmapService
from app.sensor_health.repository import SensorHealthRepository
from app.sensor_health.service import SensorHealthService

from .schemas import CommandCenterDashboard
from .service import CommandCenterAggregationService, EmptyHotspotSummaryProvider

router = APIRouter(prefix="/api/v1/command-center", tags=["command-center"])


def get_command_center_service(db: Session = Depends(get_db)) -> CommandCenterAggregationService:
    from app.environmental_data.time_series_repository import EnvironmentalTimeSeriesRepository
    from app.heatmap.repository import AQIHeatmapRepository

    time_series_service = EnvironmentalTimeSeriesService(EnvironmentalTimeSeriesRepository(db))
    heatmap_service = AQIHeatmapService(AQIHeatmapRepository(db), IDWInterpolator())
    sensor_health_service = SensorHealthService(SensorHealthRepository(db))
    return CommandCenterAggregationService(
        heatmap_service=heatmap_service,
        sensor_health_service=sensor_health_service,
        time_series_service=time_series_service,
        hotspot_provider=EmptyHotspotSummaryProvider(),
    )


@router.get("/dashboard", response_model=CommandCenterDashboard)
async def get_initial_dashboard(
    service: CommandCenterAggregationService = Depends(get_command_center_service),
) -> CommandCenterDashboard:
    return service.get_initial_dashboard()
