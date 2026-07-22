from collections import defaultdict
from datetime import UTC, datetime, timedelta
from typing import Protocol

from app.environmental_data.time_series_schemas import PollutantReading, StationLatestState
from app.sensor_health.schemas import SensorHealthStatus

from .schemas import CityPollutionTrendPoint, CommandCenterDashboard, HotspotSummary


class HotspotSummaryProvider(Protocol):
    def get_current_hotspot_summaries(self) -> list[HotspotSummary]:
        ...


class EmptyHotspotSummaryProvider:
    def get_current_hotspot_summaries(self) -> list[HotspotSummary]:
        return []


class CommandCenterAggregationService:
    def __init__(
        self,
        heatmap_service,
        sensor_health_service,
        time_series_service,
        hotspot_provider: HotspotSummaryProvider | None = None,
    ) -> None:
        self.heatmap_service = heatmap_service
        self.sensor_health_service = sensor_health_service
        self.time_series_service = time_series_service
        self.hotspot_provider = hotspot_provider or EmptyHotspotSummaryProvider()

    def get_initial_dashboard(self, now: datetime | None = None) -> CommandCenterDashboard:
        generated_at = now or datetime.now(UTC)
        ward_summaries = self.heatmap_service.get_ward_aqi_summaries()
        station_health = self.sensor_health_service.get_all_station_health()
        latest_station_readings = self.time_series_service.get_latest_station_readings()
        current_hotspots = self.hotspot_provider.get_current_hotspot_summaries()

        return CommandCenterDashboard(
            generated_at=generated_at,
            city_average_aqi=self._city_average_aqi(ward_summaries),
            worst_affected_ward=max(ward_summaries, key=lambda ward: ward.average_aqi) if ward_summaries else None,
            active_hotspot_count=len(current_hotspots),
            offline_or_degraded_station_count=sum(
                1
                for item in station_health
                if item.status in {SensorHealthStatus.OFFLINE, SensorHealthStatus.DEGRADED}
            ),
            latest_reliable_station_readings=self._reliable_station_readings(latest_station_readings, station_health),
            weather_summary=self.time_series_service.get_current_weather(),
            wind_information=self.time_series_service.get_current_wind(),
            current_hotspot_summaries=current_hotspots,
            city_pollution_trend=self._city_pollution_trend(generated_at),
        )

    @staticmethod
    def _city_average_aqi(ward_summaries) -> float | None:
        total_stations = sum(ward.station_count for ward in ward_summaries)
        if total_stations == 0:
            return None
        weighted_sum = sum(ward.average_aqi * ward.station_count for ward in ward_summaries)
        return round(weighted_sum / total_stations, 2)

    @staticmethod
    def _reliable_station_readings(
        station_readings: list[StationLatestState],
        station_health,
    ) -> list[StationLatestState]:
        reliable_codes = {
            item.station_code
            for item in station_health
            if item.status == SensorHealthStatus.ONLINE and item.is_reliable
        }
        return [
            item
            for item in station_readings
            if item.station_code in reliable_codes and item.data_quality_status == "valid"
        ]

    def _city_pollution_trend(self, now: datetime) -> list[CityPollutionTrendPoint]:
        readings = self.time_series_service.get_readings_for_time_window(
            pollutant="AQI",
            start_at=now - timedelta(hours=24),
            end_at=now,
        )
        grouped: dict[datetime, list[PollutantReading]] = defaultdict(list)
        for reading in readings:
            if reading.data_quality_status == "valid":
                grouped[reading.observed_at].append(reading)

        return [
            CityPollutionTrendPoint(
                observed_at=observed_at,
                average_aqi=round(sum(item.value for item in items) / len(items), 2),
            )
            for observed_at, items in sorted(grouped.items())
            if items
        ]


