from datetime import UTC, datetime, timedelta
from typing import Protocol

from app.environmental_data.time_series import EnvironmentalTimeSeriesService
from app.hotspot_lifecycle.schemas import HotspotDetail, HotspotEventRecord
from app.hotspot_lifecycle.service import HotspotLifecycleService
from app.investigations.evidence import EvidenceRecord, EvidenceService, EvidenceSupportDirection
from app.investigations.schemas import InvestigationDetail, InvestigationEventRecord, InvestigationStatus
from app.investigations.service import InvestigationOrchestrator

from .schemas import (
    DataQualityContract,
    HotspotCoordinates,
    IntelligenceConsumer,
    IntelligenceContractEvent,
    IntelligenceEventType,
    IntelligenceModuleContract,
    StandardizedEvidenceBundle,
)

DEFAULT_POLLUTANTS = ["PM2.5", "PM10", "NO2", "SO2", "CO", "O3"]


class InvestigationLookupProtocol(Protocol):
    def find_by_hotspot_id(self, hotspot_id: int):
        ...


class IntelligenceContractService:
    def __init__(
        self,
        hotspot_service: HotspotLifecycleService,
        investigation_service: InvestigationOrchestrator,
        investigation_lookup: InvestigationLookupProtocol,
        evidence_service: EvidenceService,
        environmental_service: EnvironmentalTimeSeriesService,
    ) -> None:
        self.hotspot_service = hotspot_service
        self.investigation_service = investigation_service
        self.investigation_lookup = investigation_lookup
        self.evidence_service = evidence_service
        self.environmental_service = environmental_service

    def get_contract_by_hotspot(
        self,
        hotspot_id: int,
        start_at: datetime | None = None,
        end_at: datetime | None = None,
        pollutants: list[str] | None = None,
    ) -> IntelligenceModuleContract:
        investigation = self.investigation_lookup.find_by_hotspot_id(hotspot_id)
        if investigation is None or investigation.id is None:
            raise ValueError("Investigation not found for hotspot.")
        return self.get_contract_by_investigation(investigation.id, start_at, end_at, pollutants)

    def get_contract_by_investigation(
        self,
        investigation_id: int,
        start_at: datetime | None = None,
        end_at: datetime | None = None,
        pollutants: list[str] | None = None,
    ) -> IntelligenceModuleContract:
        generated_at = datetime.now(UTC)
        end_at = end_at or generated_at
        start_at = start_at or end_at - timedelta(hours=24)
        pollutants = pollutants or DEFAULT_POLLUTANTS

        investigation_detail = self.investigation_service.get_investigation_detail(investigation_id)
        hotspot_id = investigation_detail.investigation.hotspot_id
        hotspot_detail = self.hotspot_service.get_hotspot_detail(hotspot_id)
        latest_observation = hotspot_detail.observations[-1] if hotspot_detail.observations else None
        ward_code = latest_observation.ward_code if latest_observation else hotspot_detail.hotspot.ward_code
        current_aqi = latest_observation.aqi if latest_observation else hotspot_detail.hotspot.current_aqi
        pollutant_snapshot = latest_observation.pollutant_snapshot if latest_observation else {}

        evidence_bundle = self._evidence_bundle(investigation_id)
        weather = self.environmental_service.get_current_weather()
        wind = self.environmental_service.get_current_wind()
        historical_pollutants = {
            pollutant: self.environmental_service.get_ward_pollutant_history(ward_code, pollutant, start_at, end_at)
            for pollutant in pollutants
            if ward_code
        }

        return IntelligenceModuleContract(
            generated_at=generated_at,
            hotspot_id=hotspot_id,
            investigation_id=investigation_id,
            hotspot_uid=hotspot_detail.hotspot.hotspot_uid,
            investigation_uid=investigation_detail.investigation.investigation_uid,
            hotspot_coordinates=self._coordinates(hotspot_detail),
            ward_code=ward_code,
            station_code=latest_observation.station_code if latest_observation else hotspot_detail.hotspot.station_code,
            current_aqi=current_aqi,
            pollutant_snapshot=pollutant_snapshot,
            historical_ward_aqi=self.environmental_service.get_ward_aqi_history(ward_code, start_at, end_at) if ward_code else [],
            historical_pollutant_series=historical_pollutants,
            weather=weather,
            wind=wind,
            data_quality=self._data_quality(hotspot_detail, investigation_detail, evidence_bundle, weather, wind),
            evidence_bundle=evidence_bundle,
            events=self._events(hotspot_detail.events, investigation_detail.events, investigation_id),
            supported_consumers=list(IntelligenceConsumer),
        )

    def _evidence_bundle(self, investigation_id: int) -> StandardizedEvidenceBundle:
        all_evidence = self.evidence_service.get_investigation_evidence(investigation_id)
        supporting = self.evidence_service.get_supporting_evidence(investigation_id)
        contradictory = self.evidence_service.get_contradictory_evidence(investigation_id)
        neutral = [item for item in all_evidence if item.support_direction == EvidenceSupportDirection.NEUTRAL]
        return StandardizedEvidenceBundle(
            investigation_id=investigation_id,
            all_evidence=all_evidence,
            supporting_evidence=supporting,
            contradictory_evidence=contradictory,
            neutral_evidence=neutral,
        )

    @staticmethod
    def _coordinates(hotspot_detail: HotspotDetail) -> HotspotCoordinates | None:
        contexts = [hotspot_detail.hotspot.detection_context]
        contexts.extend(observation.detection_context for observation in reversed(hotspot_detail.observations))
        for context in contexts:
            found = _extract_coordinates(context)
            if found is not None:
                return found
        return None

    @staticmethod
    def _data_quality(
        hotspot_detail: HotspotDetail,
        investigation_detail: InvestigationDetail,
        evidence_bundle: StandardizedEvidenceBundle,
        weather,
        wind,
    ) -> DataQualityContract:
        evidence_scores = [item.data_quality_score for item in evidence_bundle.all_evidence]
        latest_observation = hotspot_detail.observations[-1] if hotspot_detail.observations else None
        notes = []
        if not evidence_scores:
            notes.append("No evidence items have been collected yet.")
        if investigation_detail.investigation.status != InvestigationStatus.COMPLETE:
            notes.append(f"Investigation status is {investigation_detail.investigation.status.value}.")
        return DataQualityContract(
            hotspot_confidence=hotspot_detail.hotspot.data_quality_confidence,
            latest_station_quality="valid" if latest_observation else None,
            evidence_quality_score=round(sum(evidence_scores) / len(evidence_scores), 3) if evidence_scores else None,
            weather_quality=weather.data_quality_status if weather else None,
            wind_quality=wind.data_quality_status if wind else None,
            notes=notes,
        )

    @staticmethod
    def _events(
        hotspot_events: list[HotspotEventRecord],
        investigation_events: list[InvestigationEventRecord],
        investigation_id: int,
    ) -> list[IntelligenceContractEvent]:
        events: list[IntelligenceContractEvent] = []
        for event in hotspot_events:
            if event.event_type in {item.value for item in IntelligenceEventType}:
                events.append(
                    IntelligenceContractEvent(
                        event_type=event.event_type,
                        published_at=event.published_at,
                        source_module="hotspot_lifecycle",
                        hotspot_id=event.hotspot_id,
                        investigation_id=investigation_id,
                        payload=event.payload,
                    )
                )
        for event in investigation_events:
            if event.event_type in {item.value for item in IntelligenceEventType}:
                events.append(
                    IntelligenceContractEvent(
                        event_type=event.event_type,
                        published_at=event.published_at,
                        source_module="investigations",
                        investigation_id=event.investigation_id,
                        payload=event.payload,
                    )
                )
        return sorted(events, key=lambda item: item.published_at)


def _extract_coordinates(context: dict | None) -> HotspotCoordinates | None:
    if not isinstance(context, dict):
        return None
    candidates = [
        context,
        context.get("hotspot") if isinstance(context.get("hotspot"), dict) else None,
        context.get("candidate") if isinstance(context.get("candidate"), dict) else None,
        context.get("location") if isinstance(context.get("location"), dict) else None,
        context.get("coordinates") if isinstance(context.get("coordinates"), dict) else None,
    ]
    for candidate in candidates:
        if not isinstance(candidate, dict):
            continue
        latitude = candidate.get("latitude", candidate.get("lat"))
        longitude = candidate.get("longitude", candidate.get("lng", candidate.get("lon")))
        if latitude is not None and longitude is not None:
            return HotspotCoordinates(latitude=float(latitude), longitude=float(longitude))
    return None
