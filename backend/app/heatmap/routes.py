from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db

from .idw import IDWInterpolator
from .schemas import BoundingBox, GeoJSONFeatureCollection, HeatmapRequest, WardAQISummary
from .service import AQIHeatmapService

router = APIRouter(prefix="/api/v1/heatmap", tags=["aqi-heatmap"])


def get_heatmap_service(db: Session = Depends(get_db)) -> AQIHeatmapService:
    from .repository import AQIHeatmapRepository

    return AQIHeatmapService(repository=AQIHeatmapRepository(db), interpolator=IDWInterpolator())


def bbox_from_query(
    min_latitude: float,
    min_longitude: float,
    max_latitude: float,
    max_longitude: float,
) -> BoundingBox:
    return BoundingBox(
        min_latitude=min_latitude,
        min_longitude=min_longitude,
        max_latitude=max_latitude,
        max_longitude=max_longitude,
    )


@router.get("/current", response_model=dict)
async def get_current_heatmap_data(
    min_latitude: float,
    min_longitude: float,
    max_latitude: float,
    max_longitude: float,
    grid_resolution: float = Query(default=0.01, gt=0, le=1),
    include_unreliable_sensors: bool = True,
    unhealthy_sensor_weight: float = Query(default=0.25, ge=0, le=1),
    service: AQIHeatmapService = Depends(get_heatmap_service),
) -> GeoJSONFeatureCollection:
    request = HeatmapRequest(
        bbox=bbox_from_query(min_latitude, min_longitude, max_latitude, max_longitude),
        grid_resolution=grid_resolution,
        include_unreliable_sensors=include_unreliable_sensors,
        unhealthy_sensor_weight=unhealthy_sensor_weight,
    )
    return service.get_current_heatmap(request)


@router.get("/wards", response_model=list[WardAQISummary])
async def get_ward_level_aqi_summaries(
    min_latitude: float | None = None,
    min_longitude: float | None = None,
    max_latitude: float | None = None,
    max_longitude: float | None = None,
    service: AQIHeatmapService = Depends(get_heatmap_service),
) -> list[WardAQISummary]:
    bbox = None
    if None not in (min_latitude, min_longitude, max_latitude, max_longitude):
        bbox = bbox_from_query(min_latitude, min_longitude, max_latitude, max_longitude)  # type: ignore[arg-type]
    return service.get_ward_aqi_summaries(bbox)
