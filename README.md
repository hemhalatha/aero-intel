# AI Urban Air Quality Command Center — Member 2

This repository contains the AI Decision Support modules for the Urban Air Quality Command Center. The completed features are **Source Attribution** and the **Explanation Generator**.

## Module 1: Source Attribution

The API accepts an evidence bundle from Member 1 and ranks construction dust, vehicular pollution, industrial emission, road dust, and biomass burning. Scores are weighted, normalized to 100%, and returned with the evidence that affected each source.

### Run the backend

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Open `http://127.0.0.1:8000/docs` for interactive API documentation.

### Run tests

```powershell
cd backend
pytest
```

### Run the attribution screen

```powershell
cd frontend
npm install
npm run dev
```

The frontend expects the backend at `http://127.0.0.1:8000`; override it with `VITE_API_BASE_URL` if needed.

### Integration contract for Member 1

`POST /api/v1/attributions` accepts the existing evidence-bundle fields (`traffic`, `construction`, `industry`, `satellite`, `wind_direction`, and `wind_speed`) plus optional `road_dust`, `biomass_burning`, `historical_patterns`, and `pm25` values. See `backend/data/mock_evidence.json` for a complete request.

### Handoff to Members 2 and 3

Consume the endpoint response's `primary_source`, `secondary_sources`, `confidence`, and `rankings`. Future Member 2 explanation, recommendation, and simulation modules will build on this response. Member 3 can use the eventual recommendation output for department tasks and citizen advisories.

## Explanation Generator

`POST /api/v1/explanations` accepts the same evidence bundle and returns a short headline, a plain-language summary, and the weighted evidence supporting the primary source. This endpoint lets the dashboard explain *why* the source was selected rather than presenting a score alone.

## Geo Master Foundation

Member 1 owns the independent `geo_master` backend module for city and spatial reference data. It defines SQLAlchemy models, Pydantic schemas, repositories, services, migration SQL, and seeded demo data for:

- cities
- wards with PostGIS polygon boundaries
- monitoring stations with latitude/longitude and point geometry
- road segments with line geometry
- land-use zones with polygon boundaries

### Spatial operations

Reusable functions live under `backend/app/geo_master`:

- `GeoMasterService.find_ward_containing_point(point)` uses PostGIS `ST_Contains`.
- `GeoMasterService.find_entities_within_radius(entity_type, point, radius_meters)` uses `ST_DWithin` and orders by distance.
- `GeoMasterService.calculate_distance_meters(origin, destination)` uses the repository-backed `ST_DistanceSphere` when a database is available, with a pure Haversine helper available as `calculate_distance_meters` for tests and offline workflows.

### Apply the geo database foundation

Use PostgreSQL with PostGIS enabled, then apply:

```powershell
psql $env:DATABASE_URL -f backend/database/migrations/001_geo_master.sql
```

The migration creates GiST indexes on all geometry columns for containment, radius, and distance queries.

### Seed Bengaluru demo geo data

```powershell
cd backend
python -m scripts.seed_geo_master
```

Set `DATABASE_URL` before running the seed script if your PostgreSQL connection is not `postgresql+psycopg://postgres:postgres@localhost:5432/aerointel`.

## Environmental Data Seed Foundation

Member 1 also owns the reproducible environmental seed pipeline in `backend/app/environmental_data` and `backend/scripts/seed_environmental_data.py`.

### Real public data included

The bundled fixture in `backend/data/environmental_seed.json` contains small deterministic extracts from public sources so demos and tests do not depend on live API availability:

- Air quality and pollutant readings: Jigani, Bengaluru - KSPCB 15-minute AQI CSV mirrored by OpenCity from CPCB CAAQM data. The full public CSV is referenced in the fixture source metadata.
- Weather and wind: Open-Meteo Historical Weather API for Bengaluru center on 2025-01-15, including temperature, relative humidity, wind speed, and wind direction.

Each source is recorded in `env_data_sources` with `provenance = 'real_public'`, source URL, license, and notes.

### Controlled demo scenarios

Operational signals that are difficult to access reliably during a hackathon are deliberately separated in `env_controlled_scenarios` with `provenance = 'controlled_demo'`:

- evening traffic congestion around Silk Board and Outer Ring Road
- CBD road resurfacing and construction material handling
- Peenya industrial stack-maintenance activity

These scenarios are realistic enough for hotspot investigation and attribution demos, but they are not mixed into real public observations.

### Apply and seed environmental data

Apply migrations in order, then run the seed:

```powershell
psql $env:DATABASE_URL -f backend/database/migrations/001_geo_master.sql
psql $env:DATABASE_URL -f backend/database/migrations/002_environmental_data.sql
cd backend
python -m scripts.seed_geo_master
python -m scripts.seed_environmental_data
```

The environmental seed is idempotent: sources and controlled scenarios are upserted, while readings are inserted only when the station/location, timestamp, pollutant, and source combination is missing.

## Provider-Independent Environmental Ingestion

`backend/app/environmental_data/adapters.py` keeps external provider formats out of the rest of AeroIntel. Application code should consume common DTOs only:

- `AirQualityReadingDTO`
- `WeatherObservationDTO`
- `WindObservationDTO`
- `ControlledScenarioDTO`
- `EnvironmentalIngestionBatch`

Available adapters:

- `OpenAQReadingsAdapter` maps OpenAQ-style station measurement responses into AQ DTOs.
- `OpenMeteoWeatherAdapter` maps Open-Meteo historical weather responses into weather DTOs.
- `OpenMeteoWindAdapter` maps the same Open-Meteo response shape into wind DTOs.
- `SeededEnvironmentalDataAdapter` maps `backend/data/environmental_seed.json` into the same DTOs for reliable local demos.

Use `EnvironmentalIngestionService(primary_adapters=[...], fallback_adapter=SeededEnvironmentalDataAdapter())` to try live providers first and gracefully fall back to seeded data when external APIs fail. The fallback batch is marked with `used_fallback = True` and includes provider error messages for observability without breaking demos.
