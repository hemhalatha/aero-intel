
from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any

from app.command_center.schemas import HotspotSummary
from app.command_center.service import CommandCenterAggregationService
from app.environmental_data.adapters import EnvironmentalIngestionService
from app.environmental_data.normalization import EnvironmentalDataNormalizer, StationMapping, StaticWardResolver
from app.environmental_data.schemas import AirQualityReadingDTO, EnvironmentalIngestionBatch
from app.environmental_data.time_series import EnvironmentalTimeSeriesService
from app.environmental_data.time_series_schemas import HistoricalBaseline, PollutantReading, StationLatestState, WeatherForecastReading, WeatherReading, WindReading
from app.geo_master.schemas import WardRead
from app.heatmap.idw import IDWInterpolator
from app.heatmap.schemas import BoundingBox, HeatmapRequest, StationAQISample
from app.heatmap.service import AQIHeatmapService
from app.hotspot_lifecycle.schemas import HotspotStatus
from app.hotspot_lifecycle.service import HotspotLifecycleService
from app.hotspots.service import HotspotDetectionRules, HotspotDetectionService
from app.intelligence_contract.schemas import IntelligenceConsumer
from app.intelligence_contract.service import IntelligenceContractService
from app.investigations.collectors import CollectorResult
from app.investigations.construction import ConstructionEvidenceCollector, ConstructionPermit
from app.investigations.evidence import EvidenceRecord, EvidenceSupportDirection
from app.investigations.industrial import IndustrialEvidenceCollector, IndustrialUnit
from app.investigations.schemas import InvestigationStatus
from app.investigations.service import InvestigationOrchestrator
from app.investigations.traffic import RoadSegmentTrafficProfile, TrafficDensityReading, TrafficEvidenceCollector
from app.operations_contract.schemas import InterventionWindowType
from app.operations_contract.service import OperationsContractService
from app.sensor_health.schemas import SensorHealthSnapshot
from app.sensor_health.service import SensorHealthRules, SensorHealthService

NOW = datetime(2025, 1, 15, 18, tzinfo=UTC)


@dataclass(frozen=True)
class Scenario:
    key: str
    station_code: str
    ward_code: str
    latitude: float
    longitude: float
    pollutants: dict[str, float]
    expected_supporting_source: str


SCENARIOS = [
    Scenario(
        key="construction_led",
        station_code="BLR-CON-AQ",
        ward_code="BLR-W-CON",
        latitude=12.920,
        longitude=77.620,
        pollutants={"AQI": 248, "PM2.5": 96, "PM10": 242, "NO2": 44, "SO2": 12, "CO": 1.1, "Ozone": 28},
        expected_supporting_source="construction_land_use",
    ),
    Scenario(
        key="traffic_led",
        station_code="BLR-TRF-AQ",
        ward_code="BLR-W-TRF",
        latitude=12.935,
        longitude=77.610,
        pollutants={"AQI": 232, "PM2.5": 78, "PM10": 136, "NO2": 118, "SO2": 16, "CO": 4.4, "Ozone": 32},
        expected_supporting_source="traffic",
    ),
    Scenario(
        key="industrial_led",
        station_code="BLR-IND-AQ",
        ward_code="BLR-W-IND",
        latitude=12.950,
        longitude=77.590,
        pollutants={"AQI": 256, "PM2.5": 72, "PM10": 128, "NO2": 112, "SO2": 126, "CO": 4.2, "Ozone": 34},
        expected_supporting_source="industrial",
    ),
]


