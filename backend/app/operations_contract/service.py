from datetime import UTC, datetime, timedelta

from app.aqi.classifier import classify_aqi
from app.aqi.schemas import AQIClassification
from app.environmental_data.time_series import EnvironmentalTimeSeriesService
from app.environmental_data.time_series_schemas import PollutantReading, TimeWindow
from app.geo_master.schemas import WardRead
from app.geo_master.services import GeoMasterService
from app.hotspot_lifecycle.schemas import HotspotDetail, HotspotRecord
from app.hotspot_lifecycle.service import HotspotLifecycleService
from app.sensor_health.schemas import SensorHealthSnapshot
from app.sensor_health.service import SensorHealthService

from .schemas import (
    DataQualityRollup,
    HotspotRecurrenceRecord,
    HotspotStatusContract,
    InterventionVerificationWindow,
    InterventionWindowSegment,
    InterventionWindowType,
    OperationsConsumer,
    OperationsTimeWindowReadings,
    WardOperationsState,
)

DEFAULT_STATE_LOOKBACK_HOURS = 24
DEFAULT_HISTORY_CONTEXT_HOURS = 2
DEFAULT_BASELINE_HOURS = 24
DEFAULT_EVALUATION_HOURS = 24


class OperationsContractService:
    def __init__(
        self,
        environmental_service: EnvironmentalTimeSeriesService,
        hotspot_service: HotspotLifecycleService,
        sensor_health_service: SensorHealthService,
        geo_service: GeoMasterService,
    ) -> None:
        self.environmental_service = environmental_service
        self.hotspot_service = hotspot_service
        self.sensor_health_service = sensor_health_service
        self.geo_service = geo_service

    def get_ward_state(
        self,
        ward_code: str,
        as_of: datetime | None = None,
        lookback_hours: int = DEFAULT_STATE_LOOKBACK_HOURS,
    ) -> WardOperationsState:
        generated_at = _utc_now()
        as_of = _ensure_utc(as_of or generated_at)
        start_at = as_of - timedelta(hours=lookback_hours)
        readings = self.environmental_service.get_readings_for_time_window(
            ward_code=ward_code,
            start_at=start_at,
            end_at=as_of,
        )
        ward = self.geo_service.get_ward_by_code(ward_code)
        sensors = self._ward_sensor_health(ward_code)
        hotspots = self._ward_hotspot_details(ward_code)
        latest_aqi = _latest_pollutant_value(readings, "AQI")

        return WardOperationsState(
            generated_at=generated_at,
            supported_consumers=list(OperationsConsumer),
            ward=ward,
            ward_code=ward_code,
            current_ward_aqi=latest_aqi,
            aqi_band=_classify_optional_aqi(latest_aqi),
            pollutant_readings=readings,
            hotspot_statuses=[self._hotspot_status(detail) for detail in hotspots],
            hotspot_recurrence_history=self._recurrence_history(hotspots),
            sensor_quality=sensors,
            data_quality=_quality_rollup(readings, sensors, ward),
        )

    def get_readings_for_time_window(
        self,
        ward_code: str,
        start_at: datetime,
        end_at: datetime,
        pollutant: str | None = None,
        station_code: str | None = None,
        selected_at: datetime | None = None,
    ) -> OperationsTimeWindowReadings:
        window = TimeWindow(start_at=_ensure_utc(start_at), end_at=_ensure_utc(end_at))
        readings = self.environmental_service.get_readings_for_time_window(
            station_code=station_code,
            ward_code=ward_code,
            pollutant=pollutant,
            start_at=window.start_at,
            end_at=window.end_at,
        )
        sensors = self._ward_sensor_health(ward_code)
        return OperationsTimeWindowReadings(
            generated_at=_utc_now(),
            ward_code=ward_code,
            window=window,
            selected_at=_ensure_utc(selected_at) if selected_at else None,
            pollutant=pollutant,
            station_code=station_code,
            readings=readings,
            data_quality=_quality_rollup(readings, sensors, None),
        )

    def get_readings_around_timestamp(
        self,
        ward_code: str,
        selected_at: datetime,
        context_hours: int = DEFAULT_HISTORY_CONTEXT_HOURS,
        pollutant: str | None = None,
        station_code: str | None = None,
    ) -> OperationsTimeWindowReadings:
        selected_at = _ensure_utc(selected_at)
        return self.get_readings_for_time_window(
            ward_code=ward_code,
            start_at=selected_at - timedelta(hours=context_hours),
            end_at=selected_at + timedelta(hours=context_hours),
            pollutant=pollutant,
            station_code=station_code,
            selected_at=selected_at,
        )

    def get_intervention_verification_window(
        self,
        ward_code: str,
        intervention_at: datetime,
        baseline_hours: int = DEFAULT_BASELINE_HOURS,
        evaluation_hours: int = DEFAULT_EVALUATION_HOURS,
        pollutant: str | None = None,
        station_code: str | None = None,
        intervention_id: str | None = None,
        forecast_location_code: str | None = None,
    ) -> InterventionVerificationWindow:
        generated_at = _utc_now()
        intervention_at = _ensure_utc(intervention_at)
        baseline_window = TimeWindow(
            start_at=intervention_at - timedelta(hours=baseline_hours),
            end_at=intervention_at,
        )
        evaluation_window = TimeWindow(
            start_at=intervention_at,
            end_at=intervention_at + timedelta(hours=evaluation_hours),
        )
        sensors = self._ward_sensor_health(ward_code)
        baseline_readings = self.environmental_service.get_readings_for_time_window(
            station_code=station_code,
            ward_code=ward_code,
            pollutant=pollutant,
            start_at=baseline_window.start_at,
            end_at=baseline_window.end_at,
        )
        actual_readings = self.environmental_service.get_readings_for_time_window(
            station_code=station_code,
            ward_code=ward_code,
            pollutant=pollutant,
            start_at=evaluation_window.start_at,
            end_at=evaluation_window.end_at,
        )
        forecast_location_code = forecast_location_code or ward_code
        weather_forecast = self.environmental_service.get_weather_forecast(
            forecast_location_code,
            evaluation_window.start_at,
            evaluation_window.end_at,
        )

        return InterventionVerificationWindow(
            generated_at=generated_at,
            ward_code=ward_code,
            intervention_id=intervention_id,
            intervention_at=intervention_at,
            pollutant=pollutant,
            station_code=station_code,
            pre_intervention_baseline=InterventionWindowSegment(
                window_type=InterventionWindowType.PRE_INTERVENTION_BASELINE,
                window=baseline_window,
                readings=baseline_readings,
                data_quality=_quality_rollup(baseline_readings, sensors, None),
            ),
            predicted_evaluation_window=InterventionWindowSegment(
                window_type=InterventionWindowType.PREDICTED_EVALUATION_WINDOW,
                window=evaluation_window,
                weather_forecast=weather_forecast,
                data_quality=_quality_rollup([], sensors, None),
                notes=["This contract exposes the evaluation window and weather forecast only; it does not predict pollution outcomes."],
            ),
            actual_post_intervention=InterventionWindowSegment(
                window_type=InterventionWindowType.ACTUAL_POST_INTERVENTION,
                window=evaluation_window,
                readings=actual_readings,
                data_quality=_quality_rollup(actual_readings, sensors, None),
            ),
            current_weather=self.environmental_service.get_current_weather(),
            current_wind=self.environmental_service.get_current_wind(),
        )

    def _ward_sensor_health(self, ward_code: str) -> list[SensorHealthSnapshot]:
        return [snapshot for snapshot in self.sensor_health_service.get_all_station_health() if snapshot.ward_code == ward_code]

    def _ward_hotspot_details(self, ward_code: str) -> list[HotspotDetail]:
        details: list[HotspotDetail] = []
        for hotspot in self.hotspot_service.list_hotspots():
            if hotspot.ward_code != ward_code or hotspot.id is None:
                continue
            details.append(self.hotspot_service.get_hotspot_detail(hotspot.id))
        return details

    @staticmethod
    def _hotspot_status(detail: HotspotDetail) -> HotspotStatusContract:
        return HotspotStatusContract(
            hotspot_id=_required_id(detail.hotspot),
            hotspot_uid=detail.hotspot.hotspot_uid,
            status=detail.hotspot.status,
            severity=detail.hotspot.severity,
            alert_level=detail.hotspot.alert_level,
            current_aqi=detail.hotspot.current_aqi,
            first_detected_at=detail.hotspot.first_detected_at,
            last_detected_at=detail.hotspot.last_detected_at,
            recurrence_count=len(detail.observations),
            data_quality_confidence=detail.hotspot.data_quality_confidence,
        )

    @staticmethod
    def _recurrence_history(details: list[HotspotDetail]) -> list[HotspotRecurrenceRecord]:
        records: list[HotspotRecurrenceRecord] = []
        for detail in details:
            for observation in detail.observations:
                records.append(
                    HotspotRecurrenceRecord(
                        hotspot_id=observation.hotspot_id,
                        observed_at=observation.observed_at,
                        aqi=observation.aqi,
                        severity=observation.severity,
                        alert_level=observation.alert_level,
                        pollutant_snapshot=observation.pollutant_snapshot,
                        data_quality_confidence=observation.data_quality_confidence,
                    )
                )
        return sorted(records, key=lambda item: item.observed_at)


