from datetime import UTC, datetime

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.environmental_data.time_series_schemas import WeatherReading, WindReading
from app.evidence_graph.models import EvidenceGraph, EvidenceGraphEdge, EvidenceGraphNode
from app.evidence_graph.schemas import EvidenceGraphEdgeType, EvidenceGraphNodeType
from app.evidence_graph.repository import EvidenceGraphRepository
from app.evidence_graph.service import EvidenceGraphService
from app.intelligence_contract.schemas import DataQualityContract, IntelligenceModuleContract, StandardizedEvidenceBundle
from app.investigations.evidence import EvidenceRecord, EvidenceSupportDirection

NOW = datetime(2025, 1, 15, 18, tzinfo=UTC)


def make_service():
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(
        engine,
        tables=[EvidenceGraph.__table__, EvidenceGraphNode.__table__, EvidenceGraphEdge.__table__],
    )
    session = sessionmaker(bind=engine)()
    return EvidenceGraphService(EvidenceGraphRepository(session)), session


def evidence(source_type, direction, raw_details):
    return EvidenceRecord(
        evidence_id=len(source_type),
        investigation_id=17,
        source_type=source_type,
        evidence_type=f"{source_type}.signal",
        detected=direction == EvidenceSupportDirection.SUPPORTS,
        confidence=0.84,
        support_direction=direction,
        raw_details=raw_details,
        data_quality_score=0.91,
        collector_name=f"{source_type}_collector",
        checked_at=NOW,
        source=f"{source_type}_collector",
        collected_at=NOW,
    )


def contract():
    items = [
        evidence(
            "traffic",
            EvidenceSupportDirection.SUPPORTS,
            {"max_density_deviation_pct": 72, "rush_hour_correlated": True, "nearest_road_distance_meters": 220},
        ),
        evidence(
            "construction_land_use",
            EvidenceSupportDirection.CONTRADICTS,
            {"nearest_site_distance_meters": 1400, "wind_transport_supported": False},
        ),
        evidence(
            "industrial",
            EvidenceSupportDirection.NEUTRAL,
            {"nearest_unit_distance_meters": 900, "upwind_supported": True},
        ),
    ]
    return IntelligenceModuleContract(
        generated_at=NOW,
        hotspot_id=101,
        investigation_id=17,
        hotspot_uid="hs-101",
        investigation_uid="inv-17",
        ward_code="BLR-W-014",
        station_code="BLR-SB-AQ",
        current_aqi=232,
        pollutant_snapshot={"AQI": 232, "PM2.5": 78, "PM10": 136, "NO2": 118, "CO": 4.4, "SO2": 16},
        weather=WeatherReading(location_code="BLR-CENTRE", city="Bengaluru", observed_at=NOW, temperature_c=28),
        wind=WindReading(location_code="BLR-CENTRE", city="Bengaluru", observed_at=NOW, wind_speed_kmh=14, wind_direction_degrees=270),
        data_quality=DataQualityContract(hotspot_confidence=0.91, evidence_quality_score=0.86, wind_quality="valid"),
        evidence_bundle=StandardizedEvidenceBundle(
            investigation_id=17,
            all_evidence=items,
            supporting_evidence=[items[0]],
            contradictory_evidence=[items[1]],
            neutral_evidence=[items[2]],
        ),
    )


def test_builds_explainable_networkx_graph_from_hotspot_context_and_evidence() -> None:
    service, _ = make_service()

    graph = service.build_graph(contract())

    node_types = {node.type for node in graph.nodes}
    edge_types = {edge.type for edge in graph.edges}
    assert EvidenceGraphNodeType.HOTSPOT in node_types
    assert EvidenceGraphNodeType.EVIDENCE in node_types
    assert EvidenceGraphNodeType.POLLUTION_SOURCE in node_types
    assert EvidenceGraphNodeType.WEATHER_CONDITION in node_types
    assert EvidenceGraphNodeType.GEOGRAPHIC_ENTITY in node_types
    assert EvidenceGraphNodeType.POLLUTANT in node_types
    assert EvidenceGraphEdgeType.SUPPORTS in edge_types
    assert EvidenceGraphEdgeType.CONTRADICTS in edge_types
    assert EvidenceGraphEdgeType.NEAR in edge_types
    assert EvidenceGraphEdgeType.UPWIND_OF in edge_types
    assert EvidenceGraphEdgeType.ACTIVE_DURING in edge_types
    assert EvidenceGraphEdgeType.CORRELATED_WITH in edge_types
    assert EvidenceGraphEdgeType.OBSERVED_AT in edge_types
    assert graph.graph_metrics["node_count"] == len(graph.nodes)
    assert graph.graph_metrics["edge_count"] == len(graph.edges)


def test_persists_and_retrieves_latest_graph_for_reproducible_reasoning() -> None:
    service, _ = make_service()

    saved = service.build_and_persist_graph(contract())
    latest = service.get_latest_graph_for_investigation(17)

    assert latest is not None
    assert latest.graph_id == saved.graph_id
    assert latest.investigation_id == 17
    assert latest.hotspot_id == 101
    assert [node.id for node in latest.nodes] == [node.id for node in saved.nodes]
    assert [edge.id for edge in latest.edges] == [edge.id for edge in saved.edges]


def test_returns_frontend_friendly_graph_json_without_black_box_scores() -> None:
    service, _ = make_service()

    graph = service.build_and_persist_graph(contract())
    payload = graph.model_dump(mode="json")

    assert payload["contract_version"] == "v1"
    assert payload["nodes"][0].keys() >= {"id", "type", "label", "properties"}
    assert payload["edges"][0].keys() >= {"id", "source", "target", "type", "label", "properties"}
    assert "model_score" not in payload
    hotspot = next(node for node in payload["nodes"] if node["type"] == "HOTSPOT")
    assert hotspot["properties"]["current_aqi"] == 232
