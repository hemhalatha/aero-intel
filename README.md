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
### Database configuration

The backend reads `DATABASE_URL` from environment variables, then from `.env` or `backend/.env` if present. Do not commit real local credentials.

Expected local format:

```powershell
DATABASE_URL=postgresql+psycopg://postgres:YOUR_PASSWORD@127.0.0.1:5432/aerointel
```

- Replace `YOUR_PASSWORD` with your real local PostgreSQL password.
- The project database name is `aerointel`.
- The local host is `127.0.0.1` and the default PostgreSQL port is `5432` unless your install uses a different host or port.
- The SQLAlchemy URL uses the `postgresql+psycopg` driver, matching the installed `psycopg[binary]` dependency.

Test the database connection before starting the API:

```powershell
cd backend
python -m app.scripts.check_db
```

### Run tests

```powershell
cd backend
pytest
```

### Run the Command Center frontend

```powershell
cd frontend
npm install
npm run dev
```

The React/Vite frontend opens the AeroIntel Command Center: city KPIs, interactive AQI map, heatmap layer, station markers, hotspot investigation entry points, weather/wind context, sensor health, worst wards, and city pollution trend. It consumes the backend APIs under `/api/v1/command-center`, `/api/v1/heatmap`, `/api/v1/hotspots`, and `/api/v1/sensor-health`. The frontend expects the backend at `http://127.0.0.1:8000`; override it with `VITE_API_BASE_URL` if needed.

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

Set `DATABASE_URL` before running the seed script using the format `postgresql+psycopg://postgres:YOUR_PASSWORD@127.0.0.1:5432/aerointel`.

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

## Hotspot Detection Engine

`backend/app/hotspots` provides a pure hotspot-candidate detection service. It reads latest station observations, historical ward baselines, AQI classification bands, and sensor-health reliability metadata from existing services, then returns candidate DTOs without creating or updating hotspot database records.

Detection supports configurable AQI threshold crossings, ward-baseline AQI deviation, pollutant-specific spikes for PM2.5, PM10, NO2, SO2, CO, O3/Ozone, and minimum data-quality confidence checks. Returned candidates include ward, station, AQI, pollutant snapshot, severity, alert level, trigger reasons, anomaly score, timestamp, and data-quality confidence.

## Hotspot Lifecycle Management

`backend/app/hotspot_lifecycle` manages persisted hotspot records after the pure detector returns candidates. The lifecycle service checks for an existing non-resolved hotspot in the same ward, updates it instead of creating duplicates, escalates severity when a candidate worsens, preserves observation history, records status transitions, stores detection context for later investigation and verification, and writes publishable event records.

Supported states are `ACTIVE`, `INVESTIGATING`, `WAITING_FOR_EVIDENCE`, `ACTION_ASSIGNED`, `UNDER_VERIFICATION`, and `RESOLVED`. Events include `hotspot.created`, `hotspot.escalated`, `hotspot.updated`, and `hotspot.resolved`.

FastAPI routes:

- `POST /api/v1/hotspots/candidates`
- `GET /api/v1/hotspots?status=ACTIVE`
- `GET /api/v1/hotspots/{hotspot_id}`
- `PATCH /api/v1/hotspots/{hotspot_id}/state`
- `GET /api/v1/hotspots/{hotspot_id}/observations`
- `GET /api/v1/hotspots/{hotspot_id}/status-history`
- `GET /api/v1/hotspots/{hotspot_id}/events`

This module does not perform investigation, attribution, recommendations, forecasting, fingerprinting, or intervention verification.

## Investigation Orchestrator

`backend/app/investigations` provides an event-driven investigation orchestration module. When a `hotspot.created` event is received, it creates or resumes an investigation for that hotspot, captures environmental context, runs all enabled evidence collectors independently, records collector run status and failures, stores successful evidence items immediately, and preserves partial results when another collector fails.

The orchestrator publishes investigation-local event records for `evidence.collected` as each evidence item is stored and `investigation.initial_collection_completed` after a collection pass. It marks investigations as `COMPLETE`, `PARTIALLY_COMPLETE`, or `WAITING_FOR_EVIDENCE` based on collector outcomes. Additional evidence requests reuse the existing investigation record instead of restarting the workflow.

FastAPI routes:

