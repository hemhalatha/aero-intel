# AeroIntel

AeroIntel is an AI-powered Urban Air Quality Command Center for monitoring city-wide pollution, detecting hotspots, collecting investigation evidence, and handing structured environmental intelligence to downstream decision modules.

The project is built as a modular monolith with clear backend module boundaries, a React command-center frontend, and a PostgreSQL/PostGIS data foundation. It is designed for deterministic demos as well as integration with real public environmental data sources.

## What AeroIntel Does

AeroIntel turns raw environmental observations into operational intelligence:

1. Ingest monitoring-station, pollutant, weather, wind, and seeded scenario data.
2. Normalize readings, validate quality, reject impossible values, remove duplicates, and attach ward context.
3. Store reliable environmental time-series data with quality metadata.
4. Generate AQI heatmaps and ward summaries from reliable monitoring stations.
5. Detect hotspot candidates using configurable thresholds, historical baselines, pollutant spikes, and sensor reliability checks.
6. Manage hotspot lifecycle states and publish domain events.
7. Trigger investigations and collect traffic, construction, land-use, and industrial evidence independently.
8. Store standardized evidence with version history.
9. Produce pollution fingerprints, evidence graphs, uncertainty assessments, and downstream integration contracts.
10. Present the current city state in a premium command-center dashboard.

## Core Capabilities

| Area | Capabilities |
| --- | --- |
| Geo master | Cities, wards, monitoring stations, roads, land-use zones, PostGIS polygons, point containment, radius search, distance calculations |
| Environmental data | Provider-independent adapters, seeded fallback data, normalization, quality validation, pollutant/weather/wind time-series storage |
| Sensor health | ONLINE, DELAYED, DEGRADED, and OFFLINE classification with reliability checks and health history |
| AQI engine | Deterministic CPCB AQI band classification through configurable thresholds |
| Heatmap | IDW interpolation, configurable grid resolution, bounding boxes, ward-level AQI summaries, unhealthy sensor weighting |
| Command Center | Optimized dashboard aggregation API and React UI with map, KPIs, trends, weather, wind, stations, wards, and hotspots |
| Hotspots | Detection service, lifecycle management, status history, observations, and event publishing |
| Investigations | Event-driven orchestration, pluggable evidence collectors, partial-failure tolerance, follow-up evidence collection |
| Evidence | Common evidence repository with supporting/contradictory filters and version history |
| Intelligence | Pollution fingerprints, explainable evidence graph, uncertainty scoring, next-best-evidence requests, integration contracts |

## Architecture

AeroIntel follows a modular monolith architecture. Each backend module keeps API routes, schemas, services, repositories, and models separate where applicable.

```text
React + Vite Command Center
        |
        | REST /api/v1
        v
FastAPI backend
        |
        | SQLAlchemy / GeoAlchemy2
        v
PostgreSQL + PostGIS
```

Key backend principles:

- API routes stay thin and delegate business logic to services.
- Services expose reusable methods for other modules.
- Repositories own persistence concerns.
- Pydantic schemas define stable contracts.
- Downstream modules consume service/API contracts instead of internal database tables.
- Demo data is deterministic and clearly separated from real/provider-sourced data.

## Repository Layout

