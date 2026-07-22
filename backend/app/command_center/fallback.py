from datetime import UTC, datetime, timedelta
from app.environmental_data.time_series_schemas import PollutantReading, StationLatestState, WeatherReading, WindReading
from app.heatmap.schemas import WardAQISummary
from app.sensor_health.schemas import SensorHealthSnapshot, SensorHealthStatus
from .schemas import HotspotSummary

NOW = datetime.now(UTC)


class FallbackHeatmapService:
    def get_ward_aqi_summaries(self, bbox=None):
        return [
            WardAQISummary(
                ward_code="BLR-W-001",
                average_aqi=110,
                station_count=2,
                band="MODERATELY_POLLUTED",
                severity_rank=3,
                display_label="Moderately Polluted",
                health_severity_category="unhealthy_for_sensitive_groups",
            ),
            WardAQISummary(
                ward_code="BLR-W-002",
                average_aqi=240,
                station_count=1,
                band="POOR",
                severity_rank=4,
                display_label="Poor",
                health_severity_category="unhealthy",
            ),
            WardAQISummary(
                ward_code="BLR-W-003",
                average_aqi=315,
                station_count=1,
                band="VERY_POOR",
                severity_rank=5,
                display_label="Very Poor",
                health_severity_category="very_unhealthy",
            ),
        ]

    def get_current_heatmap(self, request=None):
        return {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "geometry": {"type": "Point", "coordinates": [77.5946, 12.9716]},
                    "properties": {"aqi": 110, "station_code": "BLR-CBD-AQ"},
                },
                {
                    "type": "Feature",
                    "geometry": {"type": "Point", "coordinates": [77.5186, 13.0285]},
                    "properties": {"aqi": 315, "station_code": "BLR-PEE-AQ"},
                },
            ],
        }


class FallbackHotspotLifecycleService:
    def list_hotspots(self, status_filter=None):
        from app.hotspot_lifecycle.schemas import HotspotRecord, HotspotStatus
        from app.hotspots.schemas import AlertLevel, HotspotSeverity, HotspotTrigger
        records = [
            HotspotRecord(
                id=1,
                hotspot_uid="HS-801",
                ward_code="W-17",
                station_code="ST-05",
                station_name="Okhla Phase II Corridor",
                status=HotspotStatus.ACTIVE,
                severity=HotspotSeverity.CRITICAL,
                alert_level=AlertLevel.EMERGENCY,
                current_aqi=390.0,
                anomaly_score=4.1,
                data_quality_confidence=0.95,
                trigger_reasons=[HotspotTrigger.AQI_THRESHOLD],
                first_detected_at=NOW - timedelta(hours=3),
                last_detected_at=NOW,
            ),
            HotspotRecord(
                id=2,
                hotspot_uid="HS-805",
                ward_code="LKO-W-04",
                station_code="LKO-TAL-AQ",
                station_name="Talkatora Industrial",
                status=HotspotStatus.ACTIVE,
                severity=HotspotSeverity.CRITICAL,
                alert_level=AlertLevel.EMERGENCY,
                current_aqi=365.0,
                anomaly_score=3.8,
                data_quality_confidence=0.91,
                trigger_reasons=[HotspotTrigger.AQI_THRESHOLD],
                first_detected_at=NOW - timedelta(hours=4),
                last_detected_at=NOW,
            ),
            HotspotRecord(
                id=3,
                hotspot_uid="HS-802",
                ward_code="W-04",
                station_code="ST-01",
                station_name="Anand Vihar Transport Hub",
                status=HotspotStatus.ACTIVE,
                severity=HotspotSeverity.CRITICAL,
                alert_level=AlertLevel.EMERGENCY,
                current_aqi=342.0,
                anomaly_score=3.6,
                data_quality_confidence=0.94,
                trigger_reasons=[HotspotTrigger.AQI_THRESHOLD],
                first_detected_at=NOW - timedelta(hours=5),
                last_detected_at=NOW,
            ),
            HotspotRecord(
                id=4,
                hotspot_uid="HS-BLR-001",
                ward_code="BLR-W-003",
                station_code="BLR-PEE-AQ",
                station_name="Peenya Industrial Station",
                status=HotspotStatus.ACTIVE,
                severity=HotspotSeverity.CRITICAL,
                alert_level=AlertLevel.EMERGENCY,
                current_aqi=315.0,
                anomaly_score=3.4,
                data_quality_confidence=0.92,
                trigger_reasons=[HotspotTrigger.AQI_THRESHOLD],
                first_detected_at=NOW - timedelta(hours=2),
                last_detected_at=NOW,
            ),
            HotspotRecord(
                id=5,
                hotspot_uid="HS-807",
                ward_code="BOM-W-09",
                station_code="BOM-NAV-AQ",
                station_name="Navi Mumbai Rabale",
                status=HotspotStatus.ACTIVE,
                severity=HotspotSeverity.CRITICAL,
                alert_level=AlertLevel.EMERGENCY,
                current_aqi=310.0,
                anomaly_score=3.3,
                data_quality_confidence=0.90,
                trigger_reasons=[HotspotTrigger.AQI_THRESHOLD],
                first_detected_at=NOW - timedelta(hours=2),
                last_detected_at=NOW,
            ),
            HotspotRecord(
                id=6,
                hotspot_uid="HS-808",
                ward_code="CCU-W-02",
                station_code="CCU-BAL-AQ",
                station_name="Ballygunge Station",
                status=HotspotStatus.ACTIVE,
                severity=HotspotSeverity.CRITICAL,
                alert_level=AlertLevel.EMERGENCY,
                current_aqi=305.0,
                anomaly_score=3.2,
                data_quality_confidence=0.89,
                trigger_reasons=[HotspotTrigger.AQI_THRESHOLD],
                first_detected_at=NOW - timedelta(hours=1),
                last_detected_at=NOW,
            ),
            HotspotRecord(
                id=7,
                hotspot_uid="HS-MAA-001",
                ward_code="MAA-W-01",
                station_code="MAA-MAN-AQ",
                station_name="Manali Industrial Area",
                status=HotspotStatus.ACTIVE,
                severity=HotspotSeverity.HIGH,
                alert_level=AlertLevel.WARNING,
                current_aqi=280.0,
                anomaly_score=2.9,
                data_quality_confidence=0.88,
                trigger_reasons=[HotspotTrigger.AQI_THRESHOLD],
                first_detected_at=NOW - timedelta(hours=2),
                last_detected_at=NOW,
            ),
        ]

        if status_filter is not None:
            return [r for r in records if str(r.status) == str(status_filter)]
        return records




    def get_hotspot_detail(self, hotspot_id: int):
        from app.hotspot_lifecycle.schemas import HotspotDetail
        records = self.list_hotspots()
        return HotspotDetail(
            hotspot=records[0],
            observations=[],
            status_history=[],
            events=[],
        )