class ScenarioAdapter:
    provider_name = "scenario_adapter"

    def fetch(self) -> EnvironmentalIngestionBatch:
        readings = []
        for scenario in SCENARIOS:
            for pollutant, value in scenario.pollutants.items():
                readings.append(
                    AirQualityReadingDTO(
                        provider=self.provider_name,
                        provider_station_id=scenario.station_code,
                        station_name=f"{scenario.key.replace('_', ' ').title()} Station",
                        observed_at=NOW,
                        pollutant=pollutant,
                        value=value,
                        unit="index" if pollutant == "AQI" else "ug/m3",
                        latitude=scenario.latitude,
                        longitude=scenario.longitude,
                        raw_payload={"scenario": scenario.key},
                    )
                )
        readings.append(
            AirQualityReadingDTO.model_construct(
                provider=self.provider_name,
                provider_station_id="BROKEN-STATION",
                station_name="Rejected negative demo",
                observed_at=NOW,
                pollutant="PM2.5",
                value=-7,
                unit="ug/m3",
                latitude=12.91,
                longitude=77.61,
                raw_payload={"scenario": "quality_rejection"},
            )
        )
        return EnvironmentalIngestionBatch(provider=self.provider_name, air_quality_readings=readings)


class UnusedFallbackAdapter:
    provider_name = "unused_fallback"

    def fetch(self) -> EnvironmentalIngestionBatch:
        return EnvironmentalIngestionBatch(provider=self.provider_name, used_fallback=True)

class InMemoryTimeSeriesRepository:
    def __init__(self) -> None:
        self.readings: list[PollutantReading] = []
        self.weather = WeatherReading(location_code="BLR-CENTRE", city="Bengaluru", observed_at=NOW, temperature_c=28, relative_humidity_pct=52)
        self.wind = WindReading(location_code="BLR-CENTRE", city="Bengaluru", observed_at=NOW, wind_speed_kmh=14, wind_direction_degrees=270)

    def store_normalized(self, normalized_readings) -> None:
        for item in normalized_readings:
            self.readings.append(
                PollutantReading(
                    station_code=item.station_code,
                    station_name=item.station_name,
                    ward_code=item.ward_code,
                    observed_at=item.observed_at,
                    pollutant=item.pollutant,
                    value=item.value,
                    unit=item.unit,
                    data_quality_status=item.data_quality_status,
                )
            )

    def get_latest_station_readings(self) -> list[StationLatestState]:
        states = []
        for station_code in sorted({reading.station_code for reading in self.readings}):
            station_readings = [reading for reading in self.readings if reading.station_code == station_code]
            latest_at = max(reading.observed_at for reading in station_readings)
            latest = [reading for reading in station_readings if reading.observed_at == latest_at]
            states.append(
                StationLatestState(
                    station_code=station_code,
                    station_name=latest[0].station_name,
                    ward_code=latest[0].ward_code,
                    observed_at=latest_at,
                    readings=latest,
                    data_quality_status="valid" if all(reading.data_quality_status == "valid" for reading in latest) else "suspect",
                )
            )
        return states

    def get_station_history(self, station_code, start_at, end_at):
        return self.get_readings_for_time_window(station_code=station_code, start_at=start_at, end_at=end_at)

    def get_ward_aqi_history(self, ward_code, start_at, end_at):
        return self.get_readings_for_time_window(ward_code=ward_code, pollutant="AQI", start_at=start_at, end_at=end_at)

    def get_ward_pollutant_history(self, ward_code, pollutant, start_at, end_at):
        return self.get_readings_for_time_window(ward_code=ward_code, pollutant=pollutant, start_at=start_at, end_at=end_at)

    def get_historical_baseline(self, ward_code, pollutant, start_at, end_at, comparison_days):
        baseline_values = {"AQI": 125, "PM2.5": 48, "PM10": 110, "NO2": 48, "SO2": 42, "CO": 1.6, "Ozone": 25}
        value = baseline_values.get(pollutant, 40)
        return [
            PollutantReading(
                station_code=f"baseline-{ward_code}",
                station_name="Historical baseline",
                ward_code=ward_code,
                observed_at=start_at - timedelta(days=day),
                pollutant=pollutant,
                value=value,
                unit="index" if pollutant == "AQI" else "ug/m3",
                data_quality_status="valid",
            )
            for day in (7, 14, 21)
        ]

    def get_current_weather(self, location_code=None):
        return self.weather

    def get_current_wind(self, location_code=None):
        return self.wind

    def get_weather_forecast(self, location_code, start_at, end_at):
        return [
            WeatherForecastReading(
                location_code=location_code,
                forecast_for=start_at + timedelta(hours=1),
                generated_at=NOW,
                temperature_c=27,
                relative_humidity_pct=55,
                wind_speed_kmh=12,
                wind_direction_degrees=270,
                provider="deterministic_seed",
            )
        ]

    def get_readings_for_time_window(self, station_code=None, ward_code=None, pollutant=None, start_at=None, end_at=None):
        readings = self.readings
        if station_code is not None:
            readings = [reading for reading in readings if reading.station_code == station_code]
        if ward_code is not None:
            readings = [reading for reading in readings if reading.ward_code == ward_code]
        if pollutant is not None:
            readings = [reading for reading in readings if reading.pollutant == pollutant]
        if start_at is not None:
            readings = [reading for reading in readings if reading.observed_at >= start_at]
        if end_at is not None:
            readings = [reading for reading in readings if reading.observed_at <= end_at]
        return sorted(readings, key=lambda item: (item.observed_at, item.station_code, item.pollutant))


