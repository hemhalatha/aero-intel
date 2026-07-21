from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from math import atan2, cos, degrees, radians, sin
from typing import Any, Protocol

from pydantic import BaseModel, Field

from app.environmental_data.time_series_schemas import PollutantReading
from app.geo_master.schemas import GeoPoint

from .collectors import CollectorResult


class IndustrialUnit(BaseModel):
    unit_id: str
    name: str
    industry_type: str
    pollution_category: str
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    distance_meters: float = Field(ge=0)
    consent_status: str
    compliance_status: str
    consent_valid_until: datetime | None = None
    last_reported_activity_at: datetime | None = None
    activity_status: str
    regulated_pollutants: list[str] = Field(default_factory=list)
    provenance: str


class IndustrialUnitProvider(Protocol):
    def find_units_within_radius(self, point: GeoPoint, radius_meters: float) -> list[IndustrialUnit]:
        ...


@dataclass(frozen=True)
class IndustrialEvidenceRules:
    search_radius_meters: float = 2_000
    near_unit_threshold_meters: float = 750
    pollutant_window_minutes: int = 120
    activity_alignment_hours: int = 2
    so2_elevated_threshold: float = 80
    no2_elevated_threshold: float = 90
    co_elevated_threshold: float = 3.5
    wind_alignment_degrees: float = 45
    minimum_wind_speed_kmh: float = 4


class SeededIndustrialUnitProvider:
    def find_units_within_radius(self, point: GeoPoint, radius_meters: float) -> list[IndustrialUnit]:
        now = datetime.now(UTC)
        units = [
            IndustrialUnit(
                unit_id="SEEDED-IND-BOILER-01",
                name="Seeded small boiler cluster",
                industry_type="boiler_operations",
                pollution_category="red",
                latitude=point.latitude + 0.001,
                longitude=point.longitude - 0.002,
                distance_meters=320,
                consent_status="valid",
                compliance_status="under_observation",
                consent_valid_until=now + timedelta(days=120),
                last_reported_activity_at=now - timedelta(minutes=45),
                activity_status="operational",
                regulated_pollutants=["SO2", "NO2", "CO"],
                provenance="seeded_demo",
            ),
            IndustrialUnit(
                unit_id="SEEDED-IND-FAB-02",
                name="Seeded fabrication yard",
                industry_type="fabrication",
                pollution_category="orange",
                latitude=point.latitude + 0.002,
                longitude=point.longitude - 0.003,
                distance_meters=690,
                consent_status="valid",
                compliance_status="compliant",
                consent_valid_until=now + timedelta(days=90),
                last_reported_activity_at=now - timedelta(hours=3),
                activity_status="operational",
                regulated_pollutants=["NO2"],
                provenance="seeded_demo",
            ),
        ]
        return [unit for unit in units if unit.distance_meters <= radius_meters]

class PostGISIndustrialUnitProvider:
    """Repository adapter for PostGIS-backed industrial unit registries.

    Expected table shape:
    industrial_units(unit_id, name, industry_type, pollution_category, location,
    consent_status, compliance_status, consent_valid_until,
    last_reported_activity_at, activity_status, regulated_pollutants).
    """

    def __init__(self, db) -> None:
        self.db = db

    def find_units_within_radius(self, point: GeoPoint, radius_meters: float) -> list[IndustrialUnit]:
        from sqlalchemy import text

        statement = text(
            """
            SELECT
                unit_id,
                name,
                industry_type,
                pollution_category,
                ST_Y(location::geometry) AS latitude,
                ST_X(location::geometry) AS longitude,
                ST_DistanceSphere(
                    location::geometry,
                    ST_SetSRID(ST_MakePoint(:longitude, :latitude), 4326)
                ) AS distance_meters,
                consent_status,
                compliance_status,
                consent_valid_until,
                last_reported_activity_at,
                activity_status,
                regulated_pollutants
            FROM industrial_units
            WHERE ST_DWithin(
                location::geography,
                ST_SetSRID(ST_MakePoint(:longitude, :latitude), 4326)::geography,
                :radius_meters
            )
            ORDER BY distance_meters
            """
        )
        rows = self.db.execute(
            statement,
            {"latitude": point.latitude, "longitude": point.longitude, "radius_meters": radius_meters},
        )
        return [
            IndustrialUnit(
                unit_id=row.unit_id,
                name=row.name,
                industry_type=row.industry_type,
                pollution_category=row.pollution_category,
                latitude=row.latitude,
                longitude=row.longitude,
                distance_meters=row.distance_meters,
                consent_status=row.consent_status,
                compliance_status=row.compliance_status,
                consent_valid_until=row.consent_valid_until,
                last_reported_activity_at=row.last_reported_activity_at,
                activity_status=row.activity_status,
                regulated_pollutants=list(row.regulated_pollutants or []),
                provenance="postgis",
            )
            for row in rows
        ]

