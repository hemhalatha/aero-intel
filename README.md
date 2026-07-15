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
