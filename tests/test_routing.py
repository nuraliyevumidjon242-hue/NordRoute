from __future__ import annotations

import asyncio

import httpx
import pytest

import services.routing as routing


def test_road_matrix_uses_valhalla_and_live_tomtom_flow(monkeypatch):
    async def responder(request):
        if request.url.host == "valhalla":
            assert request.url.path == "/sources_to_targets"
            body = request.content.decode()
            assert '"costing":"truck"' in body
            return httpx.Response(200, json={
                "sources_to_targets": [
                    [{"distance": 0, "time": 0}, {"distance": 100, "time": 3600}],
                    [{"distance": 110, "time": 3900}, {"distance": 0, "time": 0}],
                ]
            })
        if request.url.host == "api.tomtom.com":
            assert request.url.path.endswith("/flowSegmentData/relative/10/json")
            return httpx.Response(200, json={
                "flowSegmentData": {
                    "currentSpeed": 30,
                    "freeFlowSpeed": 60,
                    "coordinates": {"coordinate": [
                        {"longitude": 13.4, "latitude": 52.5},
                        {"longitude": 13.41, "latitude": 52.51},
                    ]},
                }
            })
        raise AssertionError(f"Unexpected request URL: {request.url}")

    client = httpx.AsyncClient(transport=httpx.MockTransport(responder))
    monkeypatch.setattr(routing.httpx, "AsyncClient", lambda **_: client)
    monkeypatch.setattr(routing, "TOMTOM_API_KEY", "test-key")
    monkeypatch.setattr(routing, "VALHALLA_URL", "http://valhalla:8002")
    monkeypatch.setattr(routing, "_traffic_cache", {})
    monkeypatch.setattr(routing, "_traffic_lock", asyncio.Lock())

    async def run():
        try:
            result = await routing.road_matrix([(52.52, 13.405), (52.51, 13.39)])
        finally:
            await client.aclose()
        return result

    result = asyncio.run(run())
    assert result.distances_m[0][1] == 100000
    assert result.traffic_times_s[0][1] == 7200
    assert result.traffic_times_s[1][0] == 7800
    assert result.live_traffic_points == 2
    assert result.missing_traffic_points == 0
    assert len(result.traffic_segments) == 1
    segment = result.traffic_segments[0]
    assert segment["geometry"]["type"] == "LineString"
    assert segment["properties"]["speed_ratio"] == 0.5


def test_live_traffic_segments_uses_tomtom_cache_and_returns_geojson(monkeypatch):
    calls = 0

    async def responder(request):
        nonlocal calls
        calls += 1
        return httpx.Response(200, json={
            "flowSegmentData": {
                "currentSpeed": 20,
                "freeFlowSpeed": 60,
                "coordinates": {"coordinate": [
                    {"longitude": 13.4, "latitude": 52.5},
                    {"longitude": 13.41, "latitude": 52.51},
                ]},
            }
        })

    async_client_class = httpx.AsyncClient
    monkeypatch.setattr(
        routing.httpx,
        "AsyncClient",
        lambda **_: async_client_class(transport=httpx.MockTransport(responder)),
    )
    monkeypatch.setattr(routing, "TOMTOM_API_KEY", "test-key")
    monkeypatch.setattr(routing, "_traffic_cache", {})
    monkeypatch.setattr(routing, "_traffic_lock", asyncio.Lock())

    async def run():
        points = [(52.52, 13.405), (52.52, 13.405)]
        first = await routing.live_traffic_segments(points)
        second = await routing.live_traffic_segments(points)
        return first, second

    first, second = asyncio.run(run())
    assert calls == 1
    assert first["live_points"] == 1
    assert first["missing_points"] == 0
    assert len(first["features"]) == 1
    assert first["features"][0]["properties"]["speed_ratio"] == pytest.approx(1 / 3)
    assert second["features"] == first["features"]


def test_tomtom_auth_errors_fail_closed(monkeypatch):
    async def responder(request):
        if request.url.host == "valhalla":
            return httpx.Response(200, json={
                "sources_to_targets": [[{"distance": 0, "time": 0}]]
            })
        return httpx.Response(401, json={"error": "invalid API key"})

    client = httpx.AsyncClient(transport=httpx.MockTransport(responder))
    monkeypatch.setattr(routing.httpx, "AsyncClient", lambda **_: client)
    monkeypatch.setattr(routing, "TOMTOM_API_KEY", "bad-key")
    monkeypatch.setattr(routing, "VALHALLA_URL", "http://valhalla:8002")
    monkeypatch.setattr(routing, "_traffic_cache", {})
    monkeypatch.setattr(routing, "_traffic_lock", asyncio.Lock())

    async def run():
        try:
            with pytest.raises(routing.RoutingUnavailable, match="rejected"):
                await routing.road_matrix([(52.52, 13.405)])
        finally:
            await client.aclose()

    asyncio.run(run())


def test_valhalla_polyline_decodes_to_geojson_coordinates():
    assert routing._decode_polyline("_p~iF~ps|U_ulLnnqC", precision=5) == [[-120.2, 38.5], [-120.95, 40.7]]