class IndustrialEvidenceCollector:
    name = "industrial"
    enabled = True

    def __init__(
        self,
        industrial_provider: IndustrialUnitProvider | None = None,
        environmental_service=None,
        rules: IndustrialEvidenceRules | None = None,
    ) -> None:
        self.industrial_provider = industrial_provider or SeededIndustrialUnitProvider()
        self.environmental_service = environmental_service
        self.rules = rules or IndustrialEvidenceRules()

    def collect(self, investigation, context: dict[str, Any]) -> list[CollectorResult]:
        observed_at = self._observed_at(context)
        point = self._hotspot_point(context)
        ward_code = self._ward_code(investigation, context)
        station_code = self._station_code(investigation, context)
        units = self._nearby_units(point)
        pollutant_anomalies = self._pollutant_anomalies(ward_code, station_code, observed_at, context)
        wind_context = self._wind_context(point, units)
        temporal_alignment = self._temporal_alignment(units, observed_at)
        nearest_distance = min((unit.distance_meters for unit in units), default=None)
        compliance_risk_count = sum(1 for unit in units if self._has_compliance_risk(unit, observed_at))
        detected = bool(units)
        support_direction = self._support_direction(detected, pollutant_anomalies, wind_context, temporal_alignment)
        confidence = self._confidence(
            units,
            nearest_distance,
            compliance_risk_count,
            pollutant_anomalies,
            wind_context,
            temporal_alignment,
        )

        return [
            CollectorResult(
                source_type="industrial",
                evidence_type="industrial.activity_signal",
                source="industrial_evidence_collector",
                detected=detected,
                support_direction=support_direction,
                confidence=confidence,
                payload={
                    "ward_code": ward_code,
                    "station_code": station_code,
                    "nearby_industrial_unit_count": len(units),
                    "industrial_units": [self._unit_payload(unit, point, observed_at) for unit in units],
                    "highest_pollution_category": self._highest_pollution_category(units),
                    "compliance_risk_count": compliance_risk_count,
                    "nearest_unit_distance_meters": nearest_distance,
                    "pollutant_anomalies": pollutant_anomalies,
                    "wind_context": wind_context,
                    "upwind_supported": wind_context.get("upwind_supported", False),
                    "temporal_alignment": temporal_alignment,
                    "industrial_data_provenance": self._industrial_provenance(units),
                },
                observed_at=observed_at,
            )
        ]

    def _nearby_units(self, point: GeoPoint | None) -> list[IndustrialUnit]:
        if point is None:
            return []
        return [
            unit
            for unit in self.industrial_provider.find_units_within_radius(point, self.rules.search_radius_meters)
            if unit.distance_meters <= self.rules.search_radius_meters
        ]

    def _pollutant_anomalies(
        self,
        ward_code: str | None,
        station_code: str | None,
        observed_at: datetime,
        context: dict[str, Any],
    ) -> dict[str, dict[str, Any]]:
        anomalies = {}
        thresholds = {
            "SO2": self.rules.so2_elevated_threshold,
            "NO2": self.rules.no2_elevated_threshold,
            "CO": self.rules.co_elevated_threshold,
        }
        for pollutant, threshold in thresholds.items():
            value = self._pollutant_value_from_repository(pollutant, ward_code, station_code, observed_at)
            if value is None:
                value = self._pollutant_value_from_context(pollutant, context)
            if value is not None:
                anomalies[pollutant] = {"value": value, "threshold": threshold, "elevated": value >= threshold}
        return anomalies

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

    def _wind_context(self, hotspot: GeoPoint | None, units: list[IndustrialUnit]) -> dict[str, Any]:
        wind = self.environmental_service.get_current_wind() if self.environmental_service is not None else None
        if hotspot is None or wind is None or wind.wind_direction_degrees is None:
            return {"available": False, "upwind_supported": False}
        downwind_direction = (wind.wind_direction_degrees + 180) % 360
        upwind_units = []
        for unit in units:
            source = GeoPoint(latitude=unit.latitude, longitude=unit.longitude)
            source_to_hotspot = self._bearing_degrees(source, hotspot)
            angular_difference = self._angular_difference(downwind_direction, source_to_hotspot)
            aligned = (
                angular_difference <= self.rules.wind_alignment_degrees
                and (wind.wind_speed_kmh or 0) >= self.rules.minimum_wind_speed_kmh
            )
            if aligned:
                upwind_units.append(
                    {
                        "unit_id": unit.unit_id,
                        "source_to_hotspot_bearing_degrees": round(source_to_hotspot, 1),
                        "angular_difference_degrees": round(angular_difference, 1),
                    }
                )
        return {
            "available": True,
            "wind_direction_degrees": wind.wind_direction_degrees,
            "downwind_direction_degrees": downwind_direction,
            "wind_speed_kmh": wind.wind_speed_kmh,
            "upwind_supported": bool(upwind_units),
            "upwind_units": upwind_units,
        }

    def _temporal_alignment(self, units: list[IndustrialUnit], observed_at: datetime) -> dict[str, Any]:
        recent_units = []
        for unit in units:
            if unit.last_reported_activity_at is None:
                continue
            age_hours = abs((observed_at - unit.last_reported_activity_at).total_seconds()) / 3600
            if age_hours <= self.rules.activity_alignment_hours and unit.activity_status in {"operational", "active"}:
                recent_units.append(
                    {
                        "unit_id": unit.unit_id,
                        "last_reported_activity_at": unit.last_reported_activity_at.isoformat(),
                        "activity_age_hours": round(age_hours, 2),
                    }
                )
        return {
            "recent_activity_count": len(recent_units),
            "recent_activity_units": recent_units,
            "activity_window_hours": self.rules.activity_alignment_hours,
        }

    def _confidence(
        self,
        units: list[IndustrialUnit],
        nearest_distance: float | None,
        compliance_risk_count: int,
        pollutant_anomalies: dict[str, dict[str, Any]],
        wind_context: dict[str, Any],
        temporal_alignment: dict[str, Any],
    ) -> float:
        confidence = 0.2 if units else 0.1
        if self._highest_pollution_category(units) == "red":
            confidence += 0.18
        elif self._highest_pollution_category(units) == "orange":
            confidence += 0.1
        if nearest_distance is not None and nearest_distance <= self.rules.near_unit_threshold_meters:
            confidence += 0.18
        if compliance_risk_count:
            confidence += min(compliance_risk_count * 0.12, 0.2)
        if any(item["elevated"] for item in pollutant_anomalies.values()):
            confidence += 0.16
        if wind_context.get("upwind_supported"):
            confidence += 0.08
        if temporal_alignment.get("recent_activity_count", 0) > 0:
            confidence += 0.08
        return round(min(confidence, 0.95), 2)

    @staticmethod
    def _support_direction(
        detected: bool,
        pollutant_anomalies: dict[str, dict[str, Any]],
        wind_context: dict[str, Any],
        temporal_alignment: dict[str, Any],
    ) -> str:
        pollutant_elevated = any(item["elevated"] for item in pollutant_anomalies.values())
        if detected and pollutant_elevated and (
            wind_context.get("upwind_supported") or temporal_alignment.get("recent_activity_count", 0) > 0
        ):
            return "SUPPORTS"
        if not detected:
            return "NEUTRAL"
        if pollutant_anomalies and not pollutant_elevated and wind_context.get("available") and not wind_context.get("upwind_supported"):
            return "CONTRADICTS"
        return "NEUTRAL"

    @staticmethod
    def _unit_payload(unit: IndustrialUnit, hotspot: GeoPoint | None, observed_at: datetime) -> dict[str, Any]:
        return {
            "unit_id": unit.unit_id,
            "name": unit.name,
            "industry_type": unit.industry_type,
            "pollution_category": unit.pollution_category,
            "latitude": unit.latitude,
            "longitude": unit.longitude,
            "distance_meters": unit.distance_meters,
            "consent_status": unit.consent_status,
            "compliance_status": unit.compliance_status,
            "consent_valid_until": unit.consent_valid_until.isoformat() if unit.consent_valid_until else None,
            "consent_valid_now": unit.consent_valid_until is None or unit.consent_valid_until >= observed_at,
            "last_reported_activity_at": unit.last_reported_activity_at.isoformat() if unit.last_reported_activity_at else None,
            "activity_status": unit.activity_status,
            "regulated_pollutants": unit.regulated_pollutants,
            "source_to_hotspot_bearing_degrees": (
                round(IndustrialEvidenceCollector._bearing_degrees(GeoPoint(latitude=unit.latitude, longitude=unit.longitude), hotspot), 1)
                if hotspot is not None
                else None
            ),
            "has_compliance_risk": IndustrialEvidenceCollector._has_compliance_risk(unit, observed_at),
            "provenance": unit.provenance,
        }

    @staticmethod
    def _has_compliance_risk(unit: IndustrialUnit, observed_at: datetime) -> bool:
        consent_expired = unit.consent_valid_until is not None and unit.consent_valid_until < observed_at
        risky_compliance = unit.compliance_status in {"non_compliant", "under_observation", "violated"}
        risky_consent = unit.consent_status in {"expired", "revoked", "pending"} or consent_expired
        return risky_compliance or risky_consent

    @staticmethod
    def _highest_pollution_category(units: list[IndustrialUnit]) -> str | None:
        ranks = {"green": 1, "white": 1, "orange": 2, "red": 3}
        if not units:
            return None
        return max((unit.pollution_category for unit in units), key=lambda category: ranks.get(category, 0))

    @staticmethod
    def _industrial_provenance(units: list[IndustrialUnit]) -> str:
        provenances = {unit.provenance for unit in units}
        return "seeded_demo" if provenances == {"seeded_demo"} else "mixed_or_live"

    @staticmethod
    def _pollutant_value_from_context(pollutant: str, context: dict[str, Any]) -> float | None:
        snapshot = context.get("latest_observation", {}).get("pollutant_snapshot", {})
        value = snapshot.get(pollutant)
        return float(value) if value is not None else None

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
