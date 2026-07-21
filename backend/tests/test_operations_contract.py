from datetime import UTC, datetime, timedelta

from app.environmental_data.time_series_schemas import PollutantReading, WeatherForecastReading, WeatherReading, WindReading
from app.geo_master.schemas import WardRead
from app.hotspot_lifecycle.schemas import HotspotDetail, HotspotObservationRecord, HotspotRecord, HotspotStatus
from app.hotspots.schemas import AlertLevel, HotspotSeverity, HotspotTrigger
from app.operations_contract.schemas import InterventionWindowType, OperationsConsumer
from app.operations_contract.service import OperationsContractService
from app.sensor_health.schemas import SensorHealthSnapshot, SensorHealthStatus

NOW = datetime(2025, 1, 15, 12, tzinfo=UTC)
WARD_CODE = "BLR-W-014"


class FakeEnvironmentalService:
    def __init__(self) -> None:
        self.window_calls = []

    def get_readings_for_time_window(self, station_code=None, ward_code=None, pollutant=None, start_at=None, end_at=None):
        self.window_calls.append(
            {
                "station_code": station_code,
                "ward_code": ward_code,
                "pollutant": pollutant,
                "start_at": start_at,
                "end_at": end_at,
            }
        )
        readings = [
            pollutant_reading("AQI", 226, NOW - timedelta(minutes=30)),
            pollutant_reading("PM2.5", 104, NOW - timedelta(minutes=30)),
            pollutant_reading("NO2", 62, NOW - timedelta(minutes=45), quality="suspect"),
        ]
        if pollutant:
            readings = [item for item in readings if item.pollutant == pollutant]
        return readings

    def get_weather_forecast(self, location_code, start_at, end_at):
        return [
            WeatherForecastReading(
                location_code=location_code,
                forecast_for=start_at + timedelta(hours=1),
                generated_at=NOW,
                temperature_c=29,
                wind_speed_kmh=12,
                wind_direction_degrees=270,
                provider="seeded_demo",
            )
        ]

    def get_current_weather(self):
        return WeatherReading(location_code="BLR-CENTRE", city="Bengaluru", observed_at=NOW, temperature_c=28)

    def get_current_wind(self):
        return WindReading(location_code="BLR-CENTRE", city="Bengaluru", observed_at=NOW, wind_speed_kmh=14)


class FakeHotspotService:
    def list_hotspots(self, status=None):
        return [hotspot_record(101), hotspot_record(102, ward_code="BLR-W-099")]

    def get_hotspot_detail(self, hotspot_id):
        return HotspotDetail(
            hotspot=hotspot_record(hotspot_id),
            observations=[
                HotspotObservationRecord(
                    hotspot_id=hotspot_id,
                    station_code="BLR-SB-AQ",
                    station_name="Silk Board Junction",
                    ward_code=WARD_CODE,
                    observed_at=NOW - timedelta(hours=2),
                    aqi=210,
                    pollutant_snapshot={"PM2.5": 98, "PM10": 166},
                    severity=HotspotSeverity.HIGH,
                    alert_level=AlertLevel.WARNING,
                    trigger_reasons=[HotspotTrigger.AQI_THRESHOLD],
                    anomaly_score=2.1,
                    data_quality_confidence=0.88,
                ),
                HotspotObservationRecord(
                    hotspot_id=hotspot_id,
                    station_code="BLR-SB-AQ",
                    station_name="Silk Board Junction",
                    ward_code=WARD_CODE,
                    observed_at=NOW - timedelta(minutes=30),
                    aqi=226,
                    pollutant_snapshot={"PM2.5": 104, "PM10": 178},
                    severity=HotspotSeverity.HIGH,
                    alert_level=AlertLevel.WARNING,
                    trigger_reasons=[HotspotTrigger.AQI_THRESHOLD],
                    anomaly_score=2.4,
                    data_quality_confidence=0.9,
                ),
            ],
            status_history=[],
            events=[],
        )


class FakeSensorHealthService:
    def get_all_station_health(self):
        return [
            SensorHealthSnapshot(
                station_code="BLR-SB-AQ",
                station_name="Silk Board Junction",
                ward_code=WARD_CODE,
                status=SensorHealthStatus.ONLINE,
                data_quality_score=0.92,
                last_reading_at=NOW,
                evaluated_at=NOW,
                is_reliable=True,
            ),
            SensorHealthSnapshot(
                station_code="BLR-HSR-AQ",
                station_name="HSR Layout",
                ward_code=WARD_CODE,
                status=SensorHealthStatus.DEGRADED,
                data_quality_score=0.61,
                last_reading_at=NOW - timedelta(hours=2),
                evaluated_at=NOW,
                reasons=["missing_pollutants"],
                is_reliable=False,
            ),
        ]


