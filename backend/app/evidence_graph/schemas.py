from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class EvidenceGraphNodeType(StrEnum):
    HOTSPOT = "HOTSPOT"
    EVIDENCE = "EVIDENCE"
    POLLUTION_SOURCE = "POLLUTION_SOURCE"
    WEATHER_CONDITION = "WEATHER_CONDITION"
    GEOGRAPHIC_ENTITY = "GEOGRAPHIC_ENTITY"
    POLLUTANT = "POLLUTANT"


class EvidenceGraphEdgeType(StrEnum):
    SUPPORTS = "SUPPORTS"
    CONTRADICTS = "CONTRADICTS"
    NEAR = "NEAR"
    UPWIND_OF = "UPWIND_OF"
    ACTIVE_DURING = "ACTIVE_DURING"
    CORRELATED_WITH = "CORRELATED_WITH"
    OBSERVED_AT = "OBSERVED_AT"


class EvidenceGraphNode(BaseModel):
    id: str
    type: EvidenceGraphNodeType
    label: str
    properties: dict[str, Any] = Field(default_factory=dict)


class EvidenceGraphEdge(BaseModel):
    id: str
    source: str
    target: str
    type: EvidenceGraphEdgeType
    label: str
    weight: float = Field(default=1.0, ge=0, le=1)
    properties: dict[str, Any] = Field(default_factory=dict)


class EvidenceGraphResponse(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "contract_version": "v1",
                "graph_id": 1,
                "graph_uid": "eg-abc123",
                "hotspot_id": 101,
                "investigation_id": 17,
                "nodes": [{"id": "hotspot:101", "type": "HOTSPOT", "label": "Hotspot 101"}],
                "edges": [{"id": "evidence:1->source:traffic", "source": "evidence:1", "target": "source:traffic", "type": "SUPPORTS"}],
                "graph_metrics": {"node_count": 12, "edge_count": 18},
            }
        }
    )

    contract_version: str = "v1"
    graph_id: int | None = None
    graph_uid: str
    hotspot_id: int
    investigation_id: int
    graph_version: int = Field(ge=1)
    generated_at: datetime
    nodes: list[EvidenceGraphNode]
    edges: list[EvidenceGraphEdge]
    graph_metrics: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)


class EvidenceGraphBuildRequest(BaseModel):
    persist: bool = True
    metadata: dict[str, Any] = Field(default_factory=dict)
