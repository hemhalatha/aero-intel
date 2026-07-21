from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def evidence_payload() -> dict:
    return {
        "hotspot_id": 101,
        "traffic": {"detected": True, "confidence": 0.82},
        "construction": {"detected": True, "confidence": 0.91},
        "industry": {"detected": False, "confidence": 0.20},
        "satellite": {"detected": True, "confidence": 0.74},
        "road_dust": {"detected": True, "confidence": 0.62},
        "wind_direction": "North",
        "wind_speed": 18,
        "historical_patterns": {"construction_match": 0.88, "traffic_match": 0.63, "road_dust_match": 0.58},
    }


def test_returns_ranked_attribution() -> None:
    response = client.post("/api/v1/attributions", json=evidence_payload())

    assert response.status_code == 201
    body = response.json()
    assert body["primary_source"] == "Construction Dust"
    assert body["confidence"] > body["secondary_sources"][0]["score"]
    assert round(sum(item["score"] for item in body["rankings"]), 1) == 100.0


def test_rejects_invalid_confidence() -> None:
    payload = evidence_payload()
    payload["traffic"]["confidence"] = 1.2
    response = client.post("/api/v1/attributions", json=payload)

    assert response.status_code == 422


def test_generates_explainable_output() -> None:
    response = client.post("/api/v1/explanations", json=evidence_payload())

    assert response.status_code == 201
    body = response.json()
    assert body["primary_source"] == "Construction Dust"
    assert "most likely pollution source" in body["headline"]
    assert len(body["evidence"]) >= 2