```text
.
|-- backend/
|   |-- app/
|   |   |-- aqi/                       # CPCB AQI classification engine
|   |   |-- command_center/            # Dashboard aggregation API
|   |   |-- environmental_data/        # Ingestion, normalization, time-series storage
|   |   |-- evidence_graph/            # Explainable graph persistence and API
|   |   |-- geo_master/                # Cities, wards, stations, roads, land-use, spatial services
|   |   |-- heatmap/                   # AQI interpolation and ward summaries
|   |   |-- hotspot_lifecycle/         # Hotspot records, state transitions, events
|   |   |-- investigations/            # Orchestrator and evidence collectors
|   |   |-- intelligence_contract/     # Handoff contract for downstream intelligence modules
|   |   |-- operations_contract/       # Read-only contracts for operations, advisory, verification
|   |   |-- pollution_fingerprint/     # Feature extraction and source pattern matching
|   |   |-- sensor_health/             # Sensor reliability and health status
|   |   |-- uncertainty/               # Uncertainty and next-best-evidence rules
|   |   |-- database.py                # Database URL loading, connectivity, and diagnostics
|   |   `-- main.py                    # FastAPI application entrypoint
|   |-- database/migrations/          # SQL migrations
|   |-- data/                         # Seed datasets
|   |-- scripts/                      # Reproducible seed loaders
|   `-- tests/                        # Backend tests
|-- frontend/                         # Wrapper for the expected frontend workflow
|-- src/                              # Active React/Vite frontend source
|-- DESIGN-apple.md                   # Frontend design system
|-- render.yaml                       # Render deployment blueprint
|-- .env.example                      # Safe environment template
`-- README.md
```

## Tech Stack

| Layer | Technology |
| --- | --- |
| Backend API | Python, FastAPI, Pydantic |
| Persistence | PostgreSQL, PostGIS, SQLAlchemy, GeoAlchemy2, psycopg 3 |
| Data processing | Python services, repository pattern, deterministic seed loaders |
| Graph reasoning | NetworkX |
| Frontend | React, Vite, TypeScript, Tailwind CSS |
| Maps and visualization | Leaflet / React Leaflet, Recharts |
| Deployment | Render Blueprint (`render.yaml`) |

## Backend Modules

### Geo Master

Provides reusable spatial services for city entities:

- Find the ward containing a latitude/longitude.
- Find wards, stations, road segments, and land-use zones within a configurable radius.
- Calculate distances between geographic points.

### Environmental Data

Owns ingestion, normalization, storage, and retrieval of environmental observations:

- Provider-independent AQI, weather, wind, and seeded-data adapters.
- Normalized schemas for AQI, pollutants, weather, and wind.
- Data-quality status on returned readings.
- Historical baselines and arbitrary time-window queries.

### Sensor Health

Classifies monitoring stations as `ONLINE`, `DELAYED`, `DEGRADED`, or `OFFLINE` using configurable rules for stale readings, missing fields, impossible values, repeated readings, and abnormal behavior.

### Hotspots and Investigations

The hotspot detection service returns candidates. The lifecycle module owns persistence, state transitions, status history, and events. The investigation orchestrator reacts to hotspot events, runs evidence collectors independently, preserves partial results, and supports follow-up evidence requests.

### Intelligence Contracts

The intelligence and operations contracts expose stable read-only APIs for downstream modules such as pollution fingerprinting, evidence graph generation, source attribution, uncertainty analysis, next-best-evidence, forecasting, citizen advisory, and intervention verification.

## API Surface

When the backend is running, interactive API documentation is available at:

```text
http://127.0.0.1:8000/docs
```

Common endpoints include:

| Endpoint | Purpose |
| --- | --- |
| `GET /health` | Application health check |
| `GET /api/v1/command-center/dashboard` | Complete command-center dashboard payload |
| `GET /api/v1/heatmap/current` | Current AQI heatmap grid for a map bounding box |
| `GET /api/v1/heatmap/wards` | Ward-level AQI summaries |
| `GET /api/v1/environmental/stations/latest` | Latest station readings with quality metadata |
| `GET /api/v1/environmental/readings/window` | Generic environmental time-window retrieval |
| `GET /api/v1/sensor-health/stations` | Station health statuses |
| `GET /api/v1/hotspots` | Hotspot lifecycle records |
| `GET /api/v1/investigations/{investigation_id}/evidence` | Standardized evidence bundle |
| `GET /api/v1/intelligence-contract/hotspots/{hotspot_id}` | Handoff payload for intelligence modules |
| `GET /api/v1/operations-contract/wards/{ward_code}/state` | Operations/advisory ward state contract |
| `GET /api/v1/pollution-fingerprints/hotspots/{hotspot_id}` | Pollution fingerprint features and pattern scores |
| `GET /api/v1/evidence-graphs/hotspots/{hotspot_id}` | Frontend-friendly explainable evidence graph |

## Demo Scenarios

The seed data supports deterministic hotspot workflows for:

| Scenario | Expected evidence pattern |
| --- | --- |
| Construction-led hotspot | PM10/PM2.5-heavy profile, nearby active construction permits, land-use context, wind support where applicable |
| Traffic-led hotspot | NO2/CO elevation, road proximity, traffic-density deviation, rush-hour correlation |
| Industrial-led hotspot | SO2/NO2/CO anomalies, nearby industrial units, compliance context, wind and temporal alignment |

These scenarios are intentionally reproducible so the full pipeline can be demonstrated even when external APIs are unavailable.

## Local Development

### Prerequisites

- Python 3.11 or newer
- Node.js 18 or newer
- PostgreSQL with PostGIS enabled
- A local database named `aerointel`

### Environment Configuration

Copy `.env.example` to `.env` or `backend/.env` and replace `YOUR_PASSWORD` with your local PostgreSQL password.

```env
DATABASE_URL=postgresql+psycopg://postgres:YOUR_PASSWORD@127.0.0.1:5432/aerointel
ALLOWED_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
VITE_API_BASE_URL=http://127.0.0.1:8000
```

Do not commit real credentials.

### Backend Setup

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m app.scripts.check_db
python -m app.scripts.apply_migrations
python -m scripts.seed_geo_master
python -m scripts.seed_environmental_data
uvicorn app.main:app --reload --port 8000
```

