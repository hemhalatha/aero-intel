from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from .models import EvidenceGraph, EvidenceGraphEdge as EvidenceGraphEdgeModel, EvidenceGraphNode as EvidenceGraphNodeModel
from .schemas import EvidenceGraphEdge, EvidenceGraphNode, EvidenceGraphResponse


class EvidenceGraphRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def next_version(self, investigation_id: int) -> int:
        latest = self.db.scalar(select(func.max(EvidenceGraph.graph_version)).where(EvidenceGraph.investigation_id == investigation_id))
        return (latest or 0) + 1

    def save(self, graph: EvidenceGraphResponse) -> EvidenceGraphResponse:
        row = EvidenceGraph(
            graph_uid=graph.graph_uid,
            hotspot_id=graph.hotspot_id,
            investigation_id=graph.investigation_id,
            graph_version=graph.graph_version,
            metadata_json={**graph.metadata, "graph_metrics": graph.graph_metrics},
            generated_at=graph.generated_at,
        )
        self.db.add(row)
        self.db.flush()
        for node in graph.nodes:
            self.db.add(
                EvidenceGraphNodeModel(
                    graph_id=row.id,
                    node_key=node.id,
                    node_type=node.type.value,
                    label=node.label,
                    properties=node.properties,
                )
            )
        for edge in graph.edges:
            self.db.add(
                EvidenceGraphEdgeModel(
                    graph_id=row.id,
                    edge_key=edge.id,
                    source_node_key=edge.source,
                    target_node_key=edge.target,
                    edge_type=edge.type.value,
                    label=edge.label,
                    weight=edge.weight,
                    properties=edge.properties,
                )
            )
        self.db.flush()
        self.db.commit()
        return graph.model_copy(update={"graph_id": row.id})

    def get_latest_for_investigation(self, investigation_id: int) -> EvidenceGraphResponse | None:
        statement = (
            select(EvidenceGraph)
            .options(selectinload(EvidenceGraph.nodes), selectinload(EvidenceGraph.edges))
            .where(EvidenceGraph.investigation_id == investigation_id)
            .order_by(EvidenceGraph.graph_version.desc(), EvidenceGraph.id.desc())
            .limit(1)
        )
        row = self.db.scalars(statement).first()
        return self._response(row) if row else None

    def get_latest_for_hotspot(self, hotspot_id: int) -> EvidenceGraphResponse | None:
        statement = (
            select(EvidenceGraph)
            .options(selectinload(EvidenceGraph.nodes), selectinload(EvidenceGraph.edges))
            .where(EvidenceGraph.hotspot_id == hotspot_id)
            .order_by(EvidenceGraph.graph_version.desc(), EvidenceGraph.id.desc())
            .limit(1)
        )
        row = self.db.scalars(statement).first()
        return self._response(row) if row else None

    @staticmethod
    def _response(row: EvidenceGraph) -> EvidenceGraphResponse:
        metadata = dict(row.metadata_json or {})
        metrics = metadata.pop("graph_metrics", {})
        return EvidenceGraphResponse(
            graph_id=row.id,
            graph_uid=row.graph_uid,
            hotspot_id=row.hotspot_id,
            investigation_id=row.investigation_id,
            graph_version=row.graph_version,
            generated_at=row.generated_at,
            nodes=[
                EvidenceGraphNode(
                    id=node.node_key,
                    type=node.node_type,
                    label=node.label,
                    properties=node.properties,
                )
                for node in sorted(row.nodes, key=lambda item: item.node_key)
            ],
            edges=[
                EvidenceGraphEdge(
                    id=edge.edge_key,
                    source=edge.source_node_key,
                    target=edge.target_node_key,
                    type=edge.edge_type,
                    label=edge.label,
                    weight=edge.weight,
                    properties=edge.properties,
                )
                for edge in sorted(row.edges, key=lambda item: item.edge_key)
            ],
            graph_metrics=metrics,
            metadata=metadata,
        )