from app.sensor_health.service import SensorHealthService


class FallbackSensorHealthService(SensorHealthService):
    def __init__(self):
        super().__init__(repository=None)

    def get_current_statuses(self):
        return self.get_all_station_health()

    def get_current_status(self, station_code: str):
        return self.get_station_health(station_code)

    def get_health_history(self, station_code: str):
        item = self.get_station_health(station_code)
        return [item] if item else []

    def get_station_health_history(self, station_code: str):
        return self.get_health_history(station_code)


    def get_all_station_health(self):
        return [
            SensorHealthSnapshot(
                station_code="BLR-CBD-AQ",
                station_name="CBD Station",
                ward_code="BLR-W-001",
                status=SensorHealthStatus.ONLINE,
                data_quality_score=0.95,
                last_reading_at=NOW,
                evaluated_at=NOW,
                is_reliable=True,
            ),
            SensorHealthSnapshot(
                station_code="BLR-IND-AQ",
                station_name="Indiranagar Station",
                ward_code="BLR-W-002",
                status=SensorHealthStatus.DEGRADED,
                data_quality_score=0.55,
                last_reading_at=NOW,
                evaluated_at=NOW,
                reasons=["missing_pollutants"],
                is_reliable=False,
            ),
            SensorHealthSnapshot(
                station_code="BLR-PEE-AQ",
                station_name="Peenya Industrial Station",
                ward_code="BLR-W-003",
                status=SensorHealthStatus.ONLINE,
                data_quality_score=0.92,
                last_reading_at=NOW,
                evaluated_at=NOW,
                is_reliable=True,
            ),
        ]

    def get_station_health(self, station_code: str):
        target = station_code.upper().strip()
        for item in self.get_all_station_health():
            if item.station_code.upper() == target:
                return item
        return None

    def get_station_health_history(self, station_code: str):
        item = self.get_station_health(station_code)
        return [item] if item else []

    def is_reading_reliable(self, status: SensorHealthStatus, data_quality_score: float) -> bool:
        return status == SensorHealthStatus.ONLINE and data_quality_score >= 0.7




