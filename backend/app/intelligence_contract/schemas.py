from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.environmental_data.time_series_schemas import PollutantReading, WeatherReading, WindReading
from app.investigations.evidence import EvidenceRecord


class IntelligenceConsumer(StrEnum):
    POLLUTION_FINGERPRINTING = "pollution_fingerprinting"
    EVIDENCE_GRAPH = "evidence_graph"
    SOURCE_ATTRIBUTION = "source_attribution"
    UNCERTAINTY_ANALYSIS = "uncertainty_analysis"
    NEXT_BEST_EVIDENCE = "next_best_evidence"
    FORECASTING = "forecasting"


class IntelligenceEventType(StrEnum):
    HOTSPOT_CREATED = "hotspot.created"
    EVIDENCE_COLLECTED = "evidence.collected"
    INVESTIGATION_INITIAL_COLLECTION_COMPLETED = "investigation.initial_collection_completed"
    INVESTIGATION_COMPLETED = "investigation.completed"


class HotspotCoordinates(BaseModel):
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    source: str = "detection_context"


class DataQualityContract(BaseModel):
    hotspot_confidence: float = Field(ge=0, le=1)
    latest_station_quality: str | None = None
    evidence_quality_score: float | None = Field(default=None, ge=0, le=1)
    weather_quality: str | None = None
    wind_quality: str | None = None
    notes: list[str] = Field(default_factory=list)


class IntelligenceContractEvent(BaseModel):
    event_type: IntelligenceEventType | str
    published_at: datetime
    source_module: str
    hotspot_id: int | None = None
    investigation_id: int | None = None
    payload: dict[str, Any] = Field(default_factory=dict)


class StandardizedEvidenceBundle(BaseModel):
    investigation_id: int
    all_evidence: list[EvidenceRecord]
    supporting_evidence: list[EvidenceRecord]
    contradictory_evidence: list[EvidenceRecord]
    neutral_evidence: list[EvidenceRecord]


class IntelligenceModuleContract(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "contract_version": "v1",
                "hotspot_id": 101,
                "investigation_id": 17,
                "hotspot_coordinates": {"latitude": 12.917, "longitude": 77.623, "source": "detection_context"},
                "ward_code": "BLR-W-014",
                "station_code": "BLR-SB-AQ",
                "current_aqi": 238,
                "pollutant_snapshot": {"PM2.5": 112, "PM10": 188, "NO2": 74, "SO2": 14, "CO": 1.4, "O3": 24},
                "historical_ward_aqi": [],
                "historical_pollutant_series": {"PM2.5": [], "PM10": [], "NO2": []},
                "weather": {"location_code": "BLR-CENTRE", "city": "Bengaluru"},
                "wind": {"location_code": "BLR-CENTRE", "city": "Bengaluru", "wind_speed_kmh": 16},
                "data_quality": {"hotspot_confidence": 0.91, "latest_station_quality": "valid"},
                "evidence_bundle": {"investigation_id": 17, "all_evidence": [], "supporting_evidence": [], "contradictory_evidence": [], "neutral_evidence": []},
                "events": [{"event_type": "hotspot.created", "source_module": "hotspot_lifecycle"}],
                "supported_consumers": ["pollution_fingerprinting", "evidence_graph", "source_attribution"],
            }
        }
    )

    contract_version: str = "v1"
    generated_at: datetime
    hotspot_id: int
    investigation_id: int
    hotspot_uid: str | None = None
    investigation_uid: str | None = None
    hotspot_coordinates: HotspotCoordinates | None = None
    ward_code: str | None = None
    station_code: str | None = None
    current_aqi: float
    pollutant_snapshot: dict[str, float] = Field(default_factory=dict)
    historical_ward_aqi: list[PollutantReading] = Field(default_factory=list)
    historical_pollutant_series: dict[str, list[PollutantReading]] = Field(default_factory=dict)
    weather: WeatherReading | None = None
    wind: WindReading | None = None
    data_quality: DataQualityContract
    evidence_bundle: StandardizedEvidenceBundle
    events: list[IntelligenceContractEvent] = Field(default_factory=list)
    supported_consumers: list[IntelligenceConsumer] = Field(default_factory=list)


class IntelligenceContractExamplePayload(BaseModel):
    name: str
    description: str
    payload: IntelligenceModuleContract