def _quality_rollup(
    readings: list[PollutantReading],
    sensors: list[SensorHealthSnapshot],
    ward: WardRead | None,
) -> DataQualityRollup:
    status_counts = {"valid": 0, "suspect": 0, "incomplete": 0}
    for reading in readings:
        status_counts[reading.data_quality_status] += 1
    reliable = sum(1 for sensor in sensors if sensor.is_reliable)
    unreliable = len(sensors) - reliable
    notes = []
    if ward is None:
        notes.append("Ward details are unavailable from geo master.")
    if not readings:
        notes.append("No environmental readings matched the requested window.")
    if unreliable:
        notes.append(f"{unreliable} station(s) are delayed, degraded, or offline.")
    return DataQualityRollup(
        reading_count=len(readings),
        valid_count=status_counts["valid"],
        suspect_count=status_counts["suspect"],
        incomplete_count=status_counts["incomplete"],
        reliable_sensor_count=reliable,
        unreliable_sensor_count=unreliable,
        average_sensor_quality_score=round(sum(sensor.data_quality_score for sensor in sensors) / len(sensors), 3) if sensors else None,
        notes=notes,
    )


def _latest_pollutant_value(readings: list[PollutantReading], pollutant: str) -> float | None:
    matching = [reading for reading in readings if reading.pollutant.upper() == pollutant.upper()]
    if not matching:
        return None
    return max(matching, key=lambda reading: reading.observed_at).value


def _classify_optional_aqi(aqi: float | None) -> AQIClassification | None:
    if aqi is None:
        return None
    try:
        return classify_aqi(aqi)
    except ValueError:
        return None


def _required_id(hotspot: HotspotRecord) -> int:
    if hotspot.id is None:
        raise ValueError("Hotspot id is required for operations contract.")
    return hotspot.id


def _utc_now() -> datetime:
    return datetime.now(UTC)


def _ensure_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)
