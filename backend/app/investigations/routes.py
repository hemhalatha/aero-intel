from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.hotspot_lifecycle.repository import HotspotLifecycleRepository
from app.hotspot_lifecycle.schemas import HotspotEventRecord
from app.hotspot_lifecycle.service import HotspotLifecycleService

from .collectors import default_collectors
from .repository import InvestigationRepository
from .schemas import AdditionalEvidenceRequest, HotspotCreatedEventIn, InvestigationDetail, InvestigationRecord, InvestigationStatus
from .service import HotspotLifecycleContextProvider, InvestigationOrchestrator

router = APIRouter(prefix="/api/v1/investigations", tags=["investigations"])


def get_investigation_orchestrator(db: Session = Depends(get_db)) -> InvestigationOrchestrator:
    hotspot_service = HotspotLifecycleService(HotspotLifecycleRepository(db))
    return InvestigationOrchestrator(
        repository=InvestigationRepository(db),
        context_provider=HotspotLifecycleContextProvider(hotspot_service),
        collectors=default_collectors(),
    )


@router.post("/events/hotspot-created", response_model=InvestigationRecord, status_code=status.HTTP_202_ACCEPTED)
async def receive_hotspot_created(
    event: HotspotCreatedEventIn,
    orchestrator: InvestigationOrchestrator = Depends(get_investigation_orchestrator),
) -> InvestigationRecord:
    try:
        return orchestrator.handle_hotspot_created(
            HotspotEventRecord(
                hotspot_id=event.hotspot_id,
                event_type=event.event_type,
                payload=event.payload,
                published_at=event.published_at,
            )
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("", response_model=list[InvestigationRecord])
async def list_investigations(
    status_filter: InvestigationStatus | None = Query(default=None, alias="status"),
    orchestrator: InvestigationOrchestrator = Depends(get_investigation_orchestrator),
) -> list[InvestigationRecord]:
    return orchestrator.list_investigations(status_filter)


@router.get("/{investigation_id}", response_model=InvestigationDetail)
async def get_investigation_detail(
    investigation_id: int,
    orchestrator: InvestigationOrchestrator = Depends(get_investigation_orchestrator),
) -> InvestigationDetail:
    try:
        return orchestrator.get_investigation_detail(investigation_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/{investigation_id}/evidence-requests", response_model=InvestigationRecord, status_code=status.HTTP_202_ACCEPTED)
async def request_additional_evidence(
    investigation_id: int,
    request: AdditionalEvidenceRequest,
    orchestrator: InvestigationOrchestrator = Depends(get_investigation_orchestrator),
) -> InvestigationRecord:
    try:
        return orchestrator.collect_additional_evidence(
            investigation_id,
            requested_collectors=request.requested_collectors,
            reason=request.reason,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
