"""
Project ASTRA - API & Microservice Test Suite
Phase-1 Review 1 (50% Implementation Milestone)
CHRIST (Deemed to be University), Department of CSE
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.services.risk_engine import risk_engine


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


def test_root_endpoint(client):
    """Verifies metadata information endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "online"
    assert "ASTRA" in data["acronym"]
    assert "Kasine RS" in data["team"]["backend_ml_lead"]
    assert "Darshan R" in data["team"]["android_client_lead"]


def test_health_endpoint(client):
    """Verifies health check and model loading status."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["model_loaded"] is True
    assert data["agent_4_trigger_pipeline"] == "enabled"


def test_scenario_1_daytime_commute(client):
    """
    Scenario 1: Normal daytime commute
    - Deviation: 10m
    - Dwell/Stop: 0s
    - Speed: 45 km/h
    - Hour: 14 (2:00 PM)
    Expected: Safe (0), Trigger: False
    """
    payload = {
        "user_id": "user_darshan_01",
        "latitude": 12.934533,
        "longitude": 77.606041,
        "deviation_meters": 10.0,
        "stop_duration_seconds": 0.0,
        "speed_kmh": 45.0,
        "hour_of_day": 14
    }
    response = client.post("/api/v1/telemetry/score", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["user_id"] == "user_darshan_01"
    assert data["risk_code"] == 0
    assert data["risk_level"] == "Safe"
    assert data["trigger_evidence_capture"] is False
    assert 0.0 <= data["confidence"] <= 1.0


def test_scenario_2_traffic_signal_pause(client):
    """
    Scenario 2: Traffic signal pause during evening commute
    - Deviation: 20m
    - Dwell/Stop: 90s
    - Speed: 0 km/h
    - Hour: 18 (6:00 PM)
    Expected: Safe (0), Trigger: False
    """
    payload = {
        "user_id": "user_darshan_02",
        "latitude": 12.935000,
        "longitude": 77.607000,
        "deviation_meters": 20.0,
        "stop_duration_seconds": 90.0,
        "speed_kmh": 0.0,
        "hour_of_day": 18
    }
    response = client.post("/api/v1/telemetry/score", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["risk_code"] == 0
    assert data["risk_level"] == "Safe"
    assert data["trigger_evidence_capture"] is False


def test_scenario_3_critical_off_route_halt(client):
    """
    Scenario 3: Severe midnight off-route deviation with prolonged halt
    - Deviation: 550m
    - Dwell/Stop: 400s
    - Speed: 0 km/h
    - Hour: 23 (11:30 PM)
    Expected: Critical (2), Trigger: True (Activates Agent 4)
    """
    payload = {
        "user_id": "user_darshan_03",
        "latitude": 12.910000,
        "longitude": 77.590000,
        "deviation_meters": 550.0,
        "stop_duration_seconds": 400.0,
        "speed_kmh": 0.0,
        "hour_of_day": 23
    }
    response = client.post("/api/v1/telemetry/score", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["risk_code"] == 2
    assert data["risk_level"] == "Critical"
    assert data["trigger_evidence_capture"] is True
    assert data["confidence"] >= 0.85


def test_telemetry_validation_error(client):
    """Verifies that invalid schema attributes trigger 422 Unprocessable Entity."""
    invalid_payload = {
        "user_id": "user_invalid",
        "latitude": 95.0,  # Invalid latitude (> 90)
        "longitude": 77.60,
        "deviation_meters": -5.0,  # Invalid negative deviation
        "stop_duration_seconds": 0.0,
        "speed_kmh": 30.0,
        "hour_of_day": 26  # Invalid hour (> 23)
    }
    response = client.post("/api/v1/telemetry/score", json=invalid_payload)
    assert response.status_code == 422
