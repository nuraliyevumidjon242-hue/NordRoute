from __future__ import annotations

import asyncio
import os
import time
from dataclasses import dataclass
from typing import Any

import httpx

VALHALLA_URL = os.getenv("VALHALLA_URL", "http://localhost:8002").rstrip("/")
TOMTOM_API_KEY = os.getenv("TOMTOM_API_KEY", "")
TRAFFIC_CACHE_TTL = max(1, int(os.getenv("TRAFFIC_CACHE_TTL_SECONDS", "60")))
TRAFFIC_CONCURRENCY = max(1, int(os.getenv("TRAFFIC_CONCURRENCY", "4")))
TRAFFIC_REQUESTS_PER_SECOND = max(1, int(os.getenv("TRAFFIC_REQUESTS_PER_SECOND", "10")))

_traffic_cache: dict[tuple[float, float], tuple[float, dict[str, Any] | None]] = {}
_traffic_lock = asyncio.Lock()
_traffic_next_request = 0.0
TRAFFIC_MAX_CACHE_ENTRIES = max(1, int(os.getenv("TRAFFIC_MAX_CACHE_ENTRIES", "10000")))


class RoutingUnavailable(RuntimeError):
    pass


@dataclass(frozen=True)
class RoadMatrix:
    distances_m: list[list[int]]
    traffic_times_s: list[list[int]]
    traffic_factors: list[float]
    live_traffic_points: int
    missing_traffic_points: int
    traffic_segments: list[dict[str, Any]]


def _location(point: tuple[float, float]) -> dict[str, float]:
    lat, lon = point
    return {"lat": lat, "lon": lon}


async def _traffic_factor(client: httpx.AsyncClient, point: tuple[float, float], semaphore: asyncio.Semaphore) -> float | None:
    global _traffic_next_request
    if not TOMTOM_API_KEY:
        raise RoutingUnavailable("TOMTOM_API_KEY is required to optimize with live traffic.")
    key = (round(point[0], 5), round(point[1], 5))
    async with _traffic_lock:
        now = time.monotonic()
        expired = [cache_key for cache_key, (created, _) in _traffic_cache.items()
                   if now - created >= TRAFFIC_CACHE_TTL]
        for cache_key in expired:
            _traffic_cache.pop(cache_key, None)
        cached = _traffic_cache.get(key)
        if cached and time.monotonic() - cached[0] < TRAFFIC_CACHE_TTL:
            data = cached[1]
            return data["factor"] if data else None

    async with semaphore:
        async with _traffic_lock:
            now = time.monotonic()
            delay = max(0.0, _traffic_next_request - now)
            _traffic_next_request = max(now, _traffic_next_request) + 1 / TRAFFIC_REQUESTS_PER_SECOND
        if delay:
            await asyncio.sleep(delay)
        try:
            response = await client.get(
                "https://api.tomtom.com/traffic/services/4/flowSegmentData/relative/10/json",
                params={"point": f"{point[0]},{point[1]}", "key": TOMTOM_API_KEY},
                timeout=15,
            )
        except httpx.HTTPError as exc:
            raise RoutingUnavailable(f"TomTom Traffic API request failed: {exc}") from exc

    if response.status_code in (400, 404):
        async with _traffic_lock:
            _traffic_cache[key] = (time.monotonic(), None)
            while len(_traffic_cache) > TRAFFIC_MAX_CACHE_ENTRIES:
                _traffic_cache.pop(next(iter(_traffic_cache)))
        return None
    if response.status_code in (401, 403):
        raise RoutingUnavailable("TomTom rejected TOMTOM_API_KEY; check the Traffic API subscription and key.")
    if response.status_code == 429:
        raise RoutingUnavailable("TomTom Traffic API rate limit reached; retry after the provider's reset window.")
    if response.is_error:
        raise RoutingUnavailable(f"TomTom Traffic API returned HTTP {response.status_code}.")
    try:
        segment = response.json()["flowSegmentData"]
        current = float(segment["currentSpeed"])
        free_flow = float(segment["freeFlowSpeed"])
        closed = bool(segment.get("roadClosure", False))
        ratio = max(0.25, min(1.25, current / free_flow)) if current > 0 and free_flow > 0 else 0.25 if closed else None
    except (KeyError, TypeError, ValueError) as exc:
        raise RoutingUnavailable("TomTom Traffic API returned an invalid flow-segment response.") from exc

    coordinates = []
    for coordinate in segment.get("coordinates", {}).get("coordinate", []):
        try:
            coordinates.append([float(coordinate["longitude"]), float(coordinate["latitude"])])
        except (KeyError, TypeError, ValueError):
            raise RoutingUnavailable("TomTom Traffic API returned invalid segment coordinates.") from None
    value = {
        "factor": ratio,
        "current_speed_kmh": current,
        "free_flow_speed_kmh": free_flow,
        "road_closure": closed,
        "coordinates": coordinates,
    } if ratio is not None else None
    async with _traffic_lock:
        _traffic_cache[key] = (time.monotonic(), value)
        while len(_traffic_cache) > TRAFFIC_MAX_CACHE_ENTRIES:
            _traffic_cache.pop(next(iter(_traffic_cache)))
    return ratio


