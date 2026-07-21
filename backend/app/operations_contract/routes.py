from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.environmental_data.time_series import EnvironmentalTimeSeriesService
from app.environmental_data.time_series_repository import EnvironmentalTimeSeriesRepository
from app.geo_master.repositories import GeoMasterRepository
from app.geo_master.services import GeoMasterService
from app.hotspot_lifecycle.repository import HotspotLifecycleRepository
from app.hotspot_lifecycle.service import HotspotLifecycleService
from app.sensor_health.repository import SensorHealthRepository
from app.sensor_health.service import SensorHealthService

from .schemas import InterventionVerificationWindow, OperationsTimeWindowReadings, WardOperationsState
from .service import (
    DEFAULT_BASELINE_HOURS,
    DEFAULT_EVALUATION_HOURS,
    DEFAULT_HISTORY_CONTEXT_HOURS,
    DEFAULT_STATE_LOOKBACK_HOURS,
    OperationsContractService,
)

router = APIRouter(prefix="/api/v1/operations-contract", tags=["operations-contract"])


def get_operations_contract_service(db: Session = Depends(get_db)) -> OperationsContractService:
    return OperationsContractService(
        environmental_service=EnvironmentalTimeSeriesService(EnvironmentalTimeSeriesRepository(db)),
        hotspot_service=HotspotLifecycleService(HotspotLifecycleRepository(db)),
        sensor_health_service=SensorHealthService(SensorHealthRepository(db)),
        geo_service=GeoMasterService(GeoMasterRepository(db)),
    )


@router.get("/wards/{ward_code}/state", response_model=WardOperationsState)
async def get_ward_operations_state(
    ward_code: str,
    as_of: datetime | None = None,
    lookback_hours: int = Query(default=DEFAULT_STATE_LOOKBACK_HOURS, ge=1, le=168),
    service: OperationsContractService = Depends(get_operations_contract_service),
) -> WardOperationsState:
    return service.get_ward_state(ward_code=ward_code, as_of=as_of, lookback_hours=lookback_hours)


@router.get("/wards/{ward_code}/readings", response_model=OperationsTimeWindowReadings)
async def get_ward_readings_for_time_window(
    ward_code: str,
    start_at: datetime,
    end_at: datetime,
    pollutant: str | None = None,
    station_code: str | None = None,
    selected_at: datetime | None = None,
    service: OperationsContractService = Depends(get_operations_contract_service),
) -> OperationsTimeWindowReadings:
    return service.get_readings_for_time_window(
        ward_code=ward_code,
        start_at=start_at,
        end_at=end_at,
        pollutant=pollutant,
        station_code=station_code,
        selected_at=selected_at,
    )


@router.get("/wards/{ward_code}/readings/around", response_model=OperationsTimeWindowReadings)
async def get_ward_readings_around_timestamp(
    ward_code: str,
    selected_at: datetime,
    context_hours: int = Query(default=DEFAULT_HISTORY_CONTEXT_HOURS, ge=1, le=72),
    pollutant: str | None = None,
    station_code: str | None = None,
    service: OperationsContractService = Depends(get_operations_contract_service),
) -> OperationsTimeWindowReadings:
    return service.get_readings_around_timestamp(
        ward_code=ward_code,
        selected_at=selected_at,
        context_hours=context_hours,
        pollutant=pollutant,
        station_code=station_code,
    )


@router.get("/wards/{ward_code}/intervention-verification", response_model=InterventionVerificationWindow)
async def get_intervention_verification_window(
    ward_code: str,
    intervention_at: datetime,
    intervention_id: str | None = None,
    baseline_hours: int = Query(default=DEFAULT_BASELINE_HOURS, ge=1, le=720),
    evaluation_hours: int = Query(default=DEFAULT_EVALUATION_HOURS, ge=1, le=720),
    pollutant: str | None = None,
    station_code: str | None = None,
    forecast_location_code: str | None = None,
    service: OperationsContractService = Depends(get_operations_contract_service),
) -> InterventionVerificationWindow:
    return service.get_intervention_verification_window(
        ward_code=ward_code,
        intervention_at=intervention_at,
        baseline_hours=baseline_hours,
        evaluation_hours=evaluation_hours,
        pollutant=pollutant,
        station_code=station_code,
        intervention_id=intervention_id,
        forecast_location_code=forecast_location_code,
    )
