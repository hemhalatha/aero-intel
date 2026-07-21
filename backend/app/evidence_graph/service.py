from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

import networkx as nx

from app.intelligence_contract.schemas import IntelligenceModuleContract
from app.investigations.evidence import EvidenceRecord, EvidenceSupportDirection

from .schemas import EvidenceGraphEdge, EvidenceGraphEdgeType, EvidenceGraphNode, EvidenceGraphNodeType, EvidenceGraphResponse

SOURCE_LABELS = {
    "traffic": "Vehicular Emissions",
    "construction_land_use": "Construction Dust",
    "industrial": "Industrial Emissions",
    "road_dust": "Road Dust",
    "biomass": "Biomass or Waste Burning",
}


class EvidenceGraphService:
    def __init__(self, repository=None) -> None:
        self.repository = repository

    def build_graph(self, contract: IntelligenceModuleContract, metadata: dict[str, Any] | None = None) -> EvidenceGraphResponse:
        graph = nx.DiGraph()
        hotspot_key = f"hotspot:{contract.hotspot_id}"
        _add_node(
            graph,
            hotspot_key,
            EvidenceGraphNodeType.HOTSPOT,
            f"Hotspot {contract.hotspot_id}",
            {
                "hotspot_id": contract.hotspot_id,
                "hotspot_uid": contract.hotspot_uid,
                "investigation_id": contract.investigation_id,
                "ward_code": contract.ward_code,
                "station_code": contract.station_code,
                "current_aqi": contract.current_aqi,
                "coordinates": contract.hotspot_coordinates.model_dump() if contract.hotspot_coordinates else None,
                "data_quality": contract.data_quality.model_dump(mode="json"),
            },
        )
        if contract.ward_code:
            ward_key = f"geo:ward:{contract.ward_code}"
            _add_node(graph, ward_key, EvidenceGraphNodeType.GEOGRAPHIC_ENTITY, contract.ward_code, {"entity_type": "ward", "ward_code": contract.ward_code})
            _add_edge(graph, hotspot_key, ward_key, EvidenceGraphEdgeType.NEAR, "located in ward", 1.0, {})

        for pollutant, value in sorted(contract.pollutant_snapshot.items()):
            pollutant_key = f"pollutant:{pollutant}"
            _add_node(graph, pollutant_key, EvidenceGraphNodeType.POLLUTANT, pollutant, {"pollutant": pollutant, "value": value})
            _add_edge(
                graph,
                hotspot_key,
                pollutant_key,
                EvidenceGraphEdgeType.OBSERVED_AT,
                f"observed {pollutant}",
                1.0,
                {"value": value, "station_code": contract.station_code},
            )

        if contract.weather:
            weather_key = f"weather:{contract.weather.location_code}:{contract.weather.observed_at.isoformat()}"
            _add_node(graph, weather_key, EvidenceGraphNodeType.WEATHER_CONDITION, "Weather condition", contract.weather.model_dump(mode="json"))
            _add_edge(graph, weather_key, hotspot_key, EvidenceGraphEdgeType.OBSERVED_AT, "weather observed at hotspot time", 1.0, {})
        if contract.wind:
            wind_key = f"weather:wind:{contract.wind.location_code}:{contract.wind.observed_at.isoformat()}"
            _add_node(graph, wind_key, EvidenceGraphNodeType.WEATHER_CONDITION, "Wind condition", contract.wind.model_dump(mode="json"))
            _add_edge(graph, wind_key, hotspot_key, EvidenceGraphEdgeType.OBSERVED_AT, "wind observed at hotspot time", 1.0, {})

        for item in contract.evidence_bundle.all_evidence:
            self._add_evidence(graph, hotspot_key, item)

        return _response_from_networkx(
            graph,
            hotspot_id=contract.hotspot_id,
            investigation_id=contract.investigation_id,
            graph_version=self._next_version(contract.investigation_id),
            metadata={"source": "intelligence_contract", **(metadata or {})},
        )

    def build_and_persist_graph(self, contract: IntelligenceModuleContract, metadata: dict[str, Any] | None = None) -> EvidenceGraphResponse:
        graph = self.build_graph(contract, metadata)
        if self.repository is None:
            raise RuntimeError("Evidence graph repository is required for persistence.")
        return self.repository.save(graph)

    def get_latest_graph_for_investigation(self, investigation_id: int) -> EvidenceGraphResponse | None:
        if self.repository is None:
            raise RuntimeError("Evidence graph repository is required for lookup.")
        return self.repository.get_latest_for_investigation(investigation_id)

    def get_latest_graph_for_hotspot(self, hotspot_id: int) -> EvidenceGraphResponse | None:
        if self.repository is None:
            raise RuntimeError("Evidence graph repository is required for lookup.")
        return self.repository.get_latest_for_hotspot(hotspot_id)

    def _next_version(self, investigation_id: int) -> int:
        return self.repository.next_version(investigation_id) if self.repository is not None else 1

    def _add_evidence(self, graph: nx.DiGraph, hotspot_key: str, item: EvidenceRecord) -> None:
        evidence_key = f"evidence:{item.evidence_id}"
        _add_node(
            graph,
            evidence_key,
            EvidenceGraphNodeType.EVIDENCE,
            item.evidence_type,
            {
                "evidence_id": item.evidence_id,
                "source_type": item.source_type,
                "evidence_type": item.evidence_type,
                "detected": item.detected,
                "confidence": item.confidence,
                "support_direction": item.support_direction.value,
                "data_quality_score": item.data_quality_score,
                "collector_name": item.collector_name,
                "checked_at": item.checked_at.isoformat(),
                "raw_details": item.raw_details,
            },
        )
        relation = _support_edge_type(item.support_direction)
        _add_edge(graph, evidence_key, hotspot_key, relation, item.support_direction.value.lower(), item.confidence, {"evidence_id": item.evidence_id})

        source_key = _source_key(item.source_type)
        _add_node(
            graph,
            source_key,
            EvidenceGraphNodeType.POLLUTION_SOURCE,
            SOURCE_LABELS.get(item.source_type, item.source_type.replace("_", " ").title()),
            {"source_type": item.source_type},
        )
        _add_edge(graph, evidence_key, source_key, relation, f"{item.support_direction.value.lower()} source", item.confidence, {"evidence_id": item.evidence_id})

        self._add_structured_relationships(graph, evidence_key, hotspot_key, source_key, item)

    def _add_structured_relationships(self, graph: nx.DiGraph, evidence_key: str, hotspot_key: str, source_key: str, item: EvidenceRecord) -> None:
        details = item.raw_details
        proximity = _first_number(details, ["nearest_road_distance_meters", "nearest_site_distance_meters", "nearest_unit_distance_meters", "distance_meters"])
        if proximity is not None:
            _add_edge(graph, source_key, hotspot_key, EvidenceGraphEdgeType.NEAR, "near hotspot", _distance_weight(proximity), {"distance_meters": proximity, "evidence_id": item.evidence_id})
        if _first_bool(details, ["upwind_supported", "wind_transport_supported", "transport_supported"]):
            _add_edge(graph, source_key, hotspot_key, EvidenceGraphEdgeType.UPWIND_OF, "upwind of hotspot", item.confidence, {"evidence_id": item.evidence_id})
        if _first_bool(details, ["rush_hour_correlated"]):
            _add_edge(graph, evidence_key, hotspot_key, EvidenceGraphEdgeType.CORRELATED_WITH, "rush-hour correlated", item.confidence, {"evidence_id": item.evidence_id})
        if _has_active_signal(details):
            _add_edge(graph, evidence_key, hotspot_key, EvidenceGraphEdgeType.ACTIVE_DURING, "active during hotspot", item.confidence, {"evidence_id": item.evidence_id})


