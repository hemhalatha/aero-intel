from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from math import atan2, cos, degrees, radians, sin
from typing import Any, Protocol

from pydantic import BaseModel, Field

from app.environmental_data.time_series_schemas import PollutantReading
from app.geo_master.schemas import GeoPoint

from .collectors import CollectorResult


class ConstructionPermit(BaseModel):
    permit_id: str
    site_name: str
    category: str
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    distance_meters: float = Field(ge=0)
    valid_from: datetime
    valid_until: datetime
    activity_start: datetime
    activity_end: datetime
    activity_status: str
    dust_control_declared: bool
    provenance: str


class ConstructionPermitProvider(Protocol):
    def find_active_permits_within_radius(
        self,
        point: GeoPoint,
        radius_meters: float,
        observed_at: datetime,
    ) -> list[ConstructionPermit]:
        ...


@dataclass(frozen=True)
class ConstructionEvidenceRules:
    search_radius_meters: float = 1_000
    land_use_radius_meters: float = 1_000
    cluster_radius_meters: float = 250
    near_site_threshold_meters: float = 500
    pollutant_window_minutes: int = 120
    pm10_elevated_threshold: float = 180
    pm25_elevated_threshold: float = 75
    wind_alignment_degrees: float = 45
    minimum_wind_speed_kmh: float = 4


class SeededConstructionPermitProvider:
    def find_active_permits_within_radius(
        self,
        point: GeoPoint,
        radius_meters: float,
        observed_at: datetime,
    ) -> list[ConstructionPermit]:
        permits = [
            ConstructionPermit(
                permit_id="SEEDED-CON-ORR-01",
                site_name="Seeded metro utility trenching",
                category="infrastructure",
                latitude=point.latitude + 0.001,
                longitude=point.longitude - 0.002,
                distance_meters=260,
                valid_from=observed_at - timedelta(days=30),
                valid_until=observed_at + timedelta(days=60),
                activity_start=observed_at - timedelta(days=12),
                activity_end=observed_at + timedelta(days=18),
                activity_status="active",
                dust_control_declared=False,
                provenance="seeded_demo",
            ),
            ConstructionPermit(
                permit_id="SEEDED-CON-CBD-02",
                site_name="Seeded commercial excavation",
                category="commercial",
                latitude=point.latitude + 0.0012,
                longitude=point.longitude - 0.0018,
                distance_meters=310,
                valid_from=observed_at - timedelta(days=18),
                valid_until=observed_at + timedelta(days=90),
                activity_start=observed_at - timedelta(days=5),
                activity_end=observed_at + timedelta(days=45),
                activity_status="active",
                dust_control_declared=True,
                provenance="seeded_demo",
            ),
        ]
        return [permit for permit in permits if permit.distance_meters <= radius_meters]


class PostGISConstructionPermitProvider:
    """Repository adapter for PostGIS-backed construction permits.

    The expected table shape is intentionally simple for integration:
    construction_permits(id, permit_id, site_name, category, location,
    valid_from, valid_until, activity_start, activity_end, activity_status,
    dust_control_declared). The collector only relies on this protocol, so a
    city-specific permit schema can be adapted without changing collector logic.
    """

    def __init__(self, db) -> None:
        self.db = db

    def find_active_permits_within_radius(
        self,
        point: GeoPoint,
        radius_meters: float,
        observed_at: datetime,
    ) -> list[ConstructionPermit]:
        from sqlalchemy import text

        statement = text(
            """
            SELECT
                permit_id,
                site_name,
                category,
                ST_Y(location::geometry) AS latitude,
                ST_X(location::geometry) AS longitude,
                ST_DistanceSphere(
                    location::geometry,
                    ST_SetSRID(ST_MakePoint(:longitude, :latitude), 4326)
                ) AS distance_meters,
                valid_from,
                valid_until,
                activity_start,
                activity_end,
                activity_status,
                dust_control_declared
            FROM construction_permits
            WHERE ST_DWithin(
                location::geography,
                ST_SetSRID(ST_MakePoint(:longitude, :latitude), 4326)::geography,
                :radius_meters
            )
            AND valid_from <= :observed_at
            AND valid_until >= :observed_at
            AND activity_start <= :observed_at
            AND activity_end >= :observed_at
            AND activity_status = 'active'
            ORDER BY distance_meters
            """
        )
        rows = self.db.execute(
            statement,
            {
                "latitude": point.latitude,
                "longitude": point.longitude,
                "radius_meters": radius_meters,
                "observed_at": observed_at,
            },
        )
        return [
            ConstructionPermit(
                permit_id=row.permit_id,
                site_name=row.site_name,
                category=row.category,
                latitude=row.latitude,
                longitude=row.longitude,
                distance_meters=row.distance_meters,
                valid_from=row.valid_from,
                valid_until=row.valid_until,
                activity_start=row.activity_start,
                activity_end=row.activity_end,
                activity_status=row.activity_status,
                dust_control_declared=row.dust_control_declared,
                provenance="postgis",
            )
            for row in rows
        ]


