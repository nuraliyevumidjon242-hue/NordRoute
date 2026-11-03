from __future__ import annotations

import json
from datetime import datetime
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

import app as scheduler
import services.auth as auth
import services.optimizer as optimizer
from services.routing import RoadMatrix


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(scheduler, "DB_PATH", tmp_path / "test.sqlite")
    scheduler.initialize()
    with TestClient(scheduler.app) as test_client:
        yield test_client


HEADERS = {"X-API-Key": "local-demo-key-change-me"}


def test_health_and_api_authentication(client):
    assert client.get("/health").json()["status"] == "ok"
    response = client.get("/api/v1/dashboard")
    assert response.status_code == 401
    assert response.headers["content-type"].startswith("application/problem+json")


def test_dashboard_has_seed_data_and_serves_ui(client):
    dashboard = client.get("/api/v1/dashboard", headers=HEADERS)
    assert dashboard.status_code == 200
    payload = dashboard.json()
    assert len(payload["vehicles"]) == 5
    assert payload["kpis"]["orders_open"] == 4
    assert datetime.fromisoformat(payload["orders"][0]["due_at"]).utcoffset() is not None
    baseline_order = next(order for order in payload["orders"] if order["id"] == "ord-1001")
    assert baseline_order["status"] == "zugewiesen"
    assert client.get("/").status_code == 200
    config = client.get("/api/v1/config").json()
    assert config["auth_mode"] == "api_key"
    assert config["map_style_url"].startswith("https://")


def test_live_traffic_endpoint_is_authenticated_and_returns_geojson(client, monkeypatch):
    async def fake_live_traffic(points):
        assert points
        return {
            "type": "FeatureCollection",
            "features": [],
            "live_points": len(points),
            "missing_points": 0,
        }

    monkeypatch.setattr(scheduler, "live_traffic_segments", fake_live_traffic)
    assert client.get("/api/v1/traffic").status_code == 401
    response = client.get("/api/v1/traffic", headers=HEADERS)
    assert response.status_code == 200
    assert response.json()["type"] == "FeatureCollection"
    assert response.json()["live_points"] > 0


def test_telemetry_ingestion_is_idempotent_and_rejects_key_reuse(client):
    payload = {"positions": [{
        "vehicle_id": "truck-01", "lat": 53.55, "lon": 9.99,
        "speed_kmh": 52, "heading": 90, "accuracy_m": 5,
    }]}
    headers = {**HEADERS, "Idempotency-Key": "batch-001"}
    first = client.post("/api/v1/telemetry/positions", headers=headers, json=payload)
    second = client.post("/api/v1/telemetry/positions", headers=headers, json=payload)
    assert first.status_code == second.status_code == 202
    assert first.json() == second.json()
    assert first.json()["accepted"] == 1
    vehicle = client.get("/api/v1/dashboard", headers=HEADERS).json()["vehicles"][0]
    assert vehicle["accuracy_m"] == 5
    changed = json.loads(json.dumps(payload))
    changed["positions"][0]["speed_kmh"] = 20
    conflict = client.post("/api/v1/telemetry/positions", headers=headers, json=changed)
    assert conflict.status_code == 409
    payload["positions"][0]["timestamp"] = "2026-11-02T12:00:00"
    invalid_timestamp = client.post("/api/v1/telemetry/positions", headers={**HEADERS, "Idempotency-Key": "batch-002"}, json=payload)
    assert invalid_timestamp.status_code == 422


def test_order_creation_and_warehouse_status_update(client):
    order = client.post("/api/v1/orders", headers=HEADERS, json={
        "id": "ord-test", "pickup": "Hamburg", "delivery": "Berlin",
        "pickup_lat": 53.55, "pickup_lon": 10.0, "delivery_lat": 52.52,
        "delivery_lon": 13.4, "weight_kg": 1000, "volume_m3": 5,
    })
    assert order.status_code == 201
    assert order.json()["status"] == "offen"
    warehouse = client.put(
        "/api/v1/warehouses/wh-ham/status",
        headers=HEADERS,
        json={"occupied_ramps": 6, "queue_length": 4, "wait_minutes": 20},
    )
    assert warehouse.status_code == 200
    assert warehouse.json()["occupied_ramps"] == 6