class InMemorySensorHealthRepository:
    def __init__(self) -> None:
        self.snapshots: dict[str, SensorHealthSnapshot] = {}

    def get_current_statuses(self):
        return list(self.snapshots.values())

    def get_current_status(self, station_code):
        return self.snapshots.get(station_code)

    def get_health_history(self, station_code):
        snapshot = self.snapshots.get(station_code)
        return [snapshot] if snapshot else []

    def save_health_snapshot(self, snapshot):
        self.snapshots[snapshot.station_code] = snapshot


class InMemoryHotspotLifecycleRepository:
    def __init__(self) -> None:
        self.hotspots = {}
        self.observations = []
        self.status_history = []
        self.events = []
        self.next_id = 1

    def find_active_hotspot_for_candidate(self, candidate):
        return next((h for h in self.hotspots.values() if h.ward_code == candidate.ward_code and h.status != HotspotStatus.RESOLVED), None)

    def create_hotspot(self, hotspot):
        saved = hotspot.model_copy(update={"id": self.next_id})
        self.hotspots[saved.id] = saved
        self.next_id += 1
        return saved

    def update_hotspot(self, hotspot):
        self.hotspots[hotspot.id] = hotspot
        return hotspot

    def get_hotspot(self, hotspot_id):
        return self.hotspots.get(hotspot_id)

    def list_hotspots(self, status=None):
        return [item for item in self.hotspots.values() if status is None or item.status == status]

    def add_observation(self, observation):
        saved = observation.model_copy(update={"id": len(self.observations) + 1})
        self.observations.append(saved)
        return saved

    def get_observations(self, hotspot_id):
        return [item for item in self.observations if item.hotspot_id == hotspot_id]

    def add_status_history(self, entry):
        saved = entry.model_copy(update={"id": len(self.status_history) + 1})
        self.status_history.append(saved)
        return saved

    def get_status_history(self, hotspot_id):
        return [item for item in self.status_history if item.hotspot_id == hotspot_id]

    def add_event(self, event):
        saved = event.model_copy(update={"id": len(self.events) + 1})
        self.events.append(saved)
        return saved

    def get_events(self, hotspot_id):
        return [item for item in self.events if item.hotspot_id == hotspot_id]

    def commit(self):
        return None

