from typing import Literal

from pydantic import BaseModel, Field, field_validator


class Detection(BaseModel):
    detected: bool
    confidence: float = Field(ge=0, le=1)


class HistoricalPatterns(BaseModel):
    construction_match: float = Field(default=0, ge=0, le=1)
    traffic_match: float = Field(default=0, ge=0, le=1)
    industry_match: float = Field(default=0, ge=0, le=1)
    road_dust_match: float = Field(default=0, ge=0, le=1)
    biomass_match: float = Field(default=0, ge=0, le=1)


class EvidenceBundle(BaseModel):
    hotspot_id: int = Field(gt=0)
    traffic: Detection
    construction: Detection
    industry: Detection
    satellite: Detection
    wind_direction: str = Field(min_length=1, max_length=32)
    wind_speed: float = Field(ge=0, le=150)
    road_dust: Detection = Detection(detected=False, confidence=0)
    biomass_burning: Detection = Detection(detected=False, confidence=0)
    historical_patterns: HistoricalPatterns = HistoricalPatterns()
    pm25: float | None = Field(default=None, ge=0)

    @field_validator("wind_direction")
    @classmethod
    def clean_wind_direction(cls, value: str) -> str:
        return value.strip().title()


class EvidenceFactor(BaseModel):
    label: str
    contribution: float


class SourceRanking(BaseModel):
    source: str
    score: float
    evidence: list[EvidenceFactor]


class AttributionResponse(BaseModel):
    hotspot_id: int
    primary_source: str
    confidence: float
    secondary_sources: list[SourceRanking]
    rankings: list[SourceRanking]
    model_version: Literal["weighted-rules-v1"] = "weighted-rules-v1"


class ExplanationResponse(BaseModel):
    hotspot_id: int
    primary_source: str
    confidence: float
    headline: str
    summary: str
    evidence: list[EvidenceFactor]
    model_version: Literal["weighted-rules-v1"] = "weighted-rules-v1"
