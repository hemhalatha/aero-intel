# AeroIntel — Implementation Plan

## AI-Powered Urban Pollution Decision Intelligence Platform

AeroIntel is a closed-loop urban air-quality intelligence platform that goes beyond AQI monitoring.

It detects pollution hotspots, investigates possible causes using multi-source evidence, builds explainable source-attribution reasoning, identifies missing evidence, simulates intervention strategies, assigns actions to responsible departments, verifies whether those interventions worked, and continuously improves future decisions.

The core product loop is:

```text
Monitor
→ Detect
→ Investigate
→ Build Evidence Graph
→ Identify Pollution Fingerprint
→ Measure Uncertainty
→ Request Next Best Evidence
→ Attribute Source
→ Forecast No-Action Future
→ Simulate Intervention Strategies
→ Recommend Best Action
→ Assign Department
→ Track Execution
→ Verify Outcome
→ Learn From Result
```

---

# 1. Product Objective

Most urban air-quality systems answer:

> What is the AQI?

AeroIntel must answer:

1. Where is pollution increasing?
2. Why is it happening?
3. What evidence supports that conclusion?
4. How confident is the system?
5. What evidence is still missing?
6. What happens if no action is taken?
7. Which intervention is expected to work best?
8. Who is responsible for executing it?
9. Did the intervention actually work?
10. What should the system learn from the result?

The final prototype should demonstrate this entire loop for at least three realistic urban pollution scenarios.

---

# 2. Recommended Technology Stack

## Frontend

- React
- Vite
- Tailwind CSS
- Leaflet or Mapbox GL
- Recharts or Chart.js
- React Query
- Zustand or Context API
- i18next for multilingual citizen advisories

## Backend

- Python
- FastAPI
- SQLAlchemy
- Pydantic
- APScheduler
- Redis
- WebSockets or Server-Sent Events

## Database

- PostgreSQL
- PostGIS

## AI and Analytics

- scikit-learn
- statsmodels
- NumPy
- pandas
- OpenCV
- NetworkX for evidence graph representation

## Optional

- XGBoost for later attribution refinement
- Bhashini for multilingual translation
- OpenAQ/CPCB for AQI data
- Weather API for weather and wind
- Sentinel-5P/Sentinel-2 sample imagery

---

# 3. High-Level Architecture

```text
┌──────────────────────────────────────────────┐
│              EXTERNAL DATA SOURCES           │
│ AQI | Weather | Wind | Traffic | Satellite   │
│ Construction | Industrial | Land Use         │
└──────────────────────┬───────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────┐
│            DATA INGESTION LAYER              │
│ Adapters → Validation → Normalization         │
└──────────────────────┬───────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────┐
│          POSTGRESQL + POSTGIS + REDIS         │
└──────────────────────┬───────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────┐
│        MONITORING AND DETECTION LAYER        │
│ Heatmap | Sensor Health | Hotspot Detection   │
└──────────────────────┬───────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────┐
│        INVESTIGATION INTELLIGENCE LAYER      │
│ Evidence Collectors                           │
│ Pollution Fingerprint                         │
│ Evidence Graph                                │
│ Uncertainty Engine                            │
│ Next Best Evidence Engine                     │
└──────────────────────┬───────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────┐
│          DECISION INTELLIGENCE LAYER         │
│ Source Attribution                            │
│ Baseline Forecast                             │
│ Counterfactual Simulation                     │
│ Recommendation Optimization                   │
└──────────────────────┬───────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────┐
│             ACTION LAYER                     │
│ Department Assignment                         │
│ Task Tracking                                 │
│ Escalation                                    │
└──────────────────────┬───────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────┐
│         VERIFICATION AND LEARNING LOOP       │
│ Prediction vs Actual                          │
│ Intervention Effectiveness                    │
│ Attribution Re-evaluation                     │
│ Coefficient Learning                          │
└──────────────────────┬───────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────┐
│           COMMAND CENTER FRONTEND            │
└──────────────────────────────────────────────┘
```

---

# 4. Core Shared Data Contracts

All modules should communicate using common schemas.

## Hotspot Context

```json
{
  "hotspot_id": "HS1001",
  "ward_id": "W21",
  "station_id": "ST101",
  "latitude": 13.0102,
  "longitude": 80.2157,
  "detected_at": "2026-07-20T10:00:00+05:30",
  "aqi": 328,
  "severity": "VERY_POOR"
}
```

