from app.environmental_data.seed_loader import build_seed_records, load_seed_fixture


def test_seed_fixture_separates_real_and_controlled_data() -> None:
    fixture = load_seed_fixture()

    source_provenance = {source["code"]: source["provenance"] for source in fixture["sources"]}

    assert source_provenance["opencity_cpcb_jigani_2024_25"] == "real_public"
    assert source_provenance["open_meteo_archive_blr_2025_01_15"] == "real_public"
    assert source_provenance["aerointel_controlled_scenarios_v1"] == "controlled_demo"
    assert len(fixture["controlled_scenarios"]) == 3


def test_build_seed_records_normalizes_pollutant_readings() -> None:
    fixture = load_seed_fixture()
    records = build_seed_records(fixture)

    jigani_pm25 = [
        reading
        for reading in records.air_quality_readings
        if reading.station_code == "site_5729" and reading.pollutant == "PM2.5"
    ]

    assert len(jigani_pm25) == 8
    assert jigani_pm25[0].value == 50.83
    assert records.weather_observations[0].wind_speed_kmh == 13.6
    assert records.controlled_scenarios[0].provenance == "controlled_demo"