class InMemoryInvestigationRepository:
    def __init__(self) -> None:
        self.investigations = {}
        self.collector_runs = []
        self.evidence = []
        self.events = []
        self.next_id = 1

    def find_by_hotspot_id(self, hotspot_id):
        return next((item for item in self.investigations.values() if item.hotspot_id == hotspot_id), None)

    def create_investigation(self, investigation):
        saved = investigation.model_copy(update={"id": self.next_id})
        self.investigations[saved.id] = saved
        self.next_id += 1
        return saved

    def update_investigation(self, investigation):
        self.investigations[investigation.id] = investigation
        return investigation

    def get_investigation(self, investigation_id):
        return self.investigations.get(investigation_id)

    def list_investigations(self, status=None):
        return [item for item in self.investigations.values() if status is None or item.status == status]

    def add_collector_run(self, run):
        saved = run.model_copy(update={"id": len(self.collector_runs) + 1})
        self.collector_runs.append(saved)
        return saved

    def update_collector_run(self, run):
        self.collector_runs = [run if item.id == run.id else item for item in self.collector_runs]
        return run

    def get_collector_runs(self, investigation_id):
        return [item for item in self.collector_runs if item.investigation_id == investigation_id]

    def add_evidence_item(self, evidence):
        saved = evidence.model_copy(update={"id": len(self.evidence) + 1})
        self.evidence.append(saved)
        return saved

    def get_evidence_items(self, investigation_id):
        return [item for item in self.evidence if item.investigation_id == investigation_id]

    def add_event(self, event):
        saved = event.model_copy(update={"id": len(self.events) + 1})
        self.events.append(saved)
        return saved

    def get_events(self, investigation_id):
        return [item for item in self.events if item.investigation_id == investigation_id]

    def commit(self):
        return None


class EvidenceServiceAdapter:
    def __init__(self, repository: InMemoryInvestigationRepository) -> None:
        self.repository = repository

    def get_investigation_evidence(self, investigation_id, source_type=None, evidence_type=None):
        records = [self._record(item) for item in self.repository.get_evidence_items(investigation_id)]
        if source_type is not None:
            records = [item for item in records if item.source_type == source_type]
        if evidence_type is not None:
            records = [item for item in records if item.evidence_type == evidence_type]
        return records

    def get_supporting_evidence(self, investigation_id):
        return [item for item in self.get_investigation_evidence(investigation_id) if item.support_direction == EvidenceSupportDirection.SUPPORTS]

    def get_contradictory_evidence(self, investigation_id):
        return [item for item in self.get_investigation_evidence(investigation_id) if item.support_direction == EvidenceSupportDirection.CONTRADICTS]

    def get_evidence_by_type(self, investigation_id, evidence_type):
        return self.get_investigation_evidence(investigation_id, evidence_type=evidence_type)

    @staticmethod
    def _record(item):
        return EvidenceRecord(
            evidence_id=item.id,
            investigation_id=item.investigation_id,
            source_type=item.source_type,
            evidence_type=item.evidence_type,
            detected=item.detected,
            confidence=item.confidence,
            support_direction=EvidenceSupportDirection(item.support_direction),
            raw_details=item.payload,
            data_quality_score=item.data_quality_score,
            collector_name=item.collector_name,
            checked_at=item.checked_at or item.observed_at,
            source=item.source,
            collected_at=item.collected_at,
        )


class ScenarioContextProvider:
    def __init__(self, hotspot_service: HotspotLifecycleService, scenarios: dict[str, Scenario]) -> None:
        self.hotspot_service = hotspot_service
        self.scenarios = scenarios

    def capture_context(self, hotspot_id: int) -> dict[str, Any]:
        detail = self.hotspot_service.get_hotspot_detail(hotspot_id)
        latest = detail.observations[-1]
        scenario = self.scenarios[latest.ward_code]
        return {
            "hotspot": detail.hotspot.model_dump(mode="json"),
            "latest_observation": {
                **latest.model_dump(mode="json"),
                "latitude": scenario.latitude,
                "longitude": scenario.longitude,
            },
        }