## Standard Evidence Object

```json
{
  "evidence_id": "EV1001",
  "investigation_id": "INV1001",
  "source_type": "TRAFFIC",
  "evidence_type": "TRAFFIC_ANOMALY",
  "detected": true,
  "confidence": 0.84,
  "support_direction": "SUPPORTS",
  "raw_detail": {
    "current_density": 92,
    "baseline_density": 55,
    "deviation_percent": 67
  },
  "checked_at": "2026-07-20T10:03:00+05:30"
}
```

## Attribution Result

```json
{
  "hotspot_id": "HS1001",
  "primary_source": {
    "source": "CONSTRUCTION_DUST",
    "confidence": 0.82
  },
  "secondary_sources": [
    {
      "source": "VEHICULAR_EMISSION",
      "confidence": 0.31
    }
  ],
  "uncertainty_level": "LOW"
}
```

## Intervention Candidate

```json
{
  "action_id": "ACT1001",
  "name": "Deploy water sprinklers",
  "expected_aqi_reduction": 28,
  "effort": "MEDIUM",
  "cost_level": "LOW",
  "department": "Municipal Corporation",
  "confidence": 0.76
}
```

---

# 5. Module 1 — Environmental Data Ingestion

## Purpose

Collect AQI, weather, wind and other environmental data through provider-independent adapters.

## Data Sources

- AQI provider
- Weather provider
- Wind provider
- Seeded demo provider

## Key Design

Every provider must return the same normalized internal DTO.

The rest of the application must never depend directly on OpenAQ, CPCB or any specific provider.

## Folder Structure

```text
backend/app/modules/data_ingestion/
├── adapters/
│   ├── base.py
│   ├── air_quality.py
│   ├── weather.py
│   └── seeded.py
├── normalizer.py
├── service.py
├── schemas.py
└── routes.py
```

## Main APIs

```http
POST /api/v1/ingestion/run
GET  /api/v1/ingestion/status
```

## Tables

```text
ingestion_batches
ingestion_errors
```

---

# 6. Module 2 — Environmental Repository

## Purpose

Store and expose normalized environmental time-series data.

## Tables

```text
stations
station_readings
weather_readings
wind_readings
latest_station_state
```

## Main APIs

```http
GET /api/v1/stations
GET /api/v1/stations/{station_id}/readings
GET /api/v1/wards/{ward_id}/readings
GET /api/v1/weather/current
GET /api/v1/weather/forecast
GET /api/v1/wind/current
```

## Important Service Methods

```python
get_latest_station_readings()
get_ward_aqi_history()
get_current_weather()
get_weather_forecast()
get_current_wind()
```

---

# 7. Module 3 — Monitoring and Command Center

## Responsibilities

- AQI classification
- Sensor health
- Heatmap generation
- City KPI aggregation

## Main Output

The Command Center should show:

- city-wide AQI heatmap
- monitoring station status
- weather
- wind
- active hotspots
- worst affected wards

## Heatmap

Use Inverse Distance Weighting for the hackathon prototype.

## APIs

```http
GET /api/v1/command-center/overview
GET /api/v1/heatmap
GET /api/v1/stations/health
```

---

# 8. Module 4 — Hotspot Detection

## Purpose

Automatically identify pollution incidents.

## Detection Logic

### Absolute Threshold

Trigger when AQI crosses configured severity thresholds.

### Historical Anomaly

Compare current AQI with the ward's historical baseline.

### Deduplication

Do not create multiple active hotspots for the same ward and incident period.

## Tables

```text
hotspots
hotspot_history
hotspot_status_history
```

## Events

```text
hotspot.created
hotspot.escalated
hotspot.resolved
```

## APIs

```http
GET   /api/v1/hotspots
GET   /api/v1/hotspots/{hotspot_id}
PATCH /api/v1/hotspots/{hotspot_id}/status
```

---

# 9. Module 5 — Investigation Orchestrator

## Purpose

Launch multiple independent evidence collectors for every hotspot.

## Flow

```text
hotspot.created
      ↓
Create investigation
      ↓
Run collectors
      ↓
Store individual evidence
      ↓
Build evidence graph
      ↓
Generate pollution fingerprint
      ↓
Measure uncertainty
      ↓
Request next best evidence if required
      ↓
Complete investigation
```