- `POST /api/v1/investigations/events/hotspot-created`
- `GET /api/v1/investigations?status=COMPLETE`
- `GET /api/v1/investigations/{investigation_id}`
- `POST /api/v1/investigations/{investigation_id}/evidence-requests`

Collectors implement the common `EvidenceCollector` interface and return normalized `CollectorResult` DTOs. This module does not perform source attribution, recommendations, forecasting, fingerprinting, or intervention verification.


## Common Evidence Repository

`backend/app/investigations/evidence.py` provides the shared evidence access layer that downstream modules should use instead of reading collector-specific tables directly. It standardizes every evidence item with evidence ID, investigation ID, source type, evidence type, detected flag, confidence, support direction, raw supporting details, data-quality score, collector name, checked timestamp, source, and collected timestamp.

Service methods:

- `get_investigation_evidence(investigation_id, source_type=None, evidence_type=None)`
- `get_supporting_evidence(investigation_id)`
- `get_contradictory_evidence(investigation_id)`
- `get_evidence_by_type(investigation_id, evidence_type)`
- `add_followup_evidence(evidence)`
- `update_evidence(evidence_id, update, reason=None)`
- `get_evidence_versions(evidence_id)`

FastAPI routes are mounted under `/api/v1/investigations`:

- `GET /{investigation_id}/evidence?source_type=traffic&evidence_type=traffic.density_anomaly`
- `GET /{investigation_id}/evidence/supporting`
- `GET /{investigation_id}/evidence/contradictory`
- `GET /{investigation_id}/evidence/types/{evidence_type}`
- `POST /{investigation_id}/evidence`
- `PATCH /evidence/{evidence_id}`
- `GET /evidence/{evidence_id}/versions`

Evidence updates preserve the previous evidence snapshot in `evidence_item_versions`, keeping later Pollution Fingerprint, Evidence Graph, Attribution, and Next Best Evidence modules insulated from collector-specific schemas while retaining audit history.

Apply the common evidence migration after the investigation tables are available:

```powershell
psql $env:DATABASE_URL -f backend/database/migrations/006_common_evidence_repository.sql
```


## Downstream Intelligence Integration Contract

`backend/app/intelligence_contract` defines the stable boundary between Member 1's environmental/investigation pipeline and downstream intelligence modules. Consumers should use this contract instead of reading environmental, hotspot, investigation, or collector tables directly.

FastAPI routes:

- `GET /api/v1/intelligence-contract/hotspots/{hotspot_id}`
- `GET /api/v1/intelligence-contract/investigations/{investigation_id}`

Query parameters:

- `start_at` and `end_at` select the historical comparison window; defaults to the last 24 hours.
- `pollutants` can be repeated to request specific series, for example `?pollutants=PM2.5&pollutants=NO2`.

The response includes hotspot ID, investigation ID, hotspot coordinates when present in detection context, current AQI, pollutant snapshot, historical ward AQI, historical pollutant series, current weather/wind, data-quality metadata, the standardized evidence bundle, supporting evidence, contradictory evidence, and canonical events.

Canonical events exposed to consumers:

- `hotspot.created`
- `evidence.collected`
- `investigation.initial_collection_completed`
- `investigation.completed`

Supported downstream consumers:

- pollution fingerprinting
- evidence graph generation
- source attribution
- uncertainty analysis
- next best evidence
- forecasting

Example payloads live in `backend/data/intelligence_contract_examples.json`.



## Member 1 End-to-End Workflow Verification

The deterministic workflow verifier in `backend/tests/test_member1_workflow_integration.py` exercises the complete Member 1 pipeline without requiring live external APIs or a local PostGIS database:

```powershell
pytest backend/tests/test_member1_workflow_integration.py -q -p no:cacheprovider
```

The verifier runs:

- environmental ingestion, seeded fallback behavior, normalization, quality rejection, and in-memory storage
- sensor-health validation and reliable-reading checks
- Command Center aggregation and AQI heatmap generation
- hotspot detection and lifecycle persistence
- investigation creation from `hotspot.created`
- traffic, construction/land-use, and industrial evidence collection
- supporting and contradictory evidence retrieval through the common evidence contract
- downstream intelligence handoff with standardized evidence bundles and canonical investigation events
- pollutant time-series retrieval for Pollution Fingerprinting
- follow-up evidence collection for Next Best Evidence workflows
- before/after environmental windows for Intervention Verification

It proves three predictable hotspot scenarios:

