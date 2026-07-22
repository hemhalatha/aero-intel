import os

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.exc import OperationalError

from .attribution import attribute_sources, generate_explanation
from .command_center.routes import router as command_center_router
from .database import (
    DatabaseConfigurationError,
    DatabaseConnectionError,
    check_database_connection,
    get_database_url,
    _diagnose_operational_error,
)
from .environmental_data.routes import router as environmental_data_router
from .evidence_graph.routes import router as evidence_graph_router
from .heatmap.routes import router as heatmap_router
from .hotspot_lifecycle.routes import router as hotspot_lifecycle_router
from .intelligence_contract.routes import router as intelligence_contract_router
from .operations_contract.routes import router as operations_contract_router
from .pollution_fingerprint.routes import router as pollution_fingerprint_router
from .investigations.routes import router as investigations_router
from .schemas import AttributionResponse, EvidenceBundle, ExplanationResponse
from .sensor_health.routes import router as sensor_health_router
from .uncertainty.routes import router as uncertainty_router


def get_allowed_origins() -> list[str]:
    defaults = ["http://localhost:5173", "http://127.0.0.1:5173"]
    configured = os.getenv("ALLOWED_ORIGINS", "")
    origins = [origin.strip() for origin in configured.split(",") if origin.strip()]
    return [*defaults, *origins]


app = FastAPI(title="AeroIntel", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=get_allowed_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(command_center_router)
app.include_router(environmental_data_router)
app.include_router(evidence_graph_router)
app.include_router(heatmap_router)
app.include_router(hotspot_lifecycle_router)
app.include_router(investigations_router)
app.include_router(intelligence_contract_router)
app.include_router(operations_contract_router)
app.include_router(pollution_fingerprint_router)
app.include_router(sensor_health_router)
app.include_router(uncertainty_router)


@app.exception_handler(DatabaseConfigurationError)
async def database_configuration_exception_handler(
    request: Request,
    exc: DatabaseConfigurationError,
) -> JSONResponse:
    return JSONResponse(
        status_code=503,
        content={
            "detail": str(exc),
            "hint": "Set DATABASE_URL in .env or backend/.env. Do not commit real passwords.",
        },
    )


@app.exception_handler(DatabaseConnectionError)
async def database_connection_exception_handler(
    request: Request,
    exc: DatabaseConnectionError,
) -> JSONResponse:
    return JSONResponse(status_code=503, content={"detail": str(exc)})


@app.exception_handler(OperationalError)
async def sqlalchemy_operational_exception_handler(
    request: Request,
    exc: OperationalError,
) -> JSONResponse:
    return JSONResponse(
        status_code=503,
        content={"detail": _diagnose_operational_error(exc, get_database_url())},
    )


@app.get("/")
def root() -> dict[str, str]:
    return {
        "message": "Welcome to AeroIntel AI Urban Air Quality Command Center API",
        "docs": "/docs",
        "health": "/health",
        "command_center_dashboard": "/api/v1/command-center/dashboard",
    }


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok", "module": "aerointel"}



@app.get("/health/database")
def database_health_check() -> JSONResponse:
    try:
        return JSONResponse(status_code=200, content=check_database_connection())
    except (DatabaseConfigurationError, DatabaseConnectionError) as exc:
        return JSONResponse(status_code=503, content={"status": "error", "detail": str(exc)})


@app.post("/api/v1/attributions", response_model=AttributionResponse, status_code=201)
def create_attribution(bundle: EvidenceBundle) -> AttributionResponse:
    rankings = attribute_sources(bundle)
    return AttributionResponse(
        hotspot_id=bundle.hotspot_id,
        primary_source=rankings[0].source,
        confidence=rankings[0].score,
        secondary_sources=rankings[1:3],
        rankings=rankings,
    )


@app.post("/api/v1/explanations", response_model=ExplanationResponse, status_code=201)
def create_explanation(bundle: EvidenceBundle) -> ExplanationResponse:
    primary, headline, summary = generate_explanation(bundle)
    return ExplanationResponse(
        hotspot_id=bundle.hotspot_id,
        primary_source=primary.source,
        confidence=primary.score,
        headline=headline,
        summary=summary,
        evidence=primary.evidence,
    )