## Investigation Status

```text
PENDING
IN_PROGRESS
WAITING_FOR_EVIDENCE
PARTIALLY_COMPLETE
COMPLETE
FAILED
```

## Tables

```text
investigations
investigation_steps
```

## API

```http
POST /api/v1/investigations
GET  /api/v1/investigations/{hotspot_id}
GET  /api/v1/investigations/{hotspot_id}/status
```

---

# 10. Module 6 — Evidence Collectors

All collectors must implement the same interface.

```python
class EvidenceCollector:
    async def collect(self, hotspot_context) -> EvidenceResult:
        ...
```

## Required Collectors

### Traffic Collector

Checks:

- nearby road segments
- current traffic density
- historical baseline
- rush-hour correlation

### Construction Collector

Checks:

- active permits
- distance
- land-use category
- concentration of construction activity

### Industrial Collector

Checks:

- nearby industrial units
- pollution category
- compliance status
- wind direction alignment

### Satellite Collector

Checks:

- aerosol or dust signature
- thermal anomaly where applicable
- pre-downloaded imagery for demo reliability

### Biomass/Waste Burning Collector

Checks:

- reported fire points
- historical burning zones
- thermal anomalies
- wind alignment

## Standard Output

Every collector must return the standard evidence schema.

---

# 11. Module 7 — Pollution Fingerprint Engine

## Purpose

Create a feature profile for every hotspot.

## Example Fingerprints

### Vehicular Emissions

```text
High NO2
High CO
Rush-hour correlation
Major road proximity
Traffic anomaly
```

### Construction Dust

```text
High PM10
High PM10/PM2.5 ratio
Construction permit nearby
Dust signature
Wind alignment
```

### Industrial Emissions

```text
SO2 or NO2 anomaly
Industrial source nearby
Wind aligned
Persistent non-rush-hour pollution
```

## Output

```json
{
  "hotspot_id": "HS1001",
  "features": {
    "pm10_pm25_ratio": 2.4,
    "traffic_anomaly": 0.82,
    "construction_proximity": 0.91,
    "industrial_wind_alignment": 0.22
  },
  "pattern_matches": {
    "CONSTRUCTION_DUST": 0.84,
    "ROAD_DUST": 0.51,
    "VEHICULAR_EMISSION": 0.22
  }
}
```

## Tables

```text
pollution_fingerprints
fingerprint_features
```

---

# 12. Module 8 — Causal Evidence Graph

## Purpose

Convert disconnected evidence into an explainable reasoning structure.

## Node Types

```text
HOTSPOT
EVIDENCE
POLLUTION_SOURCE
WEATHER_CONDITION
GEOGRAPHIC_ENTITY
INTERVENTION
```

## Edge Types

```text
SUPPORTS
CONTRADICTS
NEAR
UPWIND_OF
ACTIVE_DURING
CORRELATED_WITH
OBSERVED_AT
```

## Example

```text
Construction Permit
      │ SUPPORTS
      ▼
Construction Dust
      ▲
      │ SUPPORTS
Satellite Dust Signature

Wind Direction
      │ UPWIND_OF
      ▼
Hotspot
```

## Implementation

Use NetworkX internally.

Persist the graph as nodes and edges for reproducibility.

## Tables

```text
evidence_graph_nodes
evidence_graph_edges
```

## APIs

```http
GET /api/v1/investigations/{investigation_id}/evidence-graph
```

---

# 13. Module 9 — Source Attribution Engine

## Purpose

Rank possible pollution sources using:

- evidence confidence
- pollution fingerprint
- spatial relationship
- wind alignment
- temporal correlation
- supporting evidence
- contradictory evidence

## Suggested Scoring

```text
source_score =
    weighted_support
    + fingerprint_match
    + spatial_alignment
    + temporal_alignment
    - contradiction_penalty
```

Normalize scores to probabilities or confidence values.

## Sources

```text
CONSTRUCTION_DUST
VEHICULAR_EMISSION
INDUSTRIAL_EMISSION
ROAD_DUST
BIOMASS_BURNING
WEATHER_TRAPPING
UNKNOWN
```

## Tables

```text
pollution_sources
source_evidence_weights
attributions
attribution_evidence
```