class ScenarioTrafficProvider:
    def get_current_density(self, road_segment_code: str, observed_at: datetime):
        high = road_segment_code.startswith("TRAFFIC")
        return TrafficDensityReading(road_segment_code=road_segment_code, observed_at=observed_at, density_index=176 if high else 72, average_speed_kmph=18 if high else 38, provenance="deterministic_seed")

    def get_historical_baseline(self, road_segment_code: str, observed_at: datetime, comparison_days: int):
        return RoadSegmentTrafficProfile(road_segment_code=road_segment_code, comparable_hour=observed_at.hour, average_density_index=100, sample_count=12, provenance="deterministic_seed")


class ScenarioGeoService:
    def get_ward_by_code(self, ward_code):
        return WardRead(id=len(ward_code), city_id=1, code=ward_code, name=ward_code, population=50000, boundary_geojson=None)

    def find_entities_within_radius(self, entity_type, point, radius_meters):
        if entity_type == "road_segments":
            prefix = "TRAFFIC" if point.latitude == 12.935 else "QUIET"
            return [RoadSegment(prefix, f"{prefix} corridor", "arterial", 220)]
        if entity_type == "land_use_zones":
            return [LandUseZone("LU-MIX", "Mixed-use corridor", "mixed_use", 180)]
        return []


class RoadSegment:
    def __init__(self, code, name, road_class, distance_meters):
        self.code = code
        self.name = name
        self.road_class = road_class
        self.distance_meters = distance_meters


class LandUseZone:
    def __init__(self, code, name, category, distance_meters):
        self.code = code
        self.name = name
        self.category = category
        self.distance_meters = distance_meters

class ScenarioConstructionProvider:
    def find_active_permits_within_radius(self, point, radius_meters, observed_at):
        if point.latitude != 12.920:
            return []
        return [
            ConstructionPermit(
                permit_id="CON-001",
                site_name="Metro utility trenching",
                category="infrastructure",
                latitude=point.latitude,
                longitude=point.longitude - 0.003,
                distance_meters=260,
                valid_from=observed_at - timedelta(days=20),
                valid_until=observed_at + timedelta(days=60),
                activity_start=observed_at - timedelta(days=5),
                activity_end=observed_at + timedelta(days=25),
                activity_status="active",
                dust_control_declared=False,
                provenance="deterministic_seed",
            )
        ]


class ScenarioIndustrialProvider:
    def find_units_within_radius(self, point, radius_meters):
        if point.latitude != 12.950:
            return []
        return [
            IndustrialUnit(
                unit_id="IND-001",
                name="Boiler cluster",
                industry_type="boiler_operations",
                pollution_category="red",
                latitude=point.latitude,
                longitude=point.longitude - 0.003,
                distance_meters=320,
                consent_status="valid",
                compliance_status="under_observation",
                consent_valid_until=NOW + timedelta(days=120),
                last_reported_activity_at=NOW - timedelta(minutes=45),
                activity_status="operational",
                regulated_pollutants=["SO2", "NO2", "CO"],
                provenance="deterministic_seed",
            )
        ]


class HotspotProvider:
    def __init__(self, lifecycle_service: HotspotLifecycleService) -> None:
        self.lifecycle_service = lifecycle_service

    def get_current_hotspot_summaries(self):
        return [
            HotspotSummary(
                hotspot_id=str(hotspot.id),
                ward_code=hotspot.ward_code,
                severity=hotspot.severity,
                aqi=hotspot.current_aqi,
                detected_at=hotspot.last_detected_at,
                summary=f"{hotspot.ward_code} AQI {hotspot.current_aqi}",
            )
            for hotspot in self.lifecycle_service.list_hotspots()
        ]