def _add_node(graph: nx.DiGraph, key: str, node_type: EvidenceGraphNodeType, label: str, properties: dict[str, Any]) -> None:
    graph.add_node(key, type=node_type, label=label, properties=_json_safe(properties))


def _add_edge(graph: nx.DiGraph, source: str, target: str, edge_type: EvidenceGraphEdgeType, label: str, weight: float, properties: dict[str, Any]) -> None:
    edge_key = f"{source}->{edge_type.value}->{target}"
    graph.add_edge(source, target, key=edge_key, type=edge_type, label=label, weight=round(max(min(weight, 1), 0), 3), properties=_json_safe(properties))


def _response_from_networkx(graph: nx.DiGraph, hotspot_id: int, investigation_id: int, graph_version: int, metadata: dict[str, Any]) -> EvidenceGraphResponse:
    nodes = [
        EvidenceGraphNode(id=key, type=data["type"], label=data["label"], properties=data["properties"])
        for key, data in sorted(graph.nodes(data=True), key=lambda item: item[0])
    ]
    edges = [
        EvidenceGraphEdge(
            id=data["key"],
            source=source,
            target=target,
            type=data["type"],
            label=data["label"],
            weight=data["weight"],
            properties=data["properties"],
        )
        for source, target, data in sorted(graph.edges(data=True), key=lambda item: item[2]["key"])
    ]
    return EvidenceGraphResponse(
        graph_uid=f"eg-{uuid4().hex[:12]}",
        hotspot_id=hotspot_id,
        investigation_id=investigation_id,
        graph_version=graph_version,
        generated_at=datetime.now(UTC),
        nodes=nodes,
        edges=edges,
        graph_metrics={
            "node_count": graph.number_of_nodes(),
            "edge_count": graph.number_of_edges(),
            "weakly_connected_components": nx.number_weakly_connected_components(graph),
        },
        metadata=metadata,
    )