## APIs

```http
POST /api/v1/attributions/{investigation_id}/run
GET  /api/v1/attributions/{hotspot_id}
```

---

# 14. Module 10 — Uncertainty Engine

## Purpose

Determine whether the system has enough evidence to make a confident conclusion.

## Example Logic

```text
Primary = 48%
Secondary = 43%

Difference = 5%

Result:
High uncertainty
```

## Suggested Inputs

- difference between top source scores
- total supporting evidence count
- evidence quality
- missing evidence sources
- conflicting evidence

## Output

```json
{
  "uncertainty_level": "HIGH",
  "confidence_gap": 0.05,
  "missing_evidence": [
    "PM10_PM25_RATIO",
    "LATEST_SATELLITE_DUST_CHECK"
  ]
}
```

## Levels

```text
LOW
MEDIUM
HIGH
```

---

# 15. Module 11 — Next Best Evidence Engine

## Purpose

Identify the single additional evidence check that would most reduce uncertainty.

## Example

```text
Traffic: 48%
Construction: 43%

Missing discriminating evidence:
PM10/PM2.5 ratio

Recommendation:
Run pollutant fingerprint analysis.
```

## Implementation Strategy

For the prototype, use a rule-based decision table.

Example:

```python
if top_sources == {"TRAFFIC", "CONSTRUCTION"}:
    request("PM10_PM25_RATIO")

if top_sources == {"INDUSTRIAL", "TRAFFIC"}:
    request("WIND_SOURCE_ALIGNMENT")

if biomass_score > 0.3 and satellite_fire_missing:
    request("THERMAL_ANOMALY_CHECK")
```

## Tables

```text
evidence_request_rules
next_evidence_requests
```

## APIs

```http
GET  /api/v1/investigations/{investigation_id}/next-best-evidence
POST /api/v1/investigations/{investigation_id}/evidence-request
```

---

# 16. Module 12 — Explainable Diagnosis Generator

## Purpose

Convert technical evidence into a traceable human-readable explanation.

## Example

```text
Primary suspected source: Construction Dust
Confidence: 87%

Supporting evidence:
✓ PM10 concentration is significantly higher than PM2.5.
✓ An active construction permit exists 280 metres away.
✓ Wind direction carries dust toward the hotspot.
✓ Satellite imagery shows a dust signature over the area.

Contradictory evidence:
• Traffic is elevated but below the threshold normally associated with major traffic-driven pollution.
```

The explanation generator must never invent evidence.

Use templates grounded only in stored evidence.

---

# 17. Module 13 — Baseline AQI Forecasting

## Purpose

Predict what happens if no action is taken.

## Inputs

- recent AQI history
- current AQI
- weather forecast
- wind forecast
- time of day

## Hackathon Model

Use:

- moving average
- exponential smoothing
- weather adjustment

## Output

Hourly AQI trajectory for the next 24 hours.

## APIs

```http
POST /api/v1/forecasts/{hotspot_id}/baseline
GET  /api/v1/forecasts/{hotspot_id}/baseline
```

## Tables

```text
forecasts
forecast_points
forecast_model_versions
```

---

# 18. Module 14 — Intervention Catalog

## Purpose

Maintain all supported pollution-control actions.

## Example Actions

```text
Deploy water sprinklers
Inspect construction site
Enforce dust barriers
Divert heavy vehicles
Restrict traffic temporarily
Inspect industrial stack emissions
Stop open waste burning
Conduct mechanized road sweeping
```

## Metadata

Each action should store:

- applicable pollution source
- expected reduction
- effect duration
- implementation effort
- cost level
- responsible department

## Tables

```text
action_catalog
action_source_mapping
action_effect_coefficients
```

---

# 19. Module 15 — Recommendation Engine

## Purpose

Rank actions according to:

- attribution confidence
- expected AQI impact
- implementation effort
- cost
- urgency
- hotspot severity

## Output

```json
[
  {
    "action": "Deploy water sprinklers",
    "expected_aqi_reduction": 28,
    "priority": "HIGH",
    "effort": "MEDIUM"
  }
]
```

## APIs

```http
POST /api/v1/recommendations/{hotspot_id}/generate
GET  /api/v1/recommendations/{hotspot_id}
```

---

