from sqlalchemy import select
from sqlalchemy.orm import Session

from .models import (
    AirQualityReading,
    ControlledScenario,
    EnvironmentalDataSource,
    RejectedEnvironmentalRecordLog,
    WeatherObservation,
)
from .schemas import (
    AirQualityReadingSeed,
    ControlledScenarioSeed,
    EnvironmentalDataSourceSeed,
    NormalizedAirQualityReading,
    RejectedEnvironmentalRecord,
    WeatherObservationSeed,
)


class EnvironmentalDataRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def upsert_source(self, source: EnvironmentalDataSourceSeed) -> EnvironmentalDataSource:
        existing = self.db.scalar(select(EnvironmentalDataSource).where(EnvironmentalDataSource.code == source.code))
        values = source.model_dump()
        if existing is None:
            existing = EnvironmentalDataSource(**values)
            self.db.add(existing)
        else:
            for key, value in values.items():
                setattr(existing, key, value)
        self.db.flush()
        return existing

    def insert_air_quality_reading_if_missing(
        self,
        reading: AirQualityReadingSeed,
        source_id: int,
    ) -> None:
        exists = self.db.scalar(
            select(AirQualityReading.id).where(
                AirQualityReading.station_code == reading.station_code,
                AirQualityReading.observed_at == reading.observed_at,
                AirQualityReading.pollutant == reading.pollutant,
                AirQualityReading.source_id == source_id,
            )
        )
        if exists is None:
            self.db.add(AirQualityReading(source_id=source_id, **reading.model_dump(exclude={"source_code"})))

    def insert_normalized_air_quality_reading_if_missing(
        self,
        reading: NormalizedAirQualityReading,
        source_id: int,
    ) -> None:
        exists = self.db.scalar(
            select(AirQualityReading.id).where(
                AirQualityReading.station_code == reading.station_code,
                AirQualityReading.observed_at == reading.observed_at,
                AirQualityReading.pollutant == reading.pollutant,
                AirQualityReading.source_id == source_id,
            )
        )
        if exists is None:
            self.db.add(
                AirQualityReading(
                    source_id=source_id,
                    station_code=reading.station_code,
                    external_station_id=reading.external_station_id,
                    station_name=reading.station_name,
                    ward_code=reading.ward_code,
                    city=reading.city,
                    state=reading.state,
                    observed_at=reading.observed_at,
                    pollutant=reading.pollutant,
                    value=reading.value,
                    unit=reading.unit,
                    averaging_period=reading.averaging_period,
                    data_quality_status=reading.data_quality_status,
                    raw_payload=reading.raw_payload,
                )
            )

    def log_rejected_record(self, record: RejectedEnvironmentalRecord) -> None:
        self.db.add(RejectedEnvironmentalRecordLog(**record.model_dump()))

    def insert_weather_observation_if_missing(
        self,
        observation: WeatherObservationSeed,
        source_id: int,
    ) -> None:
        exists = self.db.scalar(
            select(WeatherObservation.id).where(
                WeatherObservation.location_code == observation.location_code,
                WeatherObservation.observed_at == observation.observed_at,
                WeatherObservation.source_id == source_id,
            )
        )
        if exists is None:
            self.db.add(WeatherObservation(source_id=source_id, **observation.model_dump(exclude={"source_code"})))

    def upsert_controlled_scenario(
        self,
        scenario: ControlledScenarioSeed,
        source_id: int,
    ) -> None:
        existing = self.db.scalar(
            select(ControlledScenario).where(ControlledScenario.scenario_key == scenario.scenario_key)
        )
        values = scenario.model_dump(exclude={"source_code"})
        if existing is None:
            self.db.add(ControlledScenario(source_id=source_id, **values))
        else:
            existing.source_id = source_id
            for key, value in values.items():
                setattr(existing, key, value)
