from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db

from .repository import HotspotLifecycleRepository
from .schemas import (
    HotspotCandidateIngestionRequest,
    HotspotDetail,
    HotspotEventRecord,
    HotspotObservationRecord,
    HotspotRecord,
    HotspotStateUpdate,
    HotspotStatus,
    HotspotStatusHistoryRecord,
)
from .service import HotspotLifecycleService

router = APIRouter(prefix="/api/v1/hotspots", tags=["hotspots"])


def get_hotspot_lifecycle_service(db: Session = Depends(get_db)) -> HotspotLifecycleService:
    return HotspotLifecycleService(HotspotLifecycleRepository(db))


@router.post("/candidates", response_model=HotspotRecord, status_code=status.HTTP_201_CREATED)
async def ingest_hotspot_candidate(
    request: HotspotCandidateIngestionRequest,
    service: HotspotLifecycleService = Depends(get_hotspot_lifecycle_service),
) -> HotspotRecord:
    return service.ingest_candidate(request.candidate, detection_context=request.detection_context)


@router.get("", response_model=list[HotspotRecord])
async def list_hotspots(
    status_filter: HotspotStatus | None = Query(default=None, alias="status"),
    service: HotspotLifecycleService = Depends(get_hotspot_lifecycle_service),
) -> list[HotspotRecord]:
    return service.list_hotspots(status_filter)


@router.get("/{hotspot_id}", response_model=HotspotDetail)
async def get_hotspot_detail(
    hotspot_id: int,
    service: HotspotLifecycleService = Depends(get_hotspot_lifecycle_service),
) -> HotspotDetail:
    try:
        return service.get_hotspot_detail(hotspot_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.patch("/{hotspot_id}/state", response_model=HotspotRecord)
async def update_hotspot_state(
    hotspot_id: int,
    update: HotspotStateUpdate,
    service: HotspotLifecycleService = Depends(get_hotspot_lifecycle_service),
) -> HotspotRecord:
    try:
        return service.update_hotspot_state(hotspot_id, update)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/{hotspot_id}/observations", response_model=list[HotspotObservationRecord])
async def get_hotspot_observations(
    hotspot_id: int,
    service: HotspotLifecycleService = Depends(get_hotspot_lifecycle_service),
) -> list[HotspotObservationRecord]:
    try:
        return service.get_hotspot_detail(hotspot_id).observations
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/{hotspot_id}/status-history", response_model=list[HotspotStatusHistoryRecord])
async def get_hotspot_status_history(
    hotspot_id: int,
    service: HotspotLifecycleService = Depends(get_hotspot_lifecycle_service),
) -> list[HotspotStatusHistoryRecord]:
    try:
        return service.get_hotspot_detail(hotspot_id).status_history
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/{hotspot_id}/events", response_model=list[HotspotEventRecord])
async def get_hotspot_events(
    hotspot_id: int,
    service: HotspotLifecycleService = Depends(get_hotspot_lifecycle_service),
) -> list[HotspotEventRecord]:
    try:
        return service.get_hotspot_detail(hotspot_id).events
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