# 20. Module 16 — Counterfactual Intervention Simulator

## Purpose

Create multiple possible futures.

## Required Scenarios

```text
Scenario A — Do Nothing
Scenario B — Intervention 1
Scenario C — Intervention 2
Scenario D — Combined Intervention
```

## Example

```text
Current AQI: 327

Do Nothing
6h AQI → 364

Water Sprinkling
6h AQI → 291

Water Sprinkling + Enforcement
6h AQI → 248

Traffic Diversion
6h AQI → 311
```

## Implementation

Use:

```text
baseline forecast
minus
time-varying intervention effect
```

Apply caps to prevent unrealistic reductions.

## Tables

```text
simulation_runs
simulation_scenarios
simulation_points
simulation_actions
```

## APIs

```http
POST /api/v1/simulations/{hotspot_id}
GET  /api/v1/simulations/{hotspot_id}
```

---

# 21. Module 17 — Best Intervention Optimizer

## Purpose

Choose the best action combination.

## Ranking Formula

```text
utility =
    expected_aqi_improvement
    × attribution_confidence
    - effort_penalty
    - cost_penalty
    - delay_penalty
```

## Output

```json
{
  "recommended_plan": [
    "DEPLOY_WATER_SPRINKLERS",
    "INSPECT_CONSTRUCTION_SITE"
  ],
  "expected_aqi_reduction": 76,
  "effort": "MEDIUM",
  "departments_required": 2,
  "confidence": 0.78
}
```

---

# 22. Module 18 — Department Assignment

## Purpose

Convert selected interventions into tracked operational tasks.

## Tables

```text
departments
department_action_mapping
tasks
task_status_history
```

## Workflow

```text
ASSIGNED
→ ACKNOWLEDGED
→ IN_PROGRESS
→ RESOLVED
```

## APIs

```http
POST  /api/v1/tasks
GET   /api/v1/tasks
PATCH /api/v1/tasks/{task_id}/status
```

---

# 23. Module 19 — Accountability and Escalation

## Purpose

Track whether departments respond.

## Detect

- overdue tasks
- repeated hotspots
- ignored recommendations
- recurring source locations

## Escalation Example

```text
Same hotspot repeated 3 times in 30 days
+
Previous task unresolved

→ Critical Escalation
```

## Tables

```text
escalations
escalation_history
```

---

# 24. Module 20 — Intervention Verification

## Purpose

Measure whether the recommended action actually worked.

This is a core differentiating feature.

## Flow

```text
Action selected
      ↓
Predicted post-action AQI generated
      ↓
Department executes action
      ↓
Actual AQI observed
      ↓
Prediction compared with reality
      ↓
Effectiveness calculated
```

## Metrics

```text
Predicted improvement
Actual improvement
Prediction error
Effectiveness score
Time to recovery
```

## Example

```json
{
  "predicted_aqi_after_3h": 245,
  "actual_aqi_after_3h": 252,
  "prediction_error": 7,
  "effectiveness_score": 0.91,
  "status": "HIGHLY_EFFECTIVE"
}
```

## Tables

```text
intervention_executions
intervention_observations
intervention_verifications
```

## APIs

```http
POST /api/v1/interventions/{task_id}/verify
GET  /api/v1/interventions/{task_id}/verification
```

---

# 25. Module 21 — Learning Loop

## Purpose

Improve future intervention estimates using verified outcomes.

## Initial Approach

Use controlled coefficient updating rather than full online ML.

Example:

```text
Previous water sprinkling coefficient:
15%

Observed average reduction:
12%

Updated coefficient:
14.4%
```

Use a conservative learning rate.

## Suggested Formula

```text
new_coefficient =
    old_coefficient × (1 - learning_rate)
    +
    observed_effect × learning_rate
```

## Important Rules

- keep original default coefficient
- keep version history
- do not update from one low-quality observation
- require minimum confidence
- update separately by source and optionally by ward

## Tables

```text
intervention_effect_versions
learning_events
```

---

# 26. Module 22 — Citizen Advisory

## Purpose

Provide localized public health guidance based on current AQI.

## Features

- ward-level advisories
- multiple languages
- vulnerable-group guidance
- public read-only page

## Approach

Use approved templates.

Do not use uncontrolled free-form generation for health advice.

## Tables

```text
advisory_templates
advisory_translations
ward_advisories
```

