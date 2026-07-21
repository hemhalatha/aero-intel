from collections.abc import Iterable
from math import asin, cos, radians, sin, sqrt
from typing import Any, Protocol

from .schemas import GeoEntityType, GeoPoint

EARTH_RADIUS_METERS = 6_371_000


class SupportsCoordinates(Protocol):
    latitude: float
    longitude: float


class GeoMasterRepositoryProtocol(Protocol):
    def get_ward_by_code(self, ward_code: str) -> Any | None:
        ...

    def find_ward_containing_point(self, point: GeoPoint) -> Any | None:
        ...

    def find_entities_within_radius(
        self,
        entity_type: GeoEntityType,
        point: GeoPoint,
        radius_meters: float,
    ) -> list[Any]:
        ...

    def calculate_distance_meters(self, origin: GeoPoint, destination: GeoPoint) -> float:
        ...


def calculate_distance_meters(origin: GeoPoint, destination: GeoPoint) -> float:
    """Calculate great-circle distance with the Haversine formula."""
    origin_lat = radians(origin.latitude)
    destination_lat = radians(destination.latitude)
    delta_lat = radians(destination.latitude - origin.latitude)
    delta_lon = radians(destination.longitude - origin.longitude)

    haversine = sin(delta_lat / 2) ** 2 + cos(origin_lat) * cos(destination_lat) * sin(delta_lon / 2) ** 2
    return 2 * EARTH_RADIUS_METERS * asin(sqrt(haversine))


class GeoMasterService:
    def __init__(self, repository: GeoMasterRepositoryProtocol | None) -> None:
        self.repository = repository

    def get_ward_by_code(self, ward_code: str) -> Any | None:
        if self.repository is None:
            raise RuntimeError("Geo master repository is required for ward lookup.")
        return self.repository.get_ward_by_code(ward_code)

    def find_ward_containing_point(self, point: GeoPoint) -> Any | None:
        if self.repository is None:
            raise RuntimeError("Geo master repository is required for ward lookup.")
        return self.repository.find_ward_containing_point(point)

    def find_entities_within_radius(
        self,
        entity_type: GeoEntityType,
        point: GeoPoint,
        radius_meters: float,
    ) -> list[Any]:
        if self.repository is None:
            raise RuntimeError("Geo master repository is required for radius search.")
        return self.repository.find_entities_within_radius(entity_type, point, radius_meters)

    def calculate_distance_meters(self, origin: GeoPoint, destination: GeoPoint) -> float:
        if self.repository is None:
            return calculate_distance_meters(origin, destination)
        return self.repository.calculate_distance_meters(origin, destination)

    def filter_entities_within_radius(
        self,
        origin: GeoPoint,
        entities: Iterable[SupportsCoordinates],
        radius_meters: float,
    ) -> list[SupportsCoordinates]:
        return [
            entity
            for entity in entities
            if calculate_distance_meters(
                origin,
                GeoPoint(latitude=entity.latitude, longitude=entity.longitude),
            )
            <= radius_meters
        ]
