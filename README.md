# AeroIntel

This repository contains the AI-powered Urban Air Quality Command Center backend and frontend modules. The current backend foundations cover source attribution, explanations, geo master data, environmental seed data, and provider-independent environmental ingestion.

## Source Attribution

The API accepts an evidence bundle and ranks construction dust, vehicular pollution, industrial emission, road dust, and biomass burning. Scores are weighted, normalized to 100%, and returned with the evidence that affected each source.

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

### Source Attribution Contract

`POST /api/v1/attributions` accepts the existing evidence-bundle fields (`traffic`, `construction`, `industry`, `satellite`, `wind_direction`, and `wind_speed`) plus optional `road_dust`, `biomass_burning`, `historical_patterns`, and `pm25` values. See `backend/data/mock_evidence.json` for a complete request.

## Explanation Generator

`POST /api/v1/explanations` accepts the same evidence bundle and returns a short headline, a plain-language summary, and the weighted evidence supporting the primary source. This endpoint lets the dashboard explain *why* the source was selected rather than presenting a score alone.

## Geo Master Foundation

The independent `geo_master` backend module provides city and spatial reference data. It defines SQLAlchemy models, Pydantic schemas, repositories, services, migration SQL, and seeded demo data for:

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

The reproducible environmental seed pipeline lives in `backend/app/environmental_data` and `backend/scripts/seed_environmental_data.py`.

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

## Environmental Data Normalization

`backend/app/environmental_data/normalization.py` converts provider-independent ingestion DTOs into repository-ready records before storage.

Normalization responsibilities:

- converts all reading timestamps to UTC
- validates pollutant names and values
- rejects impossible negative pollutant values
- handles missing pollutant names or values by logging rejected records
- prevents duplicate readings within a batch using station, timestamp, pollutant, and source
- maps external provider station IDs to internal station codes with `StationMapping`
- attaches ward codes through an injected resolver, including `GeoMasterWardResolver` for PostGIS-backed lookups
- assigns `data_quality_status` as `valid`, `suspect`, or `incomplete`
- returns `EnvironmentalNormalizationResult` with accepted `NormalizedAirQualityReading` records and rejected `RejectedEnvironmentalRecord` logs

Apply the normalization migration after the environmental data migration:

```powershell
psql $env:DATABASE_URL -f backend/database/migrations/003_environmental_normalization.sql
```

## Environmental Time-Series Retrieval

`backend/app/environmental_data/time_series.py` and `time_series_repository.py` provide storage and retrieval only. They do not implement hotspot detection, forecasting models, attribution, pollution fingerprinting, or intervention verification.

Service methods:

- `get_latest_station_readings()`
- `get_station_history(station_code, start_at, end_at)`
- `get_ward_aqi_history(ward_code, start_at, end_at)`
- `get_ward_pollutant_history(ward_code, pollutant, start_at, end_at)`
- `get_historical_baseline(ward_code, pollutant, start_at, end_at, comparison_days=28)`
- `get_current_weather(location_code=None)`
- `get_current_wind(location_code=None)`
- `get_weather_forecast(location_code, start_at, end_at)`
- `get_readings_for_time_window(station_code=None, ward_code=None, pollutant=None, start_at=None, end_at=None)`

FastAPI routes are mounted under `/api/v1/environmental` for latest station state, station history, ward AQI and pollutant history, historical baselines, current weather/wind, weather forecasts, and arbitrary time-window retrieval. Returned pollutant readings include `data_quality_status` so downstream modules can reject unreliable observations.

Apply the time-series forecast migration after normalization:

```powershell
psql $env:DATABASE_URL -f backend/database/migrations/004_environmental_time_series.sql
```

## Sensor Health Monitoring

`backend/app/sensor_health` is an independent monitoring module for station reliability. It classifies monitoring stations as `ONLINE`, `DELAYED`, `DEGRADED`, or `OFFLINE` using configurable rules for last reading age, missing pollutant fields, invalid values, repeated identical readings, and abnormal sensor behavior.

Stored health data:

- current station health in `sensor_health_current`
- historical health changes in `sensor_health_history`
- data-quality score, reasons, missing pollutants, invalid pollutants, repeated pollutants, and reliability flag

FastAPI routes are mounted under `/api/v1/sensor-health`:

- `GET /stations`
- `GET /stations/{station_code}`
- `GET /stations/{station_code}/history`
- `GET /reliability?status=ONLINE&data_quality_score=0.9`

Analytics modules should use `SensorHealthService.is_reading_reliable(status, data_quality_score)` before using sensor readings for hotspot detection, pollution fingerprinting, or intervention verification.

Apply the sensor health migration after the environmental time-series migration:

```powershell
psql $env:DATABASE_URL -f backend/database/migrations/005_sensor_health.sql
```

## AQI Classification Engine

`backend/app/aqi` provides a deterministic AQI classification engine for shared use by the Command Center, hotspot detection, citizen advisory, escalation rules, and verification dashboards.

The CPCB AQI bands live in `backend/app/aqi/config.py` as configuration, not duplicated business logic. Use `classify_aqi(aqi)` or instantiate `AQIClassifier(CPCB_AQI_BANDS)` to return:

- AQI band
- severity rank
- display label
- health severity category

The default CPCB bands cover `0-500` and reject negative or out-of-range values explicitly.

## AQI Spatial Heatmap Service

`backend/app/heatmap` generates a Leaflet/Mapbox-ready AQI pollution layer from latest monitoring-station coordinates and AQI readings. The current implementation uses Inverse Distance Weighting through `IDWInterpolator`, which implements an interpolation interface so Kriging or satellite-ground fusion can replace it later without changing the API.

Features:

- configurable grid resolution
- requested map bounding boxes
- ward-level average AQI summaries
- exclusion or reduced weighting for unhealthy sensors
- GeoJSON FeatureCollection output for map clients

FastAPI routes:

- `GET /api/v1/heatmap/current`
- `GET /api/v1/heatmap/wards`

The repository gathers latest AQI readings, station coordinates, and sensor-health reliability metadata. The service only creates spatial visualization data; it does not perform hotspot detection, attribution, escalation, or forecasting.

## Command Center Aggregation API

`backend/app/command_center` provides a read-only aggregation service for the initial dashboard load. It composes existing environmental time-series, heatmap, sensor-health, and hotspot-summary provider interfaces without implementing hotspot detection, source attribution, forecasting, fingerprinting, or intervention logic.

FastAPI route:

- `GET /api/v1/command-center/dashboard`

The response includes city average AQI, worst affected ward, active hotspot count, offline/degraded station count, latest reliable station readings, weather summary, wind information, current hotspot summaries, and city-level pollution trend. The default hotspot provider returns an empty list until a dedicated hotspot module is connected.