---

# 27. Event-Driven Workflow

## Main Events

```text
reading.normalized
hotspot.created
investigation.started
evidence.collected
investigation.completed
attribution.completed
uncertainty.detected
next_evidence.requested
recommendations.generated
actions.selected
simulation.completed
task.created
task.resolved
intervention.verification_ready
intervention.verified
learning.updated
aqi_band.changed
```

## End-to-End Flow

```text
1. Environmental readings arrive.

2. Data is normalized and stored.

3. Hotspot detector evaluates the reading.

4. hotspot.created is emitted.

5. Baseline forecast starts immediately.

6. Investigation orchestrator launches evidence collectors.

7. Evidence items are stored.

8. Pollution fingerprint is generated.

9. Evidence graph is built.

10. Attribution engine ranks sources.

11. Uncertainty engine evaluates confidence.

12. If uncertainty is high, Next Best Evidence is requested.

13. Attribution is recalculated.

14. Explanation is generated.

15. Recommendation engine creates actions.

16. Simulator generates multiple counterfactual futures.

17. Best intervention optimizer ranks the plans.

18. Administrator selects a plan.

19. Tasks are assigned to departments.

20. Departments execute actions.

21. Actual AQI is monitored.

22. Verification engine compares predicted and actual results.

23. Learning loop updates intervention-effect estimates.

24. Future simulations use improved coefficients.
```

---

# 28. Database Overview

```text
cities
wards
stations
station_readings
weather_readings
wind_readings

hotspots
hotspot_history
hotspot_status_history

investigations
investigation_steps

evidence_items
evidence_attachments

pollution_fingerprints
fingerprint_features

evidence_graph_nodes
evidence_graph_edges

pollution_sources
source_evidence_weights
attributions
attribution_evidence

next_evidence_requests
evidence_request_rules

forecasts
forecast_points

action_catalog
action_source_mapping
action_effect_coefficients

recommendations
recommendation_selections

simulation_runs
simulation_scenarios
simulation_points

departments
department_action_mapping
tasks
task_status_history

intervention_executions
intervention_observations
intervention_verifications

intervention_effect_versions
learning_events

escalations
escalation_history

advisory_templates
advisory_translations
ward_advisories
```

---

# 29. Recommended Backend Folder Structure

```text
backend/
└── app/
    ├── main.py
    ├── core/
    │   ├── config.py
    │   ├── database.py
    │   ├── events.py
    │   ├── scheduler.py
    │   └── exceptions.py
    │
    ├── modules/
    │   ├── geo_master/
    │   ├── data_ingestion/
    │   ├── environmental_repository/
    │   ├── monitoring/
    │   ├── hotspot_detection/
    │   ├── investigation/
    │   │   ├── orchestrator.py
    │   │   └── collectors/
    │   │       ├── traffic.py
    │   │       ├── construction.py
    │   │       ├── industrial.py
    │   │       ├── satellite.py
    │   │       └── biomass.py
    │   ├── fingerprint/
    │   ├── evidence_graph/
    │   ├── attribution/
    │   ├── uncertainty/
    │   ├── next_best_evidence/
    │   ├── explanation/
    │   ├── forecasting/
    │   ├── interventions/
    │   ├── recommendations/
    │   ├── simulation/
    │   ├── optimization/
    │   ├── departments/
    │   ├── tasks/
    │   ├── accountability/
    │   ├── verification/
    │   ├── learning_loop/
    │   └── citizen_advisory/
    │
    └── shared/
        ├── schemas/
        ├── enums/
        ├── geo/
        └── utilities/
```

---

# 30. Recommended Frontend Pages

```text
Command Center
Hotspot Investigation
Evidence Graph
Pollution Fingerprint
Diagnosis and Uncertainty
Next Best Evidence
Scenario Simulator
Recommended Action Plan
Department Task Tracker
Intervention Verification
Learning History
Citizen Advisory
```

---

# 31. Hero Demo Scenario

## Step 1 — Hotspot

```text
Ward 21
AQI increased from 178 to 327
```

## Step 2 — Investigation

```text
Traffic anomaly              ✓
Construction activity        ✓
Satellite dust signature     ✓
Industrial source            ✗
Wind alignment               ✓
```

## Step 3 — Initial Attribution