Backend URL:

```text
http://127.0.0.1:8000
```

### Frontend Setup

The active Vite app lives at the repository root, and `frontend/` provides the expected workflow wrapper.

```powershell
cd frontend
npm run install:root
npm run dev
```

Frontend URL:

```text
http://127.0.0.1:5173
```

## Testing and Verification

Backend tests:

```powershell
cd backend
pytest
```

Frontend production build:

```powershell
cd frontend
npm run build
```

Database connectivity check:

```powershell
cd backend
python -m app.scripts.check_db
```

Typical smoke checks after startup:

```text
GET http://127.0.0.1:8000/health
GET http://127.0.0.1:8000/api/v1/command-center/dashboard
GET http://127.0.0.1:8000/api/v1/hotspots?status=ACTIVE
```

## Deployment

The repository includes a Render Blueprint in `render.yaml` with:

- `aerointel-api`: FastAPI web service from `backend/`
- `aerointel-command-center`: static Vite frontend from the repository root
- `aerointel-db`: managed PostgreSQL database

Production environment variables:

| Variable | Service | Description |
| --- | --- | --- |
| `DATABASE_URL` | Backend | PostgreSQL connection URL. In Render this is wired from the managed database. |
| `ALLOWED_ORIGINS` | Backend | Comma-separated list of allowed frontend origins. |
| `VITE_API_BASE_URL` | Frontend | Public backend API base URL used at build time. |

After provisioning the database, run migrations and seed scripts against the production database before demoing the full workflow.

## Operational Notes

- Database authentication failures are diagnosed through `python -m app.scripts.check_db`.
- External providers should fail gracefully to seeded demo data where adapters support fallback behavior.
- Evidence collectors are expected to preserve partial investigation progress if one source fails.
- Downstream intelligence modules should consume standardized contracts, not internal tables.
- Frontend changes should follow `DESIGN-apple.md` as the authoritative visual design system.

## Security Notes

- Do not commit `.env` files or real database credentials.
- Keep database URLs in environment variables.
- Avoid exposing raw stack traces or sensitive connection details in API responses.
- Use the service and repository layers for validation and parameterized database access.

## Project Status

AeroIntel currently provides the end-to-end foundation for the environmental-data-to-investigation workflow, including deterministic demo scenarios and frontend command-center visualization. Forecasting, final source attribution, citizen advisory, and intervention execution modules are intended to consume the contracts exposed by this codebase.
