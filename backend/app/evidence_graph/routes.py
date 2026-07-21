from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.environmental_data.time_series import EnvironmentalTimeSeriesService
from app.environmental_data.time_series_repository import EnvironmentalTimeSeriesRepository
from app.hotspot_lifecycle.repository import HotspotLifecycleRepository
from app.hotspot_lifecycle.service import HotspotLifecycleService
from app.intelligence_contract.service import DEFAULT_POLLUTANTS, IntelligenceContractService
from app.investigations.evidence import EvidenceRepository, EvidenceService
from app.investigations.repository import InvestigationRepository
from app.investigations.service import EmptyEnvironmentalContextProvider, InvestigationOrchestrator

from .repository import EvidenceGraphRepository
from .schemas import EvidenceGraphBuildRequest, EvidenceGraphResponse
from .service import EvidenceGraphService

router = APIRouter(prefix="/api/v1/evidence-graphs", tags=["evidence-graphs"])


def get_intelligence_contract_service(db: Session = Depends(get_db)) -> IntelligenceContractService:
    hotspot_repository = HotspotLifecycleRepository(db)
    investigation_repository = InvestigationRepository(db)
    return IntelligenceContractService(
        hotspot_service=HotspotLifecycleService(hotspot_repository),
        investigation_service=InvestigationOrchestrator(
            repository=investigation_repository,
            context_provider=EmptyEnvironmentalContextProvider(),
            collectors=[],
        ),
        investigation_lookup=investigation_repository,
        evidence_service=EvidenceService(EvidenceRepository(db)),
        environmental_service=EnvironmentalTimeSeriesService(EnvironmentalTimeSeriesRepository(db)),
    )


def get_evidence_graph_service(db: Session = Depends(get_db)) -> EvidenceGraphService:
    return EvidenceGraphService(EvidenceGraphRepository(db))


@router.post("/investigations/{investigation_id}", response_model=EvidenceGraphResponse, status_code=201)
async def build_investigation_evidence_graph(
    investigation_id: int,
    request: EvidenceGraphBuildRequest | None = None,
    start_at: datetime | None = None,
    end_at: datetime | None = None,
    pollutants: Annotated[list[str] | None, Query()] = None,
    contract_service: IntelligenceContractService = Depends(get_intelligence_contract_service),
    graph_service: EvidenceGraphService = Depends(get_evidence_graph_service),
) -> EvidenceGraphResponse:
    try:
        contract = contract_service.get_contract_by_investigation(investigation_id, start_at, end_at, pollutants or DEFAULT_POLLUTANTS)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    request = request or EvidenceGraphBuildRequest()
    if request.persist:
        return graph_service.build_and_persist_graph(contract, metadata=request.metadata)
    return graph_service.build_graph(contract, metadata=request.metadata)


@router.post("/hotspots/{hotspot_id}", response_model=EvidenceGraphResponse, status_code=201)
async def build_hotspot_evidence_graph(
    hotspot_id: int,
    request: EvidenceGraphBuildRequest | None = None,
    start_at: datetime | None = None,
    end_at: datetime | None = None,
    pollutants: Annotated[list[str] | None, Query()] = None,
    contract_service: IntelligenceContractService = Depends(get_intelligence_contract_service),
    graph_service: EvidenceGraphService = Depends(get_evidence_graph_service),
) -> EvidenceGraphResponse:
    try:
        contract = contract_service.get_contract_by_hotspot(hotspot_id, start_at, end_at, pollutants or DEFAULT_POLLUTANTS)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    request = request or EvidenceGraphBuildRequest()
    if request.persist:
        return graph_service.build_and_persist_graph(contract, metadata=request.metadata)
    return graph_service.build_graph(contract, metadata=request.metadata)


@router.get("/investigations/{investigation_id}", response_model=EvidenceGraphResponse)
async def get_latest_investigation_evidence_graph(
    investigation_id: int,
    graph_service: EvidenceGraphService = Depends(get_evidence_graph_service),
) -> EvidenceGraphResponse:
    graph = graph_service.get_latest_graph_for_investigation(investigation_id)
    if graph is None:
        raise HTTPException(status_code=404, detail="Evidence graph not found for investigation.")
    return graph


@router.get("/hotspots/{hotspot_id}", response_model=EvidenceGraphResponse)
async def get_latest_hotspot_evidence_graph(
    hotspot_id: int,
    graph_service: EvidenceGraphService = Depends(get_evidence_graph_service),
) -> EvidenceGraphResponse:
    graph = graph_service.get_latest_graph_for_hotspot(hotspot_id)
    if graph is None:
        raise HTTPException(status_code=404, detail="Evidence graph not found for hotspot.")
    return graph