def test_optimization_uses_road_matrix_and_requires_human_decision(client, monkeypatch):
    async def fake_matrix(points):
        size = len(points)
        distances = [[0 if i == j else 60000 + abs(i - j) * 1000 for j in range(size)] for i in range(size)]
        times = [[0 if i == j else 15 * 60 for j in range(size)] for i in range(size)]
        return RoadMatrix(distances, times, [0.8] * size, size, 0, [])

    async def fake_geometry(points):
        return {"type": "LineString", "coordinates": [[lon, lat] for lat, lon in points]}

    monkeypatch.setattr(optimizer, "road_matrix", fake_matrix)
    monkeypatch.setattr(optimizer, "road_geometry", fake_geometry)
    result = client.post("/api/v1/optimizations?time_limit_seconds=1", headers=HEADERS, json={})
    assert result.status_code == 201
    payload = result.json()
    assert payload["solver"] == "OR-Tools RoutingModel (Guided Local Search)"
    assert payload["limitations"]
    assert payload["routes"]
    assert payload["traffic"]["live_points"] > 0
    assert payload["routes"][0]["geometry"]["type"] == "LineString"
    persisted_route = next(
        route for route in client.get("/api/v1/dashboard", headers=HEADERS).json()["routes"]
        if route["status"] == "vorgeschlagen"
    )
    assert persisted_route["geometry"]["coordinates"]
    if payload["routes"]:
        route = payload["routes"][0]
        assert route["status"] == "vorgeschlagen"
        decision = client.post(
            f"/api/v1/routes/{route['id']}/decision",
            headers=HEADERS,
            json={"decision": "confirm"},
        )
        assert decision.status_code == 200
        assert decision.json()["status"] == "aktiv"


def test_order_validation_and_alert_acknowledgement(client):
    invalid = client.post("/api/v1/orders", headers=HEADERS, json={
        "pickup": "Hamburg", "delivery": "Berlin", "pickup_lat": 53.5,
        "pickup_lon": 10, "delivery_lat": 52.5, "delivery_lon": 13.4,
        "weight_kg": -1, "volume_m3": 2,
    })
    assert invalid.status_code == 422
    assert invalid.headers["content-type"].startswith("application/problem+json")
    alerts = client.get("/api/v1/alerts", headers=HEADERS).json()
    response = client.post(f"/api/v1/alerts/{alerts[0]['id']}/acknowledge", headers=HEADERS)
    assert response.status_code == 200
    assert response.json()["acknowledged"] == 1


def test_order_requires_timezone_aware_due_date(client):
    response = client.post("/api/v1/orders", headers=HEADERS, json={
        "pickup": "Hamburg", "delivery": "Berlin", "pickup_lat": 53.5,
        "pickup_lon": 10, "delivery_lat": 52.5, "delivery_lon": 13.4,
        "weight_kg": 1000, "volume_m3": 5, "due_at": "2026-11-02T18:00:00",
    })
    assert response.status_code == 422
    assert response.headers["content-type"].startswith("application/problem+json")


def test_oidc_jwt_verification_and_role_based_access(client, monkeypatch):
    pytest.importorskip("cryptography")
    import jwt
    from cryptography.hazmat.primitives.asymmetric import rsa

    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    public_key = private_key.public_key()
    monkeypatch.setattr(auth, "AUTH_MODE", "oidc")
    monkeypatch.setattr(auth, "OIDC_ISSUER", "https://identity.example/realms/nordroute")

    class TestJwksClient:
        def get_signing_key_from_jwt(self, _token):
            return SimpleNamespace(key=public_key)

    monkeypatch.setattr(auth, "jwks_client", lambda: TestJwksClient())

    def token_for(role):
        return jwt.encode({
            "sub": "test-user",
            "iss": auth.OIDC_ISSUER,
            "aud": auth.OIDC_AUDIENCE,
            "iat": int(datetime.now().timestamp()),
            "exp": int(datetime.now().timestamp()) + 300,
            "realm_access": {"roles": [role]},
        }, private_key, algorithm="RS256")

    viewer_headers = {"Authorization": f"Bearer {token_for('viewer')}"}
    assert client.get("/api/v1/dashboard", headers=viewer_headers).status_code == 200
    forbidden = client.post("/api/v1/optimizations", headers=viewer_headers, json={})
    assert forbidden.status_code == 403
    dispatcher_headers = {"Authorization": f"Bearer {token_for('dispatcher')}"}
    assert client.get("/api/v1/dashboard", headers=dispatcher_headers).status_code == 200


def test_websocket_stream_requires_key_and_sends_dashboard(client):
    with client.websocket_connect("/ws/v1/live?api_key=local-demo-key-change-me") as socket:
        message = socket.receive_json()
        assert message["vehicles"][0]["id"] == "truck-01"