class HeatmapRepository:
    def __init__(self, time_series: EnvironmentalTimeSeriesService, health: SensorHealthService, scenarios: dict[str, Scenario]) -> None:
        self.time_series = time_series
        self.health = health
        self.scenarios = scenarios

    def get_latest_station_aqi_samples(self, bbox=None):
        samples = []
        for state in self.time_series.get_latest_station_readings():
            scenario = self.scenarios[state.ward_code]
            aqi = next(reading.value for reading in state.readings if reading.pollutant == "AQI")
            sensor = self.health.get_station_health(state.station_code)
            samples.append(
                StationAQISample(
                    station_code=state.station_code,
                    station_name=state.station_name,
                    ward_code=state.ward_code,
                    latitude=scenario.latitude,
                    longitude=scenario.longitude,
                    aqi=aqi,
                    data_quality_score=sensor.data_quality_score,
                    sensor_status=sensor.status,
                    is_reliable=sensor.is_reliable,
                )
            )
        return samples


class FailingIndustrialCollector:
    name = "industrial"
    enabled = True

    def collect(self, investigation, context: dict[str, Any]):
        raise RuntimeError("industrial registry unavailable")


class FollowUpCollector:
    name = "construction_land_use"
    enabled = True

    def collect(self, investigation, context: dict[str, Any]):
        return [
            CollectorResult(
                source_type="construction_land_use",
                evidence_type="construction.followup_dust_control_check",
                source="next_best_evidence",
                detected=True,
                support_direction="SUPPORTS",
                confidence=0.74,
                payload={"requested_by": "next_best_evidence", "dust_control_absent": True},
                observed_at=NOW + timedelta(hours=1),
            )
        ]


def build_workflow():
    batch = EnvironmentalIngestionService([ScenarioAdapter()], UnusedFallbackAdapter()).ingest()
    mappings = [
        StationMapping(
            provider="scenario_adapter",
            external_station_id=scenario.station_code,
            internal_station_code=scenario.station_code,
            station_name=f"{scenario.key.replace('_', ' ').title()} Station",
            city="Bengaluru",
            state="Karnataka",
            latitude=scenario.latitude,
            longitude=scenario.longitude,
            ward_code=scenario.ward_code,
        )
        for scenario in SCENARIOS
    ]
    normalizer = EnvironmentalDataNormalizer(mappings, StaticWardResolver({scenario.station_code: scenario.ward_code for scenario in SCENARIOS}))
    normalized = normalizer.normalize(batch)
    repository = InMemoryTimeSeriesRepository()
    repository.store_normalized(normalized.accepted_air_quality_readings)
    time_series = EnvironmentalTimeSeriesService(repository)

    health_repository = InMemorySensorHealthRepository()
    health_service = SensorHealthService(health_repository, rules=SensorHealthRules(required_pollutants={"PM2.5", "PM10", "NO2", "SO2", "CO", "Ozone"}))
    for state in time_series.get_latest_station_readings():
        history = time_series.get_station_history(state.station_code, NOW - timedelta(hours=3), NOW)
        health_repository.save_health_snapshot(health_service.evaluate_station(state, history, evaluated_at=NOW))

    scenario_by_ward = {scenario.ward_code: scenario for scenario in SCENARIOS}
    geo_service = ScenarioGeoService()
    heatmap = AQIHeatmapService(HeatmapRepository(time_series, health_service, scenario_by_ward), IDWInterpolator())
    detector = HotspotDetectionService(time_series, health_service, rules=HotspotDetectionRules(aqi_threshold=200, baseline_deviation_ratio=0.35))
    lifecycle_repository = InMemoryHotspotLifecycleRepository()
    lifecycle = HotspotLifecycleService(lifecycle_repository)
    candidates = detector.detect_hotspot_candidates(now=NOW)
    for candidate in candidates:
        scenario = scenario_by_ward[candidate.ward_code]
        lifecycle.ingest_candidate(candidate, {"scenario": scenario.key, "latitude": scenario.latitude, "longitude": scenario.longitude}, now=NOW)

    collectors = [
        TrafficEvidenceCollector(geo_service=geo_service, traffic_provider=ScenarioTrafficProvider(), environmental_service=time_series),
        ConstructionEvidenceCollector(construction_provider=ScenarioConstructionProvider(), geo_service=geo_service, environmental_service=time_series),
        IndustrialEvidenceCollector(industrial_provider=ScenarioIndustrialProvider(), environmental_service=time_series),
    ]
    investigation_repository = InMemoryInvestigationRepository()
    orchestrator = InvestigationOrchestrator(investigation_repository, ScenarioContextProvider(lifecycle, scenario_by_ward), collectors)
    for event in lifecycle_repository.events:
        if event.event_type == "hotspot.created":
            orchestrator.handle_hotspot_created(event, now=NOW)

    evidence_service = EvidenceServiceAdapter(investigation_repository)
    return {
        "batch": batch,
        "normalized": normalized,
        "time_series": time_series,
        "health": health_service,
        "heatmap": heatmap,
        "command_center": CommandCenterAggregationService(heatmap, health_service, time_series, HotspotProvider(lifecycle)),
        "candidates": candidates,
        "lifecycle": lifecycle,
        "lifecycle_repository": lifecycle_repository,
        "investigations": investigation_repository,
        "orchestrator": orchestrator,
        "evidence_service": evidence_service,
        "operations": OperationsContractService(time_series, lifecycle, health_service, geo_service),
        "intelligence": IntelligenceContractService(lifecycle, orchestrator, investigation_repository, evidence_service, time_series),
        "scenario_by_ward": scenario_by_ward,
    }


