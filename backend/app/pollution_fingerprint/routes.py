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

from .schemas import PollutionFingerprintResult
from .service import PollutionFingerprintService

router = APIRouter(prefix="/api/v1/pollution-fingerprints", tags=["pollution-fingerprints"])


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


def get_fingerprint_service() -> PollutionFingerprintService:
    return PollutionFingerprintService()


@router.get("/hotspots/{hotspot_id}", response_model=PollutionFingerprintResult)
async def get_hotspot_pollution_fingerprint(
    hotspot_id: int,
    start_at: datetime | None = None,
    end_at: datetime | None = None,
    pollutants: Annotated[list[str] | None, Query()] = None,
    contract_service: IntelligenceContractService = Depends(get_intelligence_contract_service),
    fingerprint_service: PollutionFingerprintService = Depends(get_fingerprint_service),
) -> PollutionFingerprintResult:
    try:
        contract = contract_service.get_contract_by_hotspot(hotspot_id, start_at, end_at, pollutants or DEFAULT_POLLUTANTS)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return fingerprint_service.generate(contract)


@router.get("/investigations/{investigation_id}", response_model=PollutionFingerprintResult)
async def get_investigation_pollution_fingerprint(
    investigation_id: int,
    start_at: datetime | None = None,
    end_at: datetime | None = None,
    pollutants: Annotated[list[str] | None, Query()] = None,
    contract_service: IntelligenceContractService = Depends(get_intelligence_contract_service),
    fingerprint_service: PollutionFingerprintService = Depends(get_fingerprint_service),
) -> PollutionFingerprintResult:
    try:
        contract = contract_service.get_contract_by_investigation(investigation_id, start_at, end_at, pollutants or DEFAULT_POLLUTANTS)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return fingerprint_service.generate(contract)
