from sqlalchemy.orm import Session

from app.database import get_session_local
from app.environmental_data.repositories import EnvironmentalDataRepository
from app.environmental_data.seed_loader import build_seed_records, load_seed_fixture


def seed(db: Session) -> None:
    records = build_seed_records(load_seed_fixture())
    repository = EnvironmentalDataRepository(db)

    sources_by_code = {
        source.code: repository.upsert_source(source)
        for source in records.sources
    }

    for reading in records.air_quality_readings:
        repository.insert_air_quality_reading_if_missing(reading, sources_by_code[reading.source_code].id)

    for observation in records.weather_observations:
        repository.insert_weather_observation_if_missing(observation, sources_by_code[observation.source_code].id)

    for scenario in records.controlled_scenarios:
        repository.upsert_controlled_scenario(scenario, sources_by_code[scenario.source_code].id)

    db.commit()


def main() -> None:
    with get_session_local()() as db:
        seed(db)


if __name__ == "__main__":
    main()
