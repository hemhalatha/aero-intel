from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.environmental_data.models import AirQualityReading
from app.geo_master.models import MonitoringStation
from app.sensor_health.models import SensorHealthCurrent
from app.sensor_health.schemas import SensorHealthStatus

from .schemas import BoundingBox, StationAQISample


class AQIHeatmapRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_latest_station_aqi_samples(self, bbox: BoundingBox | None = None) -> list[StationAQISample]:
        latest = (
            select(
                AirQualityReading.station_code,
                func.max(AirQualityReading.observed_at).label("observed_at"),
            )
            .where(AirQualityReading.pollutant == "AQI")
            .group_by(AirQualityReading.station_code)
            .subquery()
        )
        statement = (
            select(AirQualityReading, MonitoringStation, SensorHealthCurrent)
            .join(
                latest,
                (AirQualityReading.station_code == latest.c.station_code)
                & (AirQualityReading.observed_at == latest.c.observed_at),
            )
            .join(MonitoringStation, MonitoringStation.code == AirQualityReading.station_code)
            .outerjoin(SensorHealthCurrent, SensorHealthCurrent.station_code == AirQualityReading.station_code)
            .where(AirQualityReading.pollutant == "AQI")
        )
        if bbox is not None:
            statement = statement.where(MonitoringStation.latitude >= bbox.min_latitude)
            statement = statement.where(MonitoringStation.latitude <= bbox.max_latitude)
            statement = statement.where(MonitoringStation.longitude >= bbox.min_longitude)
            statement = statement.where(MonitoringStation.longitude <= bbox.max_longitude)

        samples: list[StationAQISample] = []
        for reading, station, health in self.db.execute(statement):
            sensor_status = SensorHealthStatus(health.status) if health else SensorHealthStatus.ONLINE
            score = health.data_quality_score if health else 1.0
            is_reliable = health.is_reliable if health else reading.data_quality_status == "valid"
            samples.append(
                StationAQISample(
                    station_code=reading.station_code,
                    station_name=reading.station_name or station.name,
                    ward_code=reading.ward_code,
                    latitude=station.latitude,
                    longitude=station.longitude,
                    aqi=reading.value,
                    data_quality_score=score,
                    sensor_status=sensor_status,
                    is_reliable=is_reliable,
                )
            )
        return samples
