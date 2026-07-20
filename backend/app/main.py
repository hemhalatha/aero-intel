from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .attribution import attribute_sources, generate_explanation
from .environmental_data.routes import router as environmental_data_router
from .schemas import AttributionResponse, EvidenceBundle, ExplanationResponse
from .sensor_health.routes import router as sensor_health_router

app = FastAPI(title="AeroIntel", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(environmental_data_router)
app.include_router(sensor_health_router)


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok", "module": "aerointel"}


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