```text
Construction Dust     48%
Vehicular Emission    43%
Industrial             9%

Uncertainty: HIGH
```

## Step 4 — Next Best Evidence

```text
Recommended check:
PM10 / PM2.5 pollution fingerprint
```

## Step 5 — Final Attribution

```text
Construction Dust
Confidence: 87%
```

## Step 6 — Scenario Simulation

```text
Do Nothing
6h AQI → 364

Water Sprinkling
6h AQI → 291

Water Sprinkling + Site Enforcement
6h AQI → 248
```

## Step 7 — Recommended Plan

```text
Deploy sprinklers
+
Immediate construction inspection
```

## Step 8 — Department Assignment

```text
Municipal Corporation
+
Construction Enforcement Department
```

## Step 9 — Verification

```text
Predicted AQI after 3h: 273
Actual AQI after 3h: 279

Effectiveness: 91%
```

## Step 10 — Learning

```text
Construction intervention coefficient updated.
Future simulations become better calibrated.
```

---

# 32. Minimum Viable Finals-Level Build

The prototype should prioritize the following features.

## Must Have

- live or seeded AQI Command Center
- automatic hotspot detection
- multi-source investigation
- standardized evidence collection
- pollution fingerprint
- causal evidence graph
- source attribution
- uncertainty detection
- next best evidence
- no-action forecast
- multi-scenario intervention simulation
- department assignment
- intervention verification
- learning loop

## Can Be Simulated

- real-time traffic API
- live government permit integration
- live satellite API calls
- real SMS
- full online model retraining

## Can Be Future Work

- large-scale causal ML
- city-wide optimization across multiple hotspots
- real municipal ERP integration
- mobile citizen application

---

# 33. Implementation Order

## Phase 1 — Foundation

```text
Geo Master
Environmental Repository
Seed Data
AQI Classification
```

## Phase 2 — Monitoring

```text
Heatmap
Sensor Health
Command Center
Hotspot Detection
```

## Phase 3 — Investigation

```text
Investigation Orchestrator
Evidence Collectors
Evidence Repository
```

## Phase 4 — Intelligence

```text
Pollution Fingerprint
Evidence Graph
Source Attribution
Uncertainty Engine
Next Best Evidence
Explanation Generator
```

## Phase 5 — Decision Support

```text
Baseline Forecast
Intervention Catalog
Recommendation Engine
Scenario Simulation
Best Intervention Optimizer
```

## Phase 6 — Operations

```text
Department Mapping
Task Assignment
Task Tracking
Escalation
```

## Phase 7 — Closed Learning Loop

```text
Intervention Observation
Prediction vs Actual Verification
Effectiveness Scoring
Coefficient Update
Learning History
```

## Phase 8 — Presentation Layer

```text
Command Center
Investigation Timeline
Evidence Graph
Fingerprint UI
Scenario Simulator
Verification Screen
```

---

# 34. Testing Strategy

## Unit Tests

Test every module independently.

Examples:

```text
AQI classification boundary tests
Hotspot threshold detection
Hotspot deduplication
Traffic anomaly calculation
Construction proximity
Industrial wind alignment
Fingerprint calculation
Evidence graph generation
Attribution scoring
Uncertainty detection
Next best evidence rule selection
Scenario calculation
Verification score calculation
Coefficient update
```

## Integration Tests

```text
Hotspot → Investigation
Investigation → Attribution
Attribution → Recommendation
Recommendation → Simulation
Task Resolution → Verification
Verification → Learning
```

## End-to-End Tests

Create three deterministic demo scenarios:

```text
Scenario 1 — Construction-led hotspot
Scenario 2 — Traffic-led hotspot
Scenario 3 — Industrial-led hotspot
```

Every scenario should produce a predictable evidence pattern and final diagnosis.

---

# 35. Final Product Positioning

AeroIntel should not be presented as:

> An AQI monitoring dashboard.

It should be presented as:

> An urban pollution decision intelligence system that investigates pollution events, explains their probable causes, determines what evidence is still missing, simulates interventions before deployment, verifies whether the selected action worked, and continuously learns from real outcomes.

The most important differentiator is the closed feedback loop:

```text
Evidence
→ Decision
→ Action
→ Verification
→ Learning
```

That loop should remain visible throughout the architecture, implementation and final demo.
