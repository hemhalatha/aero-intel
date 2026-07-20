from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.hotspot_lifecycle.repository import HotspotLifecycleRepository
from app.hotspot_lifecycle.schemas import HotspotEventRecord
from app.hotspot_lifecycle.service import HotspotLifecycleService

from .collectors import default_collectors
from .evidence import (
    EvidenceCreate,
    EvidenceRecord,
    EvidenceRepository,
    EvidenceService,
    EvidenceUpdate,
    EvidenceVersionRecord,
)
from .repository import InvestigationRepository
from .schemas import (
    AdditionalEvidenceRequest,
    HotspotCreatedEventIn,
    InvestigationDetail,
    InvestigationRecord,
    InvestigationStatus,
)
from .service import HotspotLifecycleContextProvider, InvestigationOrchestrator

router = APIRouter(prefix="/api/v1/investigations", tags=["investigations"])


def get_evidence_service(db: Session = Depends(get_db)) -> EvidenceService:
    return EvidenceService(EvidenceRepository(db))


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


@router.get("/{investigation_id}/evidence", response_model=list[EvidenceRecord])
async def get_investigation_evidence(
    investigation_id: int,
    source_type: str | None = None,
    evidence_type: str | None = None,
    service: EvidenceService = Depends(get_evidence_service),
) -> list[EvidenceRecord]:
    return service.get_investigation_evidence(
        investigation_id,
        source_type=source_type,
        evidence_type=evidence_type,
    )


@router.get("/{investigation_id}/evidence/supporting", response_model=list[EvidenceRecord])
async def get_supporting_evidence(
    investigation_id: int,
    service: EvidenceService = Depends(get_evidence_service),
) -> list[EvidenceRecord]:
    return service.get_supporting_evidence(investigation_id)


@router.get("/{investigation_id}/evidence/contradictory", response_model=list[EvidenceRecord])
async def get_contradictory_evidence(
    investigation_id: int,
    service: EvidenceService = Depends(get_evidence_service),
) -> list[EvidenceRecord]:
    return service.get_contradictory_evidence(investigation_id)


@router.get("/{investigation_id}/evidence/types/{evidence_type}", response_model=list[EvidenceRecord])
async def get_evidence_by_type(
    investigation_id: int,
    evidence_type: str,
    service: EvidenceService = Depends(get_evidence_service),
) -> list[EvidenceRecord]:
    return service.get_evidence_by_type(investigation_id, evidence_type)


@router.post("/{investigation_id}/evidence", response_model=EvidenceRecord, status_code=status.HTTP_201_CREATED)
async def add_followup_evidence(
    investigation_id: int,
    evidence: EvidenceCreate,
    service: EvidenceService = Depends(get_evidence_service),
) -> EvidenceRecord:
    if evidence.investigation_id != investigation_id:
        raise HTTPException(status_code=422, detail="Evidence investigation_id must match the route investigation_id.")
    return service.add_followup_evidence(evidence)


@router.patch("/evidence/{evidence_id}", response_model=EvidenceRecord)
async def update_evidence(
    evidence_id: int,
    update: EvidenceUpdate,
    reason: str | None = Query(default=None, max_length=240),
    service: EvidenceService = Depends(get_evidence_service),
) -> EvidenceRecord:
    try:
        return service.update_evidence(evidence_id, update, reason)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/evidence/{evidence_id}/versions", response_model=list[EvidenceVersionRecord])
async def get_evidence_versions(
    evidence_id: int,
    service: EvidenceService = Depends(get_evidence_service),
) -> list[EvidenceVersionRecord]:
    return service.get_evidence_versions(evidence_id)