- construction-led hotspot: construction evidence supports, traffic evidence contradicts
- traffic-led hotspot: traffic evidence supports
- industrial-led hotspot: industrial evidence supports

A separate assertion verifies that the investigation remains `PARTIALLY_COMPLETE` and preserves successful evidence when one evidence collector fails.



## Uncertainty and Next Best Evidence

`backend/app/uncertainty` provides rule-based uncertainty assessment and next-best-evidence recommendations for downstream intelligence workflows. It consumes attribution rankings, pollution fingerprint output, evidence counts, evidence quality, collector completion state, and missing fingerprint features.

FastAPI route:

- `POST /api/v1/uncertainty/assessments`

The Uncertainty Engine evaluates:

- gap between the top attribution scores
- supporting evidence quantity
- contradictory evidence quantity
- evidence quality
- missing collectors
- missing pollution-fingerprint features

It returns `LOW`, `MEDIUM`, or `HIGH` uncertainty with traceable signals. When uncertainty is `MEDIUM` or `HIGH`, the Next Best Evidence Engine returns a structured request containing `requested_collectors` and an `orchestrator_payload` compatible with the Investigation Orchestrator's additional evidence request flow.

Prototype rule-table examples:

- Traffic and Construction close together -> request `pm10_pm25_fingerprint_analysis`
- Industrial and Traffic close together -> request `wind_source_alignment_analysis`
- Missing expected collectors -> request `missing_collector_check`
- Missing biomass/waste-burning marker -> request `biomass_burning_marker_check`

The module does not restart investigations and does not perform final attribution. It recommends the next check that can distinguish leading candidate sources.
## Evidence Graph Module

`backend/app/evidence_graph` converts hotspot context and standardized evidence into an explainable, reproducible graph. It uses NetworkX internally to assemble the graph, then persists graph versions in `evidence_graphs`, `evidence_graph_nodes`, and `evidence_graph_edges` so later reasoning paths can be replayed.

Supported node types:

- `HOTSPOT`
- `EVIDENCE`
- `POLLUTION_SOURCE`
- `WEATHER_CONDITION`
- `GEOGRAPHIC_ENTITY`
- `POLLUTANT`

Supported edge types:

- `SUPPORTS`
- `CONTRADICTS`
- `NEAR`
- `UPWIND_OF`
- `ACTIVE_DURING`
- `CORRELATED_WITH`
- `OBSERVED_AT`

FastAPI routes:

- `POST /api/v1/evidence-graphs/investigations/{investigation_id}` builds and optionally persists a graph from the downstream intelligence contract.
- `POST /api/v1/evidence-graphs/hotspots/{hotspot_id}` builds and optionally persists a graph from a hotspot handoff.
- `GET /api/v1/evidence-graphs/investigations/{investigation_id}` returns the latest persisted graph for an investigation.
- `GET /api/v1/evidence-graphs/hotspots/{hotspot_id}` returns the latest persisted graph for a hotspot.

Responses are frontend-friendly JSON with stable `nodes`, `edges`, labels, properties, and graph metrics. The graph is not a black-box model and does not perform source attribution; it organizes existing evidence relationships for explanation, review, and downstream reasoning.

Apply the migration after the common evidence repository migration:

```powershell
psql $env:DATABASE_URL -f backend/database/migrations/007_evidence_graph.sql
```
## Pollution Fingerprint Engine

`backend/app/pollution_fingerprint` derives structured source-fingerprint features from the downstream intelligence contract. It consumes pollutant snapshots, historical ward AQI, wind/evidence metadata, and standardized evidence bundles without reading Member 1 database tables directly.

FastAPI routes:

- `GET /api/v1/pollution-fingerprints/hotspots/{hotspot_id}`
- `GET /api/v1/pollution-fingerprints/investigations/{investigation_id}`

Query parameters:

- `start_at` and `end_at` select the historical context window.
- `pollutants` can be repeated to request additional pollutant series through the underlying intelligence contract.

Extracted features include PM10/PM2.5 ratio, NO2, CO, SO2, traffic anomaly, rush-hour correlation, construction proximity, industrial proximity, wind alignment, temporal persistence, and optional biomass/waste-burning markers. Configurable source patterns live in `backend/app/pollution_fingerprint/config.py` for Construction Dust, Vehicular Emissions, Industrial Emissions, Road Dust, and Biomass or Waste Burning.