class SeededLandUseZone:
    def __init__(self, code: str, name: str, category: str, distance_meters: float) -> None:
        self.code = code
        self.name = name
        self.category = category
        self.distance_meters = distance_meters


class ConstructionEvidenceCollector:
    name = "construction_land_use"
    enabled = True

    def __init__(
        self,
        construction_provider: ConstructionPermitProvider | None = None,
        geo_service=None,
        environmental_service=None,
        rules: ConstructionEvidenceRules | None = None,
    ) -> None:
        self.construction_provider = construction_provider or SeededConstructionPermitProvider()
        self.geo_service = geo_service
        self.environmental_service = environmental_service
        self.rules = rules or ConstructionEvidenceRules()

    def collect(self, investigation, context: dict[str, Any]) -> list[CollectorResult]:
        observed_at = self._observed_at(context)
        point = self._hotspot_point(context)
        ward_code = self._ward_code(investigation, context)
        station_code = self._station_code(investigation, context)
        permits = self._active_permits(point, observed_at)
        land_use_context = self._land_use_context(point)
        pm_context = self._pm_context(ward_code, station_code, observed_at, context)
        wind_context = self._wind_context(point, permits)
        cluster_count = self._cluster_count(permits)
        nearest_distance = min((permit.distance_meters for permit in permits), default=None)
        detected = bool(permits)
        support_direction = self._support_direction(detected, pm_context, wind_context)
        confidence = self._confidence(permits, nearest_distance, cluster_count, pm_context, wind_context)

        return [
            CollectorResult(
                source_type="construction_land_use",
                evidence_type="construction.land_use_activity",
                source="construction_land_use_collector",
                detected=detected,
                support_direction=support_direction,
                confidence=confidence,
                payload={
                    "ward_code": ward_code,
                    "station_code": station_code,
                    "active_permit_count": len(permits),
                    "active_permits": [self._permit_payload(permit, point, observed_at) for permit in permits],
                    "construction_cluster_count": cluster_count,
                    "nearest_site_distance_meters": nearest_distance,
                    "land_use_context": land_use_context,
                    "pm_context": pm_context,
                    "wind_context": wind_context,
                    "wind_transport_supported": wind_context.get("transport_supported", False),
                    "permit_data_provenance": self._permit_provenance(permits),
                },
                observed_at=observed_at,
            )
        ]

    def _active_permits(self, point: GeoPoint | None, observed_at: datetime) -> list[ConstructionPermit]:
        if point is None:
            return []
        permits = self.construction_provider.find_active_permits_within_radius(
            point,
            self.rules.search_radius_meters,
            observed_at,
        )
        return [
            permit
            for permit in permits
            if self._permit_active_at(permit, observed_at) and permit.distance_meters <= self.rules.search_radius_meters
        ]

    def _land_use_context(self, point: GeoPoint | None) -> list[dict[str, Any]]:
        if point is not None and self.geo_service is not None:
            zones = self.geo_service.find_entities_within_radius(
                "land_use_zones",
                point,
                self.rules.land_use_radius_meters,
            )
            if zones:
                return [self._land_use_payload(zone) for zone in zones]
        return [
            self._land_use_payload(SeededLandUseZone("SEEDED-LU-MIX", "Seeded mixed-use corridor", "mixed_use", 160)),
            self._land_use_payload(SeededLandUseZone("SEEDED-LU-RES", "Seeded residential blocks", "residential", 520)),
        ]

    def _pm_context(
        self,
        ward_code: str | None,
        station_code: str | None,
        observed_at: datetime,
        context: dict[str, Any],
    ) -> dict[str, dict[str, Any]]:
        patterns = {}
        thresholds = {"PM10": self.rules.pm10_elevated_threshold, "PM2.5": self.rules.pm25_elevated_threshold}
        for pollutant, threshold in thresholds.items():
            value = self._pollutant_value_from_repository(pollutant, ward_code, station_code, observed_at)
            if value is None:
                value = self._pollutant_value_from_context(pollutant, context)
            if value is not None:
                patterns[pollutant] = {"value": value, "threshold": threshold, "elevated": value >= threshold}
        return patterns

    def _wind_context(self, hotspot: GeoPoint | None, permits: list[ConstructionPermit]) -> dict[str, Any]:
        wind = self.environmental_service.get_current_wind() if self.environmental_service is not None else None
        if hotspot is None or wind is None or wind.wind_direction_degrees is None:
            return {"available": False, "transport_supported": False}
        downwind_direction = (wind.wind_direction_degrees + 180) % 360
        aligned_sites = []
        for permit in permits:
            site = GeoPoint(latitude=permit.latitude, longitude=permit.longitude)
            site_to_hotspot = self._bearing_degrees(site, hotspot)
            angular_difference = self._angular_difference(downwind_direction, site_to_hotspot)
            aligned = (
                angular_difference <= self.rules.wind_alignment_degrees
                and (wind.wind_speed_kmh or 0) >= self.rules.minimum_wind_speed_kmh
            )
            if aligned:
                aligned_sites.append(
                    {
                        "permit_id": permit.permit_id,
                        "site_to_hotspot_bearing_degrees": round(site_to_hotspot, 1),
                        "angular_difference_degrees": round(angular_difference, 1),
                    }
                )
        return {
            "available": True,
            "wind_direction_degrees": wind.wind_direction_degrees,
            "downwind_direction_degrees": downwind_direction,
            "wind_speed_kmh": wind.wind_speed_kmh,
            "transport_supported": bool(aligned_sites),
            "aligned_sites": aligned_sites,
        }

    def _pollutant_value_from_repository(
        self,
        pollutant: str,
        ward_code: str | None,
        station_code: str | None,
        observed_at: datetime,
    ) -> float | None:
        if self.environmental_service is None:
            return None
        readings: list[PollutantReading] = self.environmental_service.get_readings_for_time_window(
            station_code=station_code,
            ward_code=ward_code,
            pollutant=pollutant,
            start_at=observed_at - timedelta(minutes=self.rules.pollutant_window_minutes),
            end_at=observed_at,
        )
        valid = [reading.value for reading in readings if reading.data_quality_status == "valid"]
        return max(valid) if valid else None

    @staticmethod
    def _permit_active_at(permit: ConstructionPermit, observed_at: datetime) -> bool:
        return (
            permit.valid_from <= observed_at <= permit.valid_until
            and permit.activity_start <= observed_at <= permit.activity_end
            and permit.activity_status == "active"
        )

    def _cluster_count(self, permits: list[ConstructionPermit]) -> int:
        if not permits:
            return 0
        remaining = set(range(len(permits)))
        clusters = 0
        while remaining:
            clusters += 1
            stack = [remaining.pop()]
            while stack:
                current = stack.pop()
                current_point = GeoPoint(latitude=permits[current].latitude, longitude=permits[current].longitude)
                nearby = [
                    index
                    for index in list(remaining)
                    if self._distance_meters(
                        current_point,
                        GeoPoint(latitude=permits[index].latitude, longitude=permits[index].longitude),
                    )
                    <= self.rules.cluster_radius_meters
                ]
                for index in nearby:
                    remaining.remove(index)
                    stack.append(index)
        return clusters

    def _confidence(
        self,
        permits: list[ConstructionPermit],
        nearest_distance: float | None,
        cluster_count: int,
        pm_context: dict[str, dict[str, Any]],
        wind_context: dict[str, Any],
    ) -> float:
        confidence = 0.2 if permits else 0.1
        if nearest_distance is not None and nearest_distance <= self.rules.near_site_threshold_meters:
            confidence += 0.25
        if cluster_count > 0:
            confidence += min(cluster_count * 0.1, 0.2)
        if any(item["elevated"] for item in pm_context.values()):
            confidence += 0.2
        if wind_context.get("transport_supported"):
            confidence += 0.15
        return round(min(confidence, 0.95), 2)

    @staticmethod
    def _support_direction(
        detected: bool,
        pm_context: dict[str, dict[str, Any]],
        wind_context: dict[str, Any],
    ) -> str:
        pm_elevated = any(item["elevated"] for item in pm_context.values())
        if detected and (pm_elevated or wind_context.get("transport_supported")):
            return "SUPPORTS"
        if not detected:
            return "NEUTRAL"
        if pm_context and not pm_elevated and wind_context.get("available") and not wind_context.get("transport_supported"):
            return "CONTRADICTS"
        return "NEUTRAL"

    @staticmethod
    def _permit_payload(permit: ConstructionPermit, hotspot: GeoPoint | None, observed_at: datetime) -> dict[str, Any]:
        return {
            "permit_id": permit.permit_id,
            "site_name": permit.site_name,
            "category": permit.category,
            "latitude": permit.latitude,
            "longitude": permit.longitude,
            "distance_meters": permit.distance_meters,
            "valid_from": permit.valid_from.isoformat(),
            "valid_until": permit.valid_until.isoformat(),
            "activity_start": permit.activity_start.isoformat(),
            "activity_end": permit.activity_end.isoformat(),
            "activity_status": permit.activity_status,
            "is_valid_now": ConstructionEvidenceCollector._permit_active_at(permit, observed_at),
            "dust_control_declared": permit.dust_control_declared,
            "site_to_hotspot_bearing_degrees": (
                round(ConstructionEvidenceCollector._bearing_degrees(GeoPoint(latitude=permit.latitude, longitude=permit.longitude), hotspot), 1)
                if hotspot is not None
                else None
            ),
            "provenance": permit.provenance,
        }

    @staticmethod
    def _land_use_payload(zone: Any) -> dict[str, Any]:
        return {
            "code": getattr(zone, "code", None),
            "name": getattr(zone, "name", None),
            "category": getattr(zone, "category", "unknown"),
            "distance_meters": getattr(zone, "distance_meters", None),
        }

    @staticmethod
    def _pollutant_value_from_context(pollutant: str, context: dict[str, Any]) -> float | None:
        snapshot = context.get("latest_observation", {}).get("pollutant_snapshot", {})
        value = snapshot.get(pollutant)
        return float(value) if value is not None else None

    @staticmethod
    def _permit_provenance(permits: list[ConstructionPermit]) -> str:
        provenances = {permit.provenance for permit in permits}
        return "seeded_demo" if provenances == {"seeded_demo"} else "mixed_or_postgis"

    @staticmethod
    def _observed_at(context: dict[str, Any]) -> datetime:
        raw = context.get("latest_observation", {}).get("observed_at") or context.get("observed_at")
        if isinstance(raw, datetime):
            return raw
        if isinstance(raw, str):
            return datetime.fromisoformat(raw)
        return datetime.now(UTC)

    @staticmethod
    def _ward_code(investigation, context: dict[str, Any]) -> str | None:
        return investigation.ward_code or context.get("latest_observation", {}).get("ward_code") or context.get("hotspot", {}).get("ward_code")

    @staticmethod
    def _station_code(investigation, context: dict[str, Any]) -> str | None:
        return investigation.station_code or context.get("latest_observation", {}).get("station_code") or context.get("hotspot", {}).get("station_code")

    @staticmethod
    def _hotspot_point(context: dict[str, Any]) -> GeoPoint | None:
        latest = context.get("latest_observation", {})
        latitude = latest.get("latitude")
        longitude = latest.get("longitude")
        if latitude is None or longitude is None:
            return None
        return GeoPoint(latitude=latitude, longitude=longitude)

    @staticmethod
    def _bearing_degrees(origin: GeoPoint, destination: GeoPoint) -> float:
        origin_lat = radians(origin.latitude)
        destination_lat = radians(destination.latitude)
        delta_lon = radians(destination.longitude - origin.longitude)
        y = sin(delta_lon) * cos(destination_lat)
        x = cos(origin_lat) * sin(destination_lat) - sin(origin_lat) * cos(destination_lat) * cos(delta_lon)
        return (degrees(atan2(y, x)) + 360) % 360

    @staticmethod
    def _angular_difference(first: float, second: float) -> float:
        return abs((first - second + 180) % 360 - 180)

    @staticmethod
    def _distance_meters(origin: GeoPoint, destination: GeoPoint) -> float:
        from app.geo_master.services import calculate_distance_meters

        return calculate_distance_meters(origin, destination)
