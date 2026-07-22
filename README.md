# 🌍 AeroIntel — AI-Powered Urban Air Quality Command Center

> **From Reactive Monitoring to Evidence-Based Intervention**  
> *Smart India Hackathon Project | Theme: Smart Cities / Environmental Intelligence / Geospatial Analytics / Public Health*

---

## 📋 Table of Contents

- [1. Executive Summary \& Pitch Presentation](#1-executive-summary--pitch-presentation)
  - [Slide 1: Vision \& Solution Overview](#slide-1-vision--solution-overview)
  - [Slide 2: Problem Context \& The Intelligence Gap](#slide-2-problem-context--the-intelligence-gap)
  - [Slide 3: Closed-Loop Decision Engine](#slide-3-closed-loop-decision-engine)
  - [Slide 4 \& 5: The 8 Core Modules](#slide-4--5-the-8-core-modules)
  - [Slide 6: System Architecture](#slide-6-system-architecture)
  - [Slide 7: Multi-Agent AI Workflow](#slide-7-multi-agent-ai-workflow)
  - [Slide 8: Team Allocation \& Workload Ownership](#slide-8-team-allocation--workload-ownership)
  - [Slide 9: Demonstrated Impact \& Evaluation Alignment](#slide-9-demonstrated-impact--evaluation-alignment)
- [2. Comprehensive Technical Engineering Blueprint](#2-comprehensive-technical-engineering-blueprint)
  - [Module 1: AI Command Center](#module-1-ai-command-center)
  - [Module 2: Hotspot Detection Engine](#module-2-hotspot-detection-engine)
  - [Module 3: AI Multi-Source Investigation](#module-3-ai-multi-source-investigation)
  - [Module 4: Evidence Collection \& Source Attribution](#module-4-evidence-collection--source-attribution)
  - [Module 5: Prediction Engine \& Scenario Simulator](#module-5-prediction-engine--scenario-simulator)
  - [Module 6: AI Actionable Interventions](#module-6-ai-actionable-interventions)
  - [Module 7: Department Assignment \& Accountability](#module-7-department-assignment--accountability)
  - [Module 8: Citizen Health Risk Advisory](#module-8-citizen-health-risk-advisory)
- [3. Database Schema \& Geo Master Spatial Operations](#3-database-schema--geo-master-spatial-operations)
- [4. API Endpoint Contracts \& Data Specifications](#4-api-endpoint-contracts--data-specifications)
- [5. How to Run \& Verification Guide](#5-how-to-run--verification-guide)

---

# 1. Executive Summary & Pitch Presentation

### Slide 1: Vision & Solution Overview
**AeroIntel** is a closed-loop urban air quality decision intelligence platform designed for municipal corporations and State Pollution Control Boards. While existing systems function as static dashboards that simply display AQI numbers, AeroIntel fuses continuous monitoring station data (CAAQMS), satellite remote sensing (Sentinel-5P/MODIS), mobility feeds, meteorological forecasts, and geospatial land-use layers to:

1. **Explain WHY pollution happens** (*Geospatial Source Attribution with Confidence Scores*)
2. **Predict WHAT happens next** (*Hyperlocal 24-72h AQI Forecasting & Scenario Simulation*)
3. **Recommend HOW to act** (*Prioritized Multi-Agency Interventions with ROI & Effort Estimates*)
4. **Assign WHO is accountable** (*Inter-Departmental Task Workflow & Auto-Escalation Engine*)
5. **Protect CITIZENS proactively** (*Multilingual Ward-Level Vulnerability Advisories*)

---

### Slide 2: Problem Context & The Intelligence Gap
* **The National Crisis:** India's air pollution crisis causes **1.67 million premature deaths annually** (*The Lancet Planetary Health*). 24 of India's 50 most polluted cities are Tier 1 or Tier 2 urban centers.
* **The Data Exists:** India has deployed over **900 Continuous Ambient Air Quality Monitoring Stations (CAAQMS)** under the National Clean Air Programme (NCAP).
* **The CAG Audit Insight:** A 2024 CAG audit found that **only 31% of cities with monitoring data had any actionable multi-agency response protocols** linked to those readings.
* **The Missing Intelligence Layer:** City administrations do not need more red markers on a dashboard. They need **geospatial attribution** (which sources are responsible at this location right now), **predictive forecasting** (what AQI will be in 24 hours under different intervention scenarios), and **enforcement intelligence** (where to deploy inspectors for maximum impact).

---

### Slide 3: Closed-Loop Decision Engine

```text
  [ 📡 1. MONITOR ] ──> [ 🚨 2. DETECT ] ──> [ 🕵️‍♂️ 3. INVESTIGATE ]
                                                         │
  [ 🎯 6. RECOMMEND ] <── [ 🔮 5. FORECAST ] <── [ 🧩 4. ATTRIBUTE ]
          │
          └──> [ 📋 7. ASSIGN & TRACK ] ──> [ 📢 8. CITIZEN ADVISORY ]
```

---

### Slide 4 & 5: The 8 Core Modules

1. **AI Command Center (Module 1):** Full-screen interactive GIS map with IDW spatial AQI heatmaps, station status markers, wind vector overlays, weather summary widgets, city KPIs, and worst ward panels.
2. **Hotspot Detection Engine (Module 2):** Real-timeWatcher Agent combining CPCB statutory threshold checks with rolling Z-score statistical anomaly detection and ward deduplication.
3. **Multi-Source AI Investigation (Module 3):** Interactive "Detective Board" timeline triggering 5 parallel evidence collectors: Satellite aerosol/dust signatures, Traffic density anomalies, Construction permits, Industrial stack registry, and Land-use zoning.
4. **Evidence Attribution & Explanation (Module 4):** Weighted multi-factor scoring engine attributing pollution across Construction Dust, Vehicular Emissions, Industrial Emissions, Road Dust, and Biomass Burning with confidence percentages and natural-language "Why?" evidence breakdowns.
5. **Hyperlocal Forecast & Scenario Simulator (Module 5):** Time-series baseline forecasting (Scenario A: No Action) vs. Intervention effect modifier simulation (Scenario B: With Action) displaying headline stats like `"-42 AQI Points Saved"`.
6. **AI Recommendations Engine (Module 6):** Ranked actionable intervention cards based on expected AQI drop, priority (High/Med/Low), and implementation effort (Low/Med/High), with interactive toggles linked directly to the Scenario Simulator.
7. **Department Assignment & Accountability (Module 7):** Action-to-Department task routing (Municipal Corp, Traffic Police, Pollution Control Board), SLA tracking, repeat-hotspot recurrence tracking, and senior officer escalation banners.
8. **Citizen Health Risk Advisory (Module 8):** Ward-level health guidance tailored to vulnerable populations (General, Schools, Elderly) rendered in regional languages (English, Hindi, Kannada, Tamil).

---

### Slide 6: System Architecture

```text
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                                 EXTERNAL DATA FEEDS                                    │
│       CPCB / CAAQMS  │  OpenWeatherMap / IMD  │  Sentinel-5P Satellite  │ GIS Land Use │
└───────────────────────────────────────────┬────────────────────────────────────────────┘
                                            │
                                            ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                              FASTAPI BACKEND SERVICES                                  │
│  ┌───────────────────────┐   ┌────────────────────────┐   ┌─────────────────────────┐  │
│  │ GeoMaster & PostGIS   │   │  Evidence Collectors   │   │ Baseline Forecaster     │  │
│  └───────────────────────┘   └────────────────────────┘   └─────────────────────────┘  │
│  ┌───────────────────────┐   ┌────────────────────────┐   ┌─────────────────────────┐  │
│  │ Attribution Engine    │   │  Scenario Simulator    │   │ Task & Escalation Engine│  │
│  └───────────────────────┘   └────────────────────────┘   └─────────────────────────┘  │
└───────────────────────────────────────────┬────────────────────────────────────────────┘
                                            │
                                            ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                           POSTGRESQL + POSTGIS DATA STORE                              │
│       stations  │  station_readings  │  hotspots  │  investigations  │  tasks              │
└───────────────────────────────────────────┬────────────────────────────────────────────┘
                                            │
                                            ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                              REACT + TAILWIND FRONTEND                                 │
│ Command Center Map │ Detective Board │ Attribution Diagnosis │ Scenario Line Charts    │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

---

### Slide 7: Multi-Agent AI Workflow

| Agent Name | Trigger Event | Primary Responsibility | Target Output / State |
| :--- | :--- | :--- | :--- |
| **Ingestion Agent** | Scheduled (5-15 min) | Pulls and normalizes external station, weather, and wind feeds | `station_readings` |
| **Watcher Agent** | New Reading Batch | Evaluates CPCB thresholds and rolling Z-score anomalies | Trigger `hotspots` event |
| **Dedup Agent** | Hotspot Trigger | Merges simultaneous nearby ward triggers | Unique `hotspots` record |
| **Investigation Orchestrator** | Hotspot Created | Fans out 5 parallel evidence checks | `investigations` bundle |
| **Attribution Agent** | Investigation Complete | Computes weighted evidence scores across candidate sources | `attributions` confidence % |
| **Explanation Agent** | Attribution Written | Converts supporting evidence into natural language copy | "Why?" summary breakdown |
| **Forecasting Agent** | Hotspot Created | Computes baseline 24-72h AQI trajectory (Scenario A) | `forecasts` (No Action) |
| **Simulation Agent** | Action Selected | Applies intervention effect modifiers to baseline forecast | `forecasts` (With Action) |
| **Assignment Agent** | Action Confirmed | Routes task to owning department and sets SLA due dates | `tasks` record |
| **Escalation Agent** | Scheduled Job | Monitors recurrence and unresolved duration per ward | `escalations` trigger |
| **Advisory Agent** | Band Change | Determines correct health advisory template for ward | `ward_advisories` |
| **Translation Agent** | Advisory Generated | Translates health guidance into English, Hindi, Kannada, Tamil | Localized Advisory UI |

---

### Slide 8: Team Allocation & Workload Ownership

Designed for complete vertical slice balance across a 3-member engineering team:

* 👤 **Member 1 — Data, Detection & Investigation:** Geo Master schema, spatial queries, ingestion scheduler, sensor health, hotspot lifecycle, evidence collectors (Traffic, Construction, Industrial), Command Center Map & Investigation Detective Board UI.
* 👤 **Member 2 — Intelligence & Decision Support:** Satellite & Biomass evidence collectors, evidence graph repository, source attribution scoring engine, explanation generator, baseline AQI forecaster, recommendation engine, scenario simulator, Attribution Diagnosis Cards & Scenario Chart UI.
* 👤 **Member 3 — Operations, Advisory & Frontend Lead:** Shared UI design system, department mapping, task assignment workflow, accountability & escalation engine, citizen advisory backend & frontend.

---

### Slide 9: Demonstrated Impact & Evaluation Alignment

| Evaluation Criteria | Weight | How AeroIntel Solves & Demonstrates It |
| :--- | :--- | :--- |
| **Innovation** | **25%** | Fuses spatial-temporal station data, satellite aerosol signatures, traffic density, and municipal permits into an explainable multi-factor attribution engine with dynamic what-if simulation. |
| **Business Impact** | **25%** | Fills the CAG audit gap by bridging raw sensor data directly into departmental accountability workflows, SLAs, and enforcement task prioritisation. |
| **Technical Excellence**| **20%** | PostGIS spatial query engine (`ST_Contains`, `ST_DWithin`), multi-agent orchestration, automated explanation generation, and 100% type-safe React/Vite TypeScript frontend code. |
| **Scalability** | **15%** | Standardized data adapters (CPCB/OpenAQ format), provider-independent ingestion layer, and PostGIS spatial indexing scalable to any Tier 1/2 urban center in India. |
| **User Experience** | **15%** | Sleek dark-mode theme, interactive "Detective Board" timeline, side-by-side scenario charts, and multilingual citizen advisories in 4 regional languages. |

---

# 2. Comprehensive Technical Engineering Blueprint

```
backend/
├── app/
│   ├── main.py                     # FastAPI application entrypoint & exception handlers
│   ├── database.py                 # SQLAlchemy database session & connection diagnostic engine
│   ├── schemas.py                  # Pydantic schemas for evidence bundles, attributions, explanations
│   ├── attribution.py              # Multi-factor source attribution & explanation generator
│   ├── command_center/             # Module 1: Geo overview, station status, weather/wind
│   ├── hotspot_lifecycle/          # Module 2: Hotspot watcher, thresholds, anomaly triggers
│   ├── investigations/             # Module 3: Investigation orchestrator & evidence collectors
│   ├── pollution_fingerprint/      # Module 4: Multi-source evidence graph & fingerprints
│   ├── intelligence_contract/      # Module 5 & 6: Baseline forecaster, scenario simulator, recommendations
│   ├── operations_contract/        # Module 7: Department mapping, tasks, escalation engine
│   ├── citizen_advisory/           # Module 8: Health guidance templates & multilingual engine
│   ├── geo_master/                 # Spatial models, PostGIS repositories, distance helpers
│   ├── environmental_data/         # Ingestion adapters, normalization DTOs, seed pipelines
│   ├── sensor_health/              # Station heartbeat ping & sensor drift diagnostic service
│   └── uncertainty/                # Next best evidence request & uncertainty quantification
├── data/                           # Mock evidence JSON & environmental seed fixtures
├── database/migrations/            # PostGIS SQL migrations (001_geo_master.sql, 002_environmental_data.sql)
├── scripts/                        # Database check & geo/environmental seeding scripts
└── tests/                          # 24 unit & integration test files
```

---

### Module 1: AI Command Center
* **Purpose:** Single-screen situational awareness displaying live city AQI, correlated weather, wind, sensor health, and active problem wards.
* **Backend Processing:** Scheduled ingestion job pulls sensor, weather, and wind data. IDW interpolation calculates continuous grid values across ward polygons.
* **APIs Required:** `GET /api/v1/command-center/overview`, `GET /api/v1/stations`, `GET /api/v1/heatmap`.
* **Database Tables:** `stations`, `station_readings`, `wards`, `weather_readings`, `wind_readings`.

### Module 2: Hotspot Detection Engine
* **Purpose:** Automated detection of abnormal pollution spikes without requiring constant manual monitoring.
* **Backend Processing:** Watcher service compares incoming AQI against statutory CPCB bands and rolling 7-day ward baselines. Triggers `hotspot.created` events.
* **APIs Required:** `GET /api/v1/hotspots?status=active`, `POST /api/v1/hotspots`, `PATCH /api/v1/hotspots/{id}/status`.
* **Database Tables:** `hotspots`, `hotspot_history`, `thresholds_config`.

### Module 3: AI Multi-Source Investigation
* **Purpose:** Automated evidence gathering across satellite, traffic, permit, land-use, and industrial registries upon hotspot creation.
* **Backend Processing:** Investigation Orchestrator fans out parallel checks. Satellite service evaluates aerosol haze; Spatial queries check construction permits within 500m and industrial consent registries.
* **APIs Required:** `POST /api/v1/investigations`, `GET /api/v1/investigations/{hotspot_id}`.
* **Database Tables:** `investigations`, `evidence_items`, `construction_permits`, `industrial_units`, `traffic_readings`.

### Module 4: Evidence Collection & Source Attribution
* **Purpose:** Translate raw evidence bundles into an explainable source verdict with confidence scores.
* **Backend Processing:** Weighted scoring engine applies directional wind-bearing multipliers to determine primary and secondary sources. Generates plain-language explanation checklists.
* **APIs Required:** `POST /api/v1/attributions`, `POST /api/v1/explanations`.
* **Database Tables:** `pollution_sources`, `source_evidence_weights`, `attributions`, `attribution_evidence`.

### Module 5: Prediction Engine & Scenario Simulator
* **Purpose:** Display two futures side-by-side: Scenario A (No Action) vs. Scenario B (With AI Recommendations applied).
* **Backend Processing:** Time-series forecaster computes baseline 24h trajectory. What-if simulator applies intervention effect coefficients to project AQI reduction and hours saved.
* **APIs Required:** `GET /api/v1/predictions/{hotspot_id}?scenario=no_action`, `POST /api/v1/predictions/{hotspot_id}/simulate`.
* **Database Tables:** `forecasts`, `forecast_points`, `intervention_effect_coefficients`.

### Module 6: AI Actionable Interventions
* **Purpose:** Provide a prioritized menu of interventions mapped directly to attributed pollution sources.
* **Backend Processing:** Maps primary source to candidate actions, calculates expected AQI drop, assigns effort level (Low/Med/High), and orders by ROI.
* **APIs Required:** `GET /api/v1/recommendations/{hotspot_id}`, `POST /api/v1/recommendations/{hotspot_id}/select`.
* **Database Tables:** `action_catalog`, `recommendations`, `recommendation_selection`.

### Module 7: Department Assignment & Accountability
* **Purpose:** Turn selected recommendations into tracked department tasks with SLA deadlines and escalation logic.
* **Backend Processing:** Routes action types to responsible municipal departments. Monitors recurrence counters per ward and escalates unacknowledged alerts.
* **APIs Required:** `POST /api/v1/tasks`, `PATCH /api/v1/tasks/{id}/status`, `GET /api/v1/hotspots/{id}/accountability`.
* **Database Tables:** `departments`, `department_action_mapping`, `tasks`, `task_status_history`, `escalations`.

### Module 8: Citizen Health Risk Advisory
* **Purpose:** Deliver ward-level health protection advisories in regional languages.
* **Backend Processing:** Templates mapped to CPCB AQI bands are customized per audience group (General, Schools, Elderly) and translated into target languages.
* **APIs Required:** `GET /api/v1/advisory/{ward_id}?lang=hi`, `GET /api/v1/advisory/{ward_id}/all-languages`.
* **Database Tables:** `advisory_templates`, `advisory_translations`, `ward_advisories`.

---

# 3. Database Schema & Geo Master Spatial Operations

### Consolidated Database ER Overview

```text
wards ──< stations ──< station_readings
wards ──< hotspots ──< hotspot_history
hotspots ──1:1── investigations ──< evidence_items
hotspots ──< attributions ──< attribution_evidence
hotspots ──< recommendations ──< recommendation_selection
hotspots ──< tasks ──< task_status_history
hotspots ──< forecasts ──< forecast_points
wards ──< ward_advisories
departments ──< department_action_mapping ──< action_catalog
action_catalog ──< source_evidence_weights ── pollution_sources
```

### Key Spatial Queries (`backend/app/geo_master`)

* **Ward Containment Query:**
  ```python
  GeoMasterService.find_ward_containing_point(point) # Uses PostGIS ST_Contains
  ```
* **Radius Entity Proximity:**
  ```python
  GeoMasterService.find_entities_within_radius(entity_type, point, radius_meters) # Uses PostGIS ST_DWithin
  ```
* **Distance Computation:**
  ```python
  GeoMasterService.calculate_distance_meters(origin, destination) # Uses ST_DistanceSphere (or Haversine fallback)
  ```

---

# 4. API Endpoint Contracts & Data Specifications

### Source Attribution Request (`POST /api/v1/attributions`)

```json
{
  "hotspot_id": "HS-BLR-2025-001",
  "ward_id": "WARD-192",
  "traffic": { "density_index": 0.85, "congestion_level": "heavy" },
  "construction": { "active_permits_within_500m": 3, "dust_complaints": 12 },
  "industry": { "nearby_units_count": 1, "stack_emission_flag": false },
  "satellite": { "aerosol_optical_depth": 0.62, "dust_signature_detected": true },
  "wind_direction": 225.0,
  "wind_speed": 12.5,
  "pm25": 185.0
}
```

### Source Attribution Response

```json
{
  "hotspot_id": "HS-BLR-2025-001",
  "primary_source": "Construction Dust",
  "confidence": 78.5,
  "secondary_sources": [
    { "source": "Vehicular Emission", "score": 14.2 },
    { "source": "Industrial Emission", "score": 7.3 }
  ],
  "rankings": [
    { "source": "Construction Dust", "score": 78.5 },
    { "source": "Vehicular Emission", "score": 14.2 },
    { "source": "Industrial Emission", "score": 7.3 },
    { "source": "Road Dust", "score": 0.0 },
    { "source": "Biomass Burning", "score": 0.0 }
  ]
}
```

### Explanation Generator Response (`POST /api/v1/explanations`)

```json
{
  "hotspot_id": "HS-BLR-2025-001",
  "primary_source": "Construction Dust",
  "confidence": 78.5,
  "headline": "Construction Dust identified as primary pollution source (78.5% confidence)",
  "summary": "High PM2.5 levels in WARD-192 are strongly correlated with 3 active construction permits within 500m and satellite dust signatures.",
  "evidence": [
    "3 active construction permits found within 500m radius",
    "Satellite remote sensing confirmed high aerosol optical depth (0.62)",
    "Favorable wind direction (225°) blowing from construction zone to station"
  ]
}
```

---

# 5. How to Run & Verification Guide

### Option 1: Quick Start (Frontend Only with Seeded Fallbacks)
No database or Python environment setup required:
```powershell
npm install
npm run dev
```
Open **[http://localhost:5173](http://localhost:5173)** in your browser.

---

### Option 2: Full Stack Setup (FastAPI Backend + React Frontend)

#### Step 1: Start FastAPI Backend
```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```
* **Interactive API Documentation (Swagger):** `http://localhost:8000/docs`
* **Health Check:** `http://localhost:8000/health`

#### Step 2: (Optional) Database Setup & Seeding
Create a `.env` file in `backend/.env`:
```env
DATABASE_URL=postgresql+psycopg://postgres:YOUR_PASSWORD@127.0.0.1:5432/aerointel
```
Apply migrations and seed data:
```powershell
psql $env:DATABASE_URL -f database/migrations/001_geo_master.sql
psql $env:DATABASE_URL -f database/migrations/002_environmental_data.sql
python -m scripts.seed_geo_master
python -m scripts.seed_environmental_data
```

#### Step 3: Start React Frontend
In a separate terminal window:
```powershell
npm run dev
```

---

### Verification & Automated Testing

* **Run Backend Python Test Suite (24 Test Files):**
  ```powershell
  cd backend
  pytest
  ```

* **Run Frontend TypeScript Type-Check:**
  ```powershell
  npx tsc --noEmit
  ```

---