def _support_edge_type(direction: EvidenceSupportDirection) -> EvidenceGraphEdgeType:
    if direction == EvidenceSupportDirection.SUPPORTS:
        return EvidenceGraphEdgeType.SUPPORTS
    if direction == EvidenceSupportDirection.CONTRADICTS:
        return EvidenceGraphEdgeType.CONTRADICTS
    return EvidenceGraphEdgeType.CORRELATED_WITH


def _source_key(source_type: str) -> str:
    if "traffic" in source_type:
        return "source:vehicular_emissions"
    if "construction" in source_type:
        return "source:construction_dust"
    if "industrial" in source_type:
        return "source:industrial_emissions"
    if "road_dust" in source_type:
        return "source:road_dust"
    if "biomass" in source_type or "waste" in source_type:
        return "source:biomass_waste_burning"
    return f"source:{source_type}"


def _first_number(value: Any, keys: list[str]) -> float | None:
    for key in keys:
        found = _deep_find(value, key)
        if isinstance(found, (int, float)):
            return float(found)
    return None


def _first_bool(value: Any, keys: list[str]) -> bool:
    for key in keys:
        found = _deep_find(value, key)
        if isinstance(found, bool):
            return found
    return False


def _deep_find(value: Any, key: str) -> Any | None:
    if isinstance(value, dict):
        if key in value:
            return value[key]
        for child in value.values():
            found = _deep_find(child, key)
            if found is not None:
                return found
    if isinstance(value, list):
        for child in value:
            found = _deep_find(child, key)
            if found is not None:
                return found
    return None


def _has_active_signal(details: dict[str, Any]) -> bool:
    if _first_bool(details, ["rush_hour_correlated"]):
        return True
    if _first_bool(details, ["is_valid_now", "upwind_supported", "wind_transport_supported"]):
        return True
    status = _deep_find(details, "activity_status")
    return status in {"active", "operational"}


def _distance_weight(distance_meters: float) -> float:
    if distance_meters <= 0:
        return 1.0
    return round(max(min(1_000 / distance_meters, 1), 0.1), 3)


def _json_safe(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: _json_safe(child) for key, child in value.items()}
    if isinstance(value, list):
        return [_json_safe(child) for child in value]
    if isinstance(value, datetime):
        return value.isoformat()
    return value