class FakeGeoService:
    def get_ward_by_code(self, ward_code):
        return WardRead(
            id=14,
            city_id=1,
            code=ward_code,
            name="Silk Board",
            population=78000,
            boundary_geojson={"type": "Polygon", "coordinates": []},
        )


def pollutant_reading(name, value, observed_at, quality="valid"):
    return PollutantReading(
        station_code="BLR-SB-AQ",
        station_name="Silk Board Junction",
        ward_code=WARD_CODE,
        observed_at=observed_at,
        pollutant=name,
        value=value,
        unit="index" if name == "AQI" else "ug/m3",
        data_quality_status=quality,
    )


def hotspot_record(hotspot_id, ward_code=WARD_CODE):
    return HotspotRecord(
        id=hotspot_id,
        hotspot_uid=f"hs-{hotspot_id}",
        ward_code=ward_code,
        station_code="BLR-SB-AQ",
        station_name="Silk Board Junction",
        status=HotspotStatus.ACTIVE,
        severity=HotspotSeverity.HIGH,
        alert_level=AlertLevel.WARNING,
        current_aqi=226,
        anomaly_score=2.4,
        data_quality_confidence=0.9,
        trigger_reasons=[HotspotTrigger.AQI_THRESHOLD],
        detection_context={},
        first_detected_at=NOW - timedelta(hours=2),
        last_detected_at=NOW - timedelta(minutes=30),
    )


def contract_service():
    env = FakeEnvironmentalService()
    service = OperationsContractService(
        environmental_service=env,
        hotspot_service=FakeHotspotService(),
        sensor_health_service=FakeSensorHealthService(),
        geo_service=FakeGeoService(),
    )
    return service, env


def test_ward_state_exposes_operations_advisory_contract() -> None:
    service, _ = contract_service()

    state = service.get_ward_state(WARD_CODE, as_of=NOW)

    assert state.ward.name == "Silk Board"
    assert state.current_ward_aqi == 226
    assert state.aqi_band.band == "POOR"
    assert OperationsConsumer.CITIZEN_ADVISORY in state.supported_consumers
    assert [item.pollutant for item in state.pollutant_readings] == ["AQI", "PM2.5", "NO2"]
    assert len(state.hotspot_statuses) == 1
    assert state.hotspot_statuses[0].recurrence_count == 2
    assert len(state.hotspot_recurrence_history) == 2
    assert state.data_quality.reading_count == 3
    assert state.data_quality.valid_count == 2
    assert state.data_quality.suspect_count == 1
    assert state.data_quality.reliable_sensor_count == 1
    assert state.data_quality.unreliable_sensor_count == 1


def test_readings_around_timestamp_uses_generic_time_window_contract() -> None:
    service, env = contract_service()
    selected_at = NOW - timedelta(hours=1)

    response = service.get_readings_around_timestamp(
        WARD_CODE,
        selected_at=selected_at,
        context_hours=3,
        pollutant="PM2.5",
        station_code="BLR-SB-AQ",
    )

    assert response.selected_at == selected_at
    assert response.window.start_at == selected_at - timedelta(hours=3)
    assert response.window.end_at == selected_at + timedelta(hours=3)
    assert response.pollutant == "PM2.5"
    assert [item.pollutant for item in response.readings] == ["PM2.5"]
    assert env.window_calls[-1]["station_code"] == "BLR-SB-AQ"


def test_intervention_verification_contract_returns_pre_predicted_and_post_windows() -> None:
    service, _ = contract_service()

    response = service.get_intervention_verification_window(
        WARD_CODE,
        intervention_at=NOW,
        baseline_hours=6,
        evaluation_hours=8,
        pollutant="PM2.5",
        intervention_id="dust-control-42",
        forecast_location_code="BLR-CENTRE",
    )

    assert response.intervention_id == "dust-control-42"
    assert response.pre_intervention_baseline.window_type == InterventionWindowType.PRE_INTERVENTION_BASELINE
    assert response.pre_intervention_baseline.window.start_at == NOW - timedelta(hours=6)
    assert response.predicted_evaluation_window.window_type == InterventionWindowType.PREDICTED_EVALUATION_WINDOW
    assert response.predicted_evaluation_window.window.end_at == NOW + timedelta(hours=8)
    assert response.predicted_evaluation_window.weather_forecast[0].location_code == "BLR-CENTRE"
    assert response.actual_post_intervention.window_type == InterventionWindowType.ACTUAL_POST_INTERVENTION
    assert [item.pollutant for item in response.actual_post_intervention.readings] == ["PM2.5"]
    assert response.current_weather.city == "Bengaluru"
    assert response.current_wind.wind_speed_kmh == 14