The response returns extracted feature values, pattern-match scores for every source, missing fingerprint features, and data-quality confidence. It deliberately sets `is_final_attribution = false`; Attribution and Uncertainty modules should consume this output as evidence, not as a final source decision.
## Operations, Advisory, and Verification Contract

`backend/app/operations_contract` defines the read-only API boundary for operations, citizen advisory, and intervention-verification modules. Consumers should use this contract instead of reading Member 1 environmental, geo, hotspot, or sensor-health tables directly.

FastAPI routes:

- `GET /api/v1/operations-contract/wards/{ward_code}/state`
- `GET /api/v1/operations-contract/wards/{ward_code}/readings`
- `GET /api/v1/operations-contract/wards/{ward_code}/readings/around`
- `GET /api/v1/operations-contract/wards/{ward_code}/intervention-verification`

The ward-state response exposes current ward AQI, CPCB AQI band, pollutant readings, hotspot status, hotspot recurrence history, ward details, sensor-health snapshots, and a data-quality rollup. It is designed for operations dashboards and citizen advisory workflows that need a reliable current view without knowing the database layout.

The generic time-window endpoint accepts `start_at`, `end_at`, optional `pollutant`, optional `station_code`, and optional `selected_at`. The `/readings/around` helper accepts a selected timestamp plus a configurable context window for investigation timelines.

The intervention-verification endpoint accepts `intervention_at`, optional `baseline_hours`, optional `evaluation_hours`, optional `pollutant`, optional `station_code`, optional `intervention_id`, and optional `forecast_location_code`. It returns three stable segments:

- `pre_intervention_baseline`
- `predicted_evaluation_window`
- `actual_post_intervention`

The contract only retrieves and packages environmental, weather, wind, hotspot, ward, and data-quality context. It does not implement citizen-advisory rules, intervention scoring, forecasting, attribution, or hotspot detection.
## Traffic Evidence Collector

`backend/app/investigations/traffic.py` provides an independent traffic evidence collector for hotspot investigations. It identifies nearby road segments, retrieves current traffic density, compares against historical traffic baselines for comparable hours, calculates density deviation, checks rush-hour correlation, evaluates road proximity, optionally enriches evidence with NO2 and CO patterns from environmental readings, and returns a standardized evidence object.

Returned evidence includes `source_type`, `evidence_type`, `detected`, `confidence`, `support_direction` (`SUPPORTS`, `CONTRADICTS`, or `NEUTRAL`), raw supporting details, and `observed_at`. The collector only generates evidence and does not calculate final traffic-causation probability. When live traffic or geo dependencies are unavailable, it falls back to realistic seeded traffic corridors so demo investigations remain reproducible.

## Construction and Land-Use Evidence Collector

`backend/app/investigations/construction.py` provides an independent construction and land-use evidence collector. For a hotspot, it finds active construction permits within a configurable radius through a PostGIS-ready provider, verifies permit validity and activity dates, calculates site distances, counts nearby construction clusters, identifies surrounding land-use classifications, analyzes PM10 and PM2.5 context when available, evaluates whether wind direction supports transport from the site toward the hotspot, and returns common evidence output.

Returned evidence uses `source_type="construction_land_use"`, `evidence_type="construction.land_use_activity"`, `detected`, `confidence`, `support_direction` (`SUPPORTS`, `CONTRADICTS`, or `NEUTRAL`), raw permit/site/land-use/PM/wind details, and `observed_at`. The collector only generates evidence for later fingerprinting, evidence graphs, and explanations; it does not calculate final source attribution probability. Seeded permit and land-use data are used when live PostGIS permit data or geo dependencies are unavailable.

## Industrial Evidence Collector

`backend/app/investigations/industrial.py` provides an independent industrial evidence collector. For a hotspot, it finds nearby industrial units, evaluates pollution category, consent and compliance status, distance, relevant SO2/NO2/CO anomalies, current-wind upwind alignment, and temporal alignment between reported industrial activity and the hotspot.

Returned evidence uses `source_type="industrial"`, `evidence_type="industrial.activity_signal"`, `detected`, `confidence`, `support_direction`, structured raw unit/compliance/pollutant/wind/activity details, and `observed_at`. The collector only generates evidence for later Evidence Graph and Pollution Fingerprint modules; it does not calculate final source attribution probability. Seeded industrial units are used when live industrial registry data is unavailable.
