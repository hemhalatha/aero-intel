from datetime import UTC, datetime

from app.environmental_data.time_series_schemas import PollutantReading, WeatherReading, WindReading
from app.hotspot_lifecycle.schemas import HotspotDetail, HotspotEventRecord, HotspotObservationRecord, HotspotRecord, HotspotStatus
from app.hotspots.schemas import AlertLevel, HotspotSeverity, HotspotTrigger
from app.intelligence_contract.schemas import IntelligenceConsumer
from app.intelligence_contract.service import IntelligenceContractService
from app.investigations.evidence import EvidenceRecord, EvidenceSupportDirection
from app.investigations.schemas import InvestigationDetail, InvestigationRecord, InvestigationStatus

NOW = datetime(2025, 1, 15, 12, tzinfo=UTC)


class FakeHotspotService:
    def get_hotspot_detail(self, hotspot_id):
        return HotspotDetail(
            hotspot=HotspotRecord(
                id=hotspot_id,
                hotspot_uid="hs-test",
                ward_code="BLR-W-014",
                station_code="BLR-SB-AQ",
                station_name="Silk Board Junction",
                status=HotspotStatus.ACTIVE,
                severity=HotspotSeverity.HIGH,
                alert_level=AlertLevel.WARNING,
                current_aqi=238,
                anomaly_score=2.7,
                data_quality_confidence=0.91,
                trigger_reasons=[HotspotTrigger.AQI_THRESHOLD],
                detection_context={"coordinates": {"latitude": 12.917, "longitude": 77.623}},
                first_detected_at=NOW,
                last_detected_at=NOW,
            ),
            observations=[
                HotspotObservationRecord(
                    hotspot_id=hotspot_id,
                    station_code="BLR-SB-AQ",
                    station_name="Silk Board Junction",
                    ward_code="BLR-W-014",
                    observed_at=NOW,
                    aqi=238,
                    pollutant_snapshot={"PM2.5": 112, "PM10": 188, "NO2": 74},
                    severity=HotspotSeverity.HIGH,
                    alert_level=AlertLevel.WARNING,
                    trigger_reasons=[HotspotTrigger.AQI_THRESHOLD],
                    anomaly_score=2.7,
                    data_quality_confidence=0.91,
                    detection_context={},
                )
            ],
            status_history=[],
            events=[
                HotspotEventRecord(
                    hotspot_id=hotspot_id,
                    event_type="hotspot.created",
                    payload={"hotspot_uid": "hs-test"},
                    published_at=NOW,
                )
            ],
        )


class FakeInvestigationService:
    def get_investigation_detail(self, investigation_id):
        return InvestigationDetail(
            investigation=InvestigationRecord(
                id=investigation_id,
                investigation_uid="inv-test",
                hotspot_id=101,
                hotspot_uid="hs-test",
                ward_code="BLR-W-014",
                station_code="BLR-SB-AQ",
                status=InvestigationStatus.COMPLETE,
                environmental_context={},
                created_at=NOW,
            ),
            collector_runs=[],
            evidence_items=[],
            events=[
                {
                    "id": 1,
                    "investigation_id": investigation_id,
                    "event_type": "evidence.collected",
                    "payload": {"evidence_id": 1},
                    "published_at": NOW,
                },
                {
                    "id": 2,
                    "investigation_id": investigation_id,
                    "event_type": "investigation.completed",
                    "payload": {"status": "COMPLETE"},
                    "published_at": NOW,
                },
            ],
        )


class FakeInvestigationLookup:
    def find_by_hotspot_id(self, hotspot_id):
        return InvestigationRecord(
            id=17,
            investigation_uid="inv-test",
            hotspot_id=hotspot_id,
            status=InvestigationStatus.COMPLETE,
            environmental_context={},
        )


class FakeEvidenceService:
    def get_investigation_evidence(self, investigation_id):
        return [
            EvidenceRecord(
                evidence_id=1,
                investigation_id=investigation_id,
                source_type="traffic",
                evidence_type="traffic.density_anomaly",
                detected=True,
                confidence=0.82,
                support_direction=EvidenceSupportDirection.SUPPORTS,
                raw_details={"deviation_pct": 44},
                data_quality_score=0.9,
                collector_name="traffic_evidence_collector",
                checked_at=NOW,
                source="traffic",
                collected_at=NOW,
            ),
            EvidenceRecord(
                evidence_id=2,
                investigation_id=investigation_id,
                source_type="industrial",
                evidence_type="industrial.activity_signal",
                detected=False,
                confidence=0.3,
                support_direction=EvidenceSupportDirection.CONTRADICTS,
                raw_details={"upwind": False},
                data_quality_score=0.8,
                collector_name="industrial_evidence_collector",
                checked_at=NOW,
                source="industrial",
                collected_at=NOW,
            ),
        ]

    def get_supporting_evidence(self, investigation_id):
        return [item for item in self.get_investigation_evidence(investigation_id) if item.support_direction == EvidenceSupportDirection.SUPPORTS]

    def get_contradictory_evidence(self, investigation_id):
        return [item for item in self.get_investigation_evidence(investigation_id) if item.support_direction == EvidenceSupportDirection.CONTRADICTS]


class FakeEnvironmentalService:
    def get_ward_aqi_history(self, ward_code, start_at, end_at):
        return [pollutant("AQI", 154)]

    def get_ward_pollutant_history(self, ward_code, pollutant_name, start_at, end_at):
        return [pollutant(pollutant_name, 42)]

    def get_current_weather(self):
        return WeatherReading(location_code="BLR-CENTRE", city="Bengaluru", observed_at=NOW, temperature_c=28)

    def get_current_wind(self):
        return WindReading(location_code="BLR-CENTRE", city="Bengaluru", observed_at=NOW, wind_speed_kmh=16, wind_direction_degrees=315)


def pollutant(name, value):
    return PollutantReading(
        station_code="BLR-SB-AQ",
        station_name="Silk Board Junction",
        ward_code="BLR-W-014",
        observed_at=NOW,
        pollutant=name,
        value=value,
        unit="index" if name == "AQI" else "ug/m3",
        data_quality_status="valid",
    )


def test_intelligence_contract_exposes_stable_downstream_context() -> None:
    service = IntelligenceContractService(
        hotspot_service=FakeHotspotService(),
        investigation_service=FakeInvestigationService(),
        investigation_lookup=FakeInvestigationLookup(),
        evidence_service=FakeEvidenceService(),
        environmental_service=FakeEnvironmentalService(),
    )

    contract = service.get_contract_by_hotspot(101, pollutants=["PM2.5", "NO2"])

    assert contract.hotspot_id == 101
    assert contract.investigation_id == 17
    assert contract.hotspot_coordinates.latitude == 12.917
    assert contract.current_aqi == 238
    assert contract.pollutant_snapshot["PM2.5"] == 112
    assert [item.pollutant for item in contract.historical_ward_aqi] == ["AQI"]
    assert set(contract.historical_pollutant_series) == {"PM2.5", "NO2"}
    assert contract.weather.city == "Bengaluru"
    assert contract.wind.wind_speed_kmh == 16
    assert len(contract.evidence_bundle.supporting_evidence) == 1
    assert len(contract.evidence_bundle.contradictory_evidence) == 1
    assert contract.data_quality.evidence_quality_score == 0.85
    assert IntelligenceConsumer.SOURCE_ATTRIBUTION in contract.supported_consumers
    assert [event.event_type for event in contract.events] == [
        "hotspot.created",
        "evidence.collected",
        "investigation.completed",
    ]