async def live_traffic_segments(points: list[tuple[float, float]]) -> dict[str, Any]:
    unique_points = list(dict.fromkeys(points))
    if not unique_points:
        return {"type": "FeatureCollection", "features": [], "live_points": 0, "missing_points": 0}
    async with httpx.AsyncClient() as client:
        semaphore = asyncio.Semaphore(max(1, TRAFFIC_CONCURRENCY))
        results = await asyncio.gather(
            *(_traffic_factor(client, point, semaphore) for point in unique_points)
        )
    features = []
    seen = set()
    for point, factor in zip(unique_points, results, strict=True):
        cache_key = (round(point[0], 5), round(point[1], 5))
        cached = _traffic_cache.get(cache_key)
        data = cached[1] if cached else None
        coordinates = data.get("coordinates", []) if data else []
        if factor is None or len(coordinates) < 2:
            continue
        signature = tuple((round(lon, 5), round(lat, 5)) for lon, lat in coordinates)
        if signature in seen:
            continue
        seen.add(signature)
        features.append(
            {
                "type": "Feature",
                "geometry": {"type": "LineString", "coordinates": coordinates},
                "properties": {
                    "current_speed_kmh": data["current_speed_kmh"],
                    "free_flow_speed_kmh": data["free_flow_speed_kmh"],
                    "speed_ratio": factor,
                    "road_closure": data["road_closure"],
                },
            }
        )
    return {
        "type": "FeatureCollection",
        "features": features,
        "live_points": sum(value is not None for value in results),
        "missing_points": sum(value is None for value in results),
        "fetched_at": time.time(),
    }