def evidence_pattern(evidence_items: list[EvidenceRecord]) -> dict[str, EvidenceSupportDirection]:
    return {item.source_type: item.support_direction for item in evidence_items}


def test_member1_workflow_runs_three_deterministic_hotspot_scenarios_end_to_end() -> None:
    workflow = build_workflow()

    assert workflow["batch"].used_fallback is False
    assert len(workflow["normalized"].accepted_air_quality_readings) == len(SCENARIOS) * 7
    assert [item.reason for item in workflow["normalized"].rejected_records] == ["negative_pollutant_value"]
    assert all(snapshot.is_reliable for snapshot in workflow["health"].get_all_station_health())

    dashboard = workflow["command_center"].get_initial_dashboard(now=NOW)
    heatmap_layer = workflow["heatmap"].get_current_heatmap(
        HeatmapRequest(
            bbox=BoundingBox(min_latitude=12.91, min_longitude=77.58, max_latitude=12.96, max_longitude=77.63),
            grid_resolution=0.025,
        )
    )

    assert dashboard.active_hotspot_count == 3
    assert dashboard.city_average_aqi is not None
    assert heatmap_layer["type"] == "FeatureCollection"
    assert heatmap_layer["features"]
    assert {candidate.ward_code for candidate in workflow["candidates"]} == {scenario.ward_code for scenario in SCENARIOS}

    for investigation in workflow["investigations"].list_investigations():
        assert investigation.status == InvestigationStatus.COMPLETE
        all_evidence = workflow["evidence_service"].get_investigation_evidence(investigation.id)
        assert {item.source_type for item in all_evidence} == {"traffic", "construction_land_use", "industrial"}
        scenario = workflow["scenario_by_ward"][investigation.ward_code]
        pattern = evidence_pattern(all_evidence)
        assert pattern[scenario.expected_supporting_source] == EvidenceSupportDirection.SUPPORTS

    construction_investigation = next(item for item in workflow["investigations"].list_investigations() if item.ward_code == "BLR-W-CON")
    construction_evidence = workflow["evidence_service"].get_investigation_evidence(construction_investigation.id)
    assert evidence_pattern(construction_evidence)["traffic"] == EvidenceSupportDirection.CONTRADICTS
    assert workflow["evidence_service"].get_supporting_evidence(construction_investigation.id)
    assert workflow["evidence_service"].get_contradictory_evidence(construction_investigation.id)

    handoff = workflow["intelligence"].get_contract_by_investigation(construction_investigation.id, pollutants=["PM2.5", "PM10"])
    assert handoff.hotspot_id == construction_investigation.hotspot_id
    assert handoff.evidence_bundle.supporting_evidence
    assert handoff.evidence_bundle.contradictory_evidence
    assert IntelligenceConsumer.EVIDENCE_GRAPH in handoff.supported_consumers
    assert [event.event_type for event in handoff.events][-2:] == [
        "investigation.initial_collection_completed",
        "investigation.completed",
    ]