class FallbackTimeSeriesService:
    def get_latest_station_readings(self):
        r1 = PollutantReading(
            station_code="BLR-CBD-AQ",
            station_name="CBD Station",
            ward_code="BLR-W-001",
            observed_at=NOW,
            pollutant="AQI",
            value=110,
            unit="index",
            data_quality_status="valid",
        )
        r2 = PollutantReading(
            station_code="BLR-PEE-AQ",
            station_name="Peenya Industrial Station",
            ward_code="BLR-W-003",
            observed_at=NOW,
            pollutant="AQI",
            value=315,
            unit="index",
            data_quality_status="valid",
        )
        r3 = PollutantReading(
            station_code="BLR-IND-AQ",
            station_name="Indiranagar Station",
            ward_code="BLR-W-002",
            observed_at=NOW,
            pollutant="AQI",
            value=240,
            unit="index",
            data_quality_status="valid",
        )

        return [
            StationLatestState(
                station_code="BLR-CBD-AQ",
                station_name="CBD Station",
                ward_code="BLR-W-001",
                observed_at=NOW,
                readings=[r1],
                data_quality_status="valid",
            ),
            StationLatestState(
                station_code="BLR-IND-AQ",
                station_name="Indiranagar Station",
                ward_code="BLR-W-002",
                observed_at=NOW,
                readings=[r3],
                data_quality_status="valid",
            ),
            StationLatestState(
                station_code="BLR-PEE-AQ",
                station_name="Peenya Industrial Station",
                ward_code="BLR-W-003",
                observed_at=NOW,
                readings=[r2],
                data_quality_status="valid",
            ),
        ]


    def get_current_weather(self, location_code=None):
        return WeatherReading(
            location_code="BLR-CENTRE",
            city="Bengaluru",
            observed_at=NOW,
            temperature_c=24.2,
            relative_humidity_pct=54,
            data_quality_status="valid",
        )

    def get_current_wind(self, location_code=None):
        return WindReading(
            location_code="BLR-CENTRE",
            city="Bengaluru",
            observed_at=NOW,
            wind_speed_kmh=13.7,
            wind_direction_degrees=92,
            data_quality_status="valid",
        )

    def get_readings_for_time_window(self, station_code=None, ward_code=None, pollutant=None, start_at=None, end_at=None):
        return [
            PollutantReading(
                station_code="BLR-CBD-AQ",
                station_name="CBD Station",
                ward_code="BLR-W-001",
                observed_at=NOW - timedelta(hours=i),
                pollutant="AQI",
                value=100 + (i * 3),
                unit="index",
                data_quality_status="valid",
            )
            for i in range(24, 0, -1)
        ]


class FallbackHotspotSummaryProvider:
    def get_current_hotspot_summaries(self) -> list[HotspotSummary]:
        return [
            HotspotSummary(
                hotspot_id="HS-801",
                ward_code="W-17",
                severity="critical",
                aqi=390.0,
                detected_at=NOW - timedelta(hours=3),
                summary="Construction dust and freight emissions in Okhla Phase II.",
            ),
            HotspotSummary(
                hotspot_id="HS-805",
                ward_code="LKO-W-04",
                severity="critical",
                aqi=365.0,
                detected_at=NOW - timedelta(hours=4),
                summary="Industrial stack emissions in Talkatora Lucknow.",
            ),
            HotspotSummary(
                hotspot_id="HS-802",
                ward_code="W-04",
                severity="critical",
                aqi=342.0,
                detected_at=NOW - timedelta(hours=5),
                summary="Heavy transport idling in Anand Vihar Delhi.",
            ),
            HotspotSummary(
                hotspot_id="HS-BLR-001",
                ward_code="BLR-W-003",
                severity="critical",
                aqi=315.0,
                detected_at=NOW - timedelta(hours=2),
                summary="Severe PM10 surge detected near Peenya Industrial zone due to construction dust.",
            ),
            HotspotSummary(
                hotspot_id="HS-807",
                ward_code="BOM-W-09",
                severity="critical",
                aqi=310.0,
                detected_at=NOW - timedelta(hours=2),
                summary="Fugitive dust and industrial transport in Navi Mumbai Rabale.",
            ),
            HotspotSummary(
                hotspot_id="HS-808",
                ward_code="CCU-W-02",
                severity="critical",
                aqi=305.0,
                detected_at=NOW - timedelta(hours=1),
                summary="Biomass burning and vehicle exhaust in Ballygunge Kolkata.",
            ),
            HotspotSummary(
                hotspot_id="HS-MAA-001",
                ward_code="MAA-W-01",
                severity="high",
                aqi=280.0,
                detected_at=NOW - timedelta(hours=2),
                summary="Petrochemical & thermal stack emissions surge in Manali Industrial Zone Chennai.",
            ),
        ]