async def road_matrix(points: list[tuple[float, float]]) -> RoadMatrix:
    if len(points) < 1:
        return RoadMatrix([], [], [], 0, 0, [])
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{VALHALLA_URL}/sources_to_targets",
                json={
                    "sources": [_location(point) for point in points],
                    "targets": [_location(point) for point in points],
                    "costing": "truck",
                    "units": "kilometers",
                },
                timeout=httpx.Timeout(120, connect=10),
            )
        except httpx.HTTPError as exc:
            raise RoutingUnavailable(f"Valhalla road matrix request failed: {exc}") from exc
        if response.is_error:
            raise RoutingUnavailable(f"Valhalla road matrix returned HTTP {response.status_code}: {response.text[:500]}")
        try:
            raw_matrix = response.json()["sources_to_targets"]
            if len(raw_matrix) != len(points) or any(len(row) != len(points) for row in raw_matrix):
                raise ValueError("matrix is not square")
            distances_m: list[list[int]] = []
            base_times_s: list[list[int]] = []
            for row in raw_matrix:
                distance_row, time_row = [], []
                for item in row:
                    if not item or item.get("distance") is None or item.get("time") is None:
                        distance_row.append(1_000_000_000)
                        time_row.append(1_000_000_000)
                    else:
                        distance_row.append(max(0, round(float(item["distance"]) * 1000)))
                        time_row.append(max(0, round(float(item["time"]))))
                distances_m.append(distance_row)
                base_times_s.append(time_row)
        except (KeyError, TypeError, ValueError) as exc:
            raise RoutingUnavailable("Valhalla returned an invalid road-network matrix.") from exc

        semaphore = asyncio.Semaphore(max(1, TRAFFIC_CONCURRENCY))
        unique_points = list(dict.fromkeys(points))
        unique_factors = await asyncio.gather(
            *(_traffic_factor(client, point, semaphore) for point in unique_points)
        )
        factors_by_point = dict(zip(unique_points, unique_factors, strict=True))
        traffic_results = [factors_by_point[point] for point in points]
        traffic_features = []
        seen_segments = set()
        for point, factor in zip(unique_points, unique_factors, strict=True):
            cache_key = (round(point[0], 5), round(point[1], 5))
            cached = _traffic_cache.get(cache_key)
            data = cached[1] if cached else None
            coordinates = data.get("coordinates", []) if data else []
            signature = tuple((round(lon, 5), round(lat, 5)) for lon, lat in coordinates)
            if factor is None or len(coordinates) < 2 or signature in seen_segments:
                continue
            seen_segments.add(signature)
            traffic_features.append(
                {
                    "type": "Feature",
                    "geometry": {"type": "LineString", "coordinates": coordinates},
                    "properties": {
                        "current_speed_kmh": data["current_speed_kmh"],
                        "free_flow_speed_kmh": data["free_flow_speed_kmh"],
                        "speed_ratio": factor,
                        "road_closure": data["road_closure"],
                    },
                }
            )

    factors = [factor if factor is not None else 1.0 for factor in traffic_results]
    traffic_times = [
        [round(duration / factors[source]) if duration < 1_000_000_000 else duration for duration in row]
        for source, row in enumerate(base_times_s)
    ]
    return RoadMatrix(
        distances_m=distances_m,
        traffic_times_s=traffic_times,
        traffic_factors=factors,
        live_traffic_points=sum(factor is not None for factor in traffic_results),
        missing_traffic_points=sum(factor is None for factor in traffic_results),
        traffic_segments=traffic_features,
    )


def _decode_polyline(encoded: str, precision: int = 6) -> list[list[float]]:
    coordinates: list[list[float]] = []
    lat = lon = index = 0
    factor = 10**precision
    while index < len(encoded):
        values = []
        for _ in range(2):
            result = shift = 0
            while True:
                if index >= len(encoded):
                    raise RoutingUnavailable("Valhalla returned a truncated route geometry.")
                byte = ord(encoded[index]) - 63
                index += 1
                result |= (byte & 0x1F) << shift
                shift += 5
                if byte < 0x20:
                    break
            values.append(~(result >> 1) if result & 1 else result >> 1)
        lat += values[0]
        lon += values[1]
        coordinates.append([lon / factor, lat / factor])
    return coordinates


async def road_geometry(points: list[tuple[float, float]]) -> dict[str, Any]:
    if len(points) < 2:
        return {"type": "LineString", "coordinates": []}
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{VALHALLA_URL}/route",
                json={
                    "locations": [_location(point) for point in points],
                    "costing": "truck",
                    "units": "kilometers",
                    "directions_options": {"units": "kilometers", "language": "de-DE"},
                },
                timeout=httpx.Timeout(60, connect=10),
            )
    except httpx.HTTPError as exc:
        raise RoutingUnavailable(f"Valhalla route geometry request failed: {exc}") from exc
    if response.is_error:
        raise RoutingUnavailable(f"Valhalla route request returned HTTP {response.status_code}: {response.text[:500]}")
    try:
        legs = response.json()["trip"]["legs"]
        coordinates: list[list[float]] = []
        for leg in legs:
            segment = _decode_polyline(leg["shape"])
            coordinates.extend(segment if not coordinates else segment[1:])
        if len(coordinates) < 2:
            raise ValueError("route geometry is empty")
        return {"type": "LineString", "coordinates": coordinates}
    except (KeyError, TypeError, ValueError) as exc:
        raise RoutingUnavailable("Valhalla returned an invalid truck-route geometry.") from exc
