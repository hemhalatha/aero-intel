from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class FingerprintSource(StrEnum):
    CONSTRUCTION_DUST = "Construction Dust"
    VEHICULAR_EMISSIONS = "Vehicular Emissions"
    INDUSTRIAL_EMISSIONS = "Industrial Emissions"
    ROAD_DUST = "Road Dust"
    BIOMASS_WASTE_BURNING = "Biomass or Waste Burning"


class FeatureKind(StrEnum):
    RATIO = "ratio"
    CONCENTRATION = "concentration"
    PERCENT = "percent"
    DISTANCE_METERS = "distance_meters"
    BOOLEAN = "boolean"
    SCORE = "score"


class FingerprintFeatureValue(BaseModel):
    name: str
    kind: FeatureKind
    value: float | bool | None = None
    available: bool
    unit: str | None = None
    data_quality_score: float = Field(default=1.0, ge=0, le=1)
    source: str
    notes: list[str] = Field(default_factory=list)


class ExtractedFingerprintFeatures(BaseModel):
    pm10_pm25_ratio: FingerprintFeatureValue
    no2_level: FingerprintFeatureValue
    co_level: FingerprintFeatureValue
    so2_level: FingerprintFeatureValue
    traffic_anomaly: FingerprintFeatureValue
    rush_hour_correlation: FingerprintFeatureValue
    construction_proximity: FingerprintFeatureValue
    industrial_proximity: FingerprintFeatureValue
    wind_alignment: FingerprintFeatureValue
    temporal_persistence: FingerprintFeatureValue
    biomass_burning_marker: FingerprintFeatureValue


class FingerprintPatternScore(BaseModel):
    source: FingerprintSource
    score: float = Field(ge=0, le=1)
    rank: int = Field(ge=1)
    matched_features: list[str] = Field(default_factory=list)
    weak_or_missing_features: list[str] = Field(default_factory=list)
    contribution_breakdown: dict[str, float] = Field(default_factory=dict)


class PollutionFingerprintResult(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "contract_version": "v1",
                "hotspot_id": 101,
                "investigation_id": 17,
                "is_final_attribution": False,
                "features": {"pm10_pm25_ratio": {"value": 1.74, "available": True}},
                "pattern_scores": {"Vehicular Emissions": {"score": 0.86, "rank": 1}},
                "missing_fingerprint_features": ["biomass_burning_marker"],
                "data_quality_confidence": 0.89,
            }
        }
    )

    contract_version: str = "v1"
    generated_at: datetime
    hotspot_id: int
    investigation_id: int
    ward_code: str | None = None
    station_code: str | None = None
    is_final_attribution: bool = False
    features: ExtractedFingerprintFeatures
    pattern_scores: dict[FingerprintSource, FingerprintPatternScore]
    missing_fingerprint_features: list[str] = Field(default_factory=list)
    data_quality_confidence: float = Field(ge=0, le=1)
    notes: list[str] = Field(default_factory=list)


class FingerprintPatternRule(BaseModel):
    feature_name: str
    weight: float = Field(gt=0)
    min_value: float | None = None
    max_value: float | None = None
    expected_bool: bool | None = None
    missing_penalty: float = Field(default=0.0, ge=0, le=1)


class FingerprintPatternConfig(BaseModel):
    source: FingerprintSource
    rules: list[FingerprintPatternRule]
    description: str


class PollutionFingerprintExamplePayload(BaseModel):
    name: str
    description: str
    payload: dict[str, Any]