def test_member1_workflow_exposes_downstream_time_windows_and_followup_collection() -> None:
    workflow = build_workflow()
    traffic_investigation = next(item for item in workflow["investigations"].list_investigations() if item.ward_code == "BLR-W-TRF")

    pollutant_series = workflow["time_series"].get_ward_pollutant_history("BLR-W-TRF", "NO2", NOW - timedelta(hours=1), NOW + timedelta(minutes=1))
    intervention_window = workflow["operations"].get_intervention_verification_window(
        "BLR-W-TRF",
        intervention_at=NOW,
        baseline_hours=2,
        evaluation_hours=3,
        pollutant="NO2",
        intervention_id="signal-retiming-001",
    )
    around_window = workflow["operations"].get_readings_around_timestamp("BLR-W-TRF", selected_at=NOW, context_hours=1, pollutant="CO")

    assert pollutant_series[0].pollutant == "NO2"
    assert intervention_window.pre_intervention_baseline.window_type == InterventionWindowType.PRE_INTERVENTION_BASELINE
    assert intervention_window.predicted_evaluation_window.weather_forecast
    assert intervention_window.actual_post_intervention.window.end_at == NOW + timedelta(hours=3)
    assert around_window.readings[0].pollutant == "CO"

    workflow["orchestrator"].collectors = [FollowUpCollector()]
    updated = workflow["orchestrator"].collect_additional_evidence(
        traffic_investigation.id,
        requested_collectors=["construction_land_use"],
        reason="next_best_evidence",
        now=NOW + timedelta(hours=1),
    )
    followup_evidence = workflow["evidence_service"].get_evidence_by_type(updated.id, "construction.followup_dust_control_check")

    assert updated.id == traffic_investigation.id
    assert followup_evidence[0].raw_details["requested_by"] == "next_best_evidence"
    assert workflow["investigations"].get_events(updated.id)[-2].payload["reason"] == "next_best_evidence"


def test_member1_workflow_preserves_partial_results_when_one_evidence_source_fails() -> None:
    workflow = build_workflow()
    hotspot_event = next(event for event in workflow["lifecycle_repository"].events if event.event_type == "hotspot.created")
    partial_repository = InMemoryInvestigationRepository()
    partial_orchestrator = InvestigationOrchestrator(
        partial_repository,
        ScenarioContextProvider(workflow["lifecycle"], workflow["scenario_by_ward"]),
        [
            TrafficEvidenceCollector(geo_service=ScenarioGeoService(), traffic_provider=ScenarioTrafficProvider(), environmental_service=workflow["time_series"]),
            FailingIndustrialCollector(),
            ConstructionEvidenceCollector(construction_provider=ScenarioConstructionProvider(), geo_service=ScenarioGeoService(), environmental_service=workflow["time_series"]),
        ],
    )

    investigation = partial_orchestrator.handle_hotspot_created(hotspot_event, now=NOW)

    assert investigation.status == InvestigationStatus.PARTIALLY_COMPLETE
    assert len(partial_repository.get_evidence_items(investigation.id)) == 2
    assert {run.status.value for run in partial_repository.get_collector_runs(investigation.id)} == {"SUCCEEDED", "FAILED"}
    assert partial_repository.get_events(investigation.id)[-1].event_type == "investigation.initial_collection_completed"
