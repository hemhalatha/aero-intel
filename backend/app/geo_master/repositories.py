import json
from typing import Any

from geoalchemy2 import Geography
from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session

from .models import LandUseZone, MonitoringStation, RoadSegment, Ward
from .schemas import (
    GeoEntityType,
    GeoPoint,
    LandUseZoneRead,
    MonitoringStationRead,
    RoadSegmentRead,
    WardRead,
)


class GeoMasterRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def find_ward_containing_point(self, point: GeoPoint) -> WardRead | None:
        point_geometry = self._point_geometry(point)
        statement = (
            select(Ward, func.ST_AsGeoJSON(Ward.boundary).label("boundary_geojson"))
            .where(func.ST_Contains(Ward.boundary, point_geometry))
            .limit(1)
        )
        row = self.db.execute(statement).first()
        if row is None:
            return None
        ward, boundary_geojson = row
        return self._ward_to_schema(ward, boundary_geojson)

    def find_entities_within_radius(
        self,
        entity_type: GeoEntityType,
        point: GeoPoint,
        radius_meters: float,
    ) -> list[WardRead | MonitoringStationRead | RoadSegmentRead | LandUseZoneRead]:
        handlers = {
            "wards": self._find_wards_within_radius,
            "monitoring_stations": self._find_monitoring_stations_within_radius,
            "road_segments": self._find_road_segments_within_radius,
            "land_use_zones": self._find_land_use_zones_within_radius,
        }
        return handlers[entity_type](point, radius_meters)

    def calculate_distance_meters(self, origin: GeoPoint, destination: GeoPoint) -> float:
        statement = select(func.ST_DistanceSphere(self._point_geometry(origin), self._point_geometry(destination)))
        return float(self.db.execute(statement).scalar_one())

    def _find_wards_within_radius(self, point: GeoPoint, radius_meters: float) -> list[WardRead]:
        statement = self._radius_statement(Ward, Ward.boundary, point, radius_meters).add_columns(
            func.ST_AsGeoJSON(Ward.boundary).label("boundary_geojson")
        )
        return [self._ward_to_schema(ward, boundary_geojson) for ward, boundary_geojson in self.db.execute(statement)]

    def _find_monitoring_stations_within_radius(
        self,
        point: GeoPoint,
        radius_meters: float,
    ) -> list[MonitoringStationRead]:
        statement = self._radius_statement(MonitoringStation, MonitoringStation.location, point, radius_meters)
        return [MonitoringStationRead.model_validate(station) for station in self.db.scalars(statement)]

    def _find_road_segments_within_radius(self, point: GeoPoint, radius_meters: float) -> list[RoadSegmentRead]:
        statement = self._radius_statement(RoadSegment, RoadSegment.geometry, point, radius_meters).add_columns(
            func.ST_AsGeoJSON(RoadSegment.geometry).label("geometry_geojson")
        )
        return [self._road_segment_to_schema(segment, geometry_geojson) for segment, geometry_geojson in self.db.execute(statement)]

    def _find_land_use_zones_within_radius(self, point: GeoPoint, radius_meters: float) -> list[LandUseZoneRead]:
        statement = self._radius_statement(LandUseZone, LandUseZone.boundary, point, radius_meters).add_columns(
            func.ST_AsGeoJSON(LandUseZone.boundary).label("boundary_geojson")
        )
        return [self._land_use_zone_to_schema(zone, boundary_geojson) for zone, boundary_geojson in self.db.execute(statement)]

    def _radius_statement(
        self,
        model: type[Any],
        geometry_column: Any,
        point: GeoPoint,
        radius_meters: float,
    ) -> Select[tuple[Any]]:
        point_geometry = self._point_geometry(point)
        return (
            select(model)
            .where(func.ST_DWithin(geometry_column.cast(Geography), point_geometry.cast(Geography), radius_meters))
            .order_by(func.ST_DistanceSphere(geometry_column, point_geometry))
        )

    @staticmethod
    def _point_geometry(point: GeoPoint) -> Any:
        return func.ST_SetSRID(func.ST_MakePoint(point.longitude, point.latitude), 4326)

    @staticmethod
    def _decode_geojson(value: str | None) -> dict[str, Any] | None:
        return json.loads(value) if value else None

    def _ward_to_schema(self, ward: Ward, boundary_geojson: str | None) -> WardRead:
        return WardRead(
            id=ward.id,
            city_id=ward.city_id,
            code=ward.code,
            name=ward.name,
            population=ward.population,
            boundary_geojson=self._decode_geojson(boundary_geojson),
        )

    def _road_segment_to_schema(self, segment: RoadSegment, geometry_geojson: str | None) -> RoadSegmentRead:
        return RoadSegmentRead(
            id=segment.id,
            city_id=segment.city_id,
            ward_id=segment.ward_id,
            code=segment.code,
            name=segment.name,
            road_class=segment.road_class,
            length_meters=segment.length_meters,
            geometry_geojson=self._decode_geojson(geometry_geojson),
        )

    def _land_use_zone_to_schema(self, zone: LandUseZone, boundary_geojson: str | None) -> LandUseZoneRead:
        return LandUseZoneRead(
            id=zone.id,
            city_id=zone.city_id,
            ward_id=zone.ward_id,
            code=zone.code,
            name=zone.name,
            category=zone.category,
            boundary_geojson=self._decode_geojson(boundary_geojson),
        )
