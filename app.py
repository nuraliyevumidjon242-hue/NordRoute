from __future__ import annotations

import asyncio
import hashlib
import json
import os
import sqlite3
import time
import uuid
from contextlib import asynccontextmanager, closing
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Annotated, Literal

from fastapi import Depends, FastAPI, Header, HTTPException, Query, WebSocket, WebSocketDisconnect
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, field_validator

from services.auth import (
    API_KEY,
    AUTH_MODE,
    OIDC_CLIENT_ID,
    OIDC_ISSUER,
    Principal,
    require_roles,
    websocket_principal,
)
from services.optimizer import optimize_routes
from services.routing import RoutingUnavailable, live_traffic_segments

ROOT = Path(__file__).parent
DB_PATH = Path(os.getenv("DATABASE_PATH", str(ROOT / "data" / "scheduler.db")))
MAP_STYLE_URL = os.getenv(
    "MAP_STYLE_URL",
    "https://basemaps.cartocdn.com/gl/positron-gl-style/style.json",
)
READ_ACTOR = Annotated[
    Principal,
    Depends(require_roles("admin", "dispatcher", "viewer", "dpo")),
]
DISPATCH_ACTOR = Annotated[
    Principal,
    Depends(require_roles("admin", "dispatcher")),
]
AUDIT_ACTOR = Annotated[
    Principal,
    Depends(require_roles("admin", "dpo")),
]


@asynccontextmanager
async def lifespan(_: FastAPI):
    initialize()
    yield


app = FastAPI(
    title="Distributed Logistics Scheduler",
    description="Demo-API für Fahrzeugtelemetrie, Aufträge, Alerts und erklärbare Routenvorschläge.",
    version="0.1.0",
    openapi_url="/api/v1/openapi.json",
    docs_url="/api/v1/docs",
    lifespan=lifespan,
)


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def connect() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(DB_PATH, timeout=10)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA journal_mode=WAL")
    return db


def fetch_all(db: sqlite3.Connection, query: str, args: tuple = ()) -> list[dict]:
    return [dict(row) for row in db.execute(query, args).fetchall()]


def fetch_one(db: sqlite3.Connection, query: str, args: tuple = ()) -> dict | None:
    row = db.execute(query, args).fetchone()
    return dict(row) if row else None


def initialize() -> None:
    with closing(connect()) as db:
        db.executescript(
            """
            CREATE TABLE IF NOT EXISTS vehicles (
                id TEXT PRIMARY KEY, label TEXT NOT NULL, status TEXT NOT NULL,
                lat REAL NOT NULL, lon REAL NOT NULL, speed_kmh REAL NOT NULL,
                heading REAL NOT NULL, accuracy_m REAL NOT NULL DEFAULT 10,
                max_weight_kg REAL NOT NULL,
                max_volume_m3 REAL NOT NULL, driven_minutes INTEGER NOT NULL,
                updated_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS warehouses (
                id TEXT PRIMARY KEY, name TEXT NOT NULL, city TEXT NOT NULL,
                lat REAL NOT NULL, lon REAL NOT NULL, ramp_count INTEGER NOT NULL,
                occupied_ramps INTEGER NOT NULL, queue_length INTEGER NOT NULL,
                wait_minutes INTEGER NOT NULL
            );
            CREATE TABLE IF NOT EXISTS orders (
                id TEXT PRIMARY KEY, pickup TEXT NOT NULL, delivery TEXT NOT NULL,
                pickup_lat REAL NOT NULL, pickup_lon REAL NOT NULL,
                delivery_lat REAL NOT NULL, delivery_lon REAL NOT NULL,
                weight_kg REAL NOT NULL, volume_m3 REAL NOT NULL,
                priority TEXT NOT NULL, due_at TEXT NOT NULL, status TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS routes (
                id TEXT PRIMARY KEY, vehicle_id TEXT NOT NULL, order_ids TEXT NOT NULL,
                distance_km REAL NOT NULL, fuel_l REAL NOT NULL, co2_kg REAL NOT NULL,
                toll_eur REAL NOT NULL, break_minutes INTEGER NOT NULL DEFAULT 0,
                travel_minutes INTEGER NOT NULL DEFAULT 0, geometry_json TEXT NOT NULL DEFAULT '{}',
                stops_json TEXT NOT NULL DEFAULT '[]', status TEXT NOT NULL, explanation TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS alerts (
                id TEXT PRIMARY KEY, severity TEXT NOT NULL, kind TEXT NOT NULL,
                message TEXT NOT NULL, entity_id TEXT, created_at TEXT NOT NULL,
                acknowledged INTEGER NOT NULL DEFAULT 0
            );
            CREATE TABLE IF NOT EXISTS idempotency (
                key TEXT PRIMARY KEY, payload_hash TEXT NOT NULL, response TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS audit_log (
                id TEXT PRIMARY KEY, actor TEXT NOT NULL, action TEXT NOT NULL,
                entity TEXT NOT NULL, created_at TEXT NOT NULL
            );
            """
        )
        route_columns = {row["name"] for row in db.execute("PRAGMA table_info(routes)")}
        route_migrations = {
            "break_minutes": "INTEGER NOT NULL DEFAULT 0",
            "travel_minutes": "INTEGER NOT NULL DEFAULT 0",
            "geometry_json": "TEXT NOT NULL DEFAULT '{}'",
            "stops_json": "TEXT NOT NULL DEFAULT '[]'",
        }
        for column, definition in route_migrations.items():
            if column not in route_columns:
                db.execute(f"ALTER TABLE routes ADD COLUMN {column} {definition}")
        vehicle_columns = {row["name"] for row in db.execute("PRAGMA table_info(vehicles)")}
        if "accuracy_m" not in vehicle_columns:
            db.execute("ALTER TABLE vehicles ADD COLUMN accuracy_m REAL NOT NULL DEFAULT 10")
        for order in fetch_all(db, "SELECT id, due_at FROM orders"):
            try:
                due_at = datetime.fromisoformat(order["due_at"].replace("Z", "+00:00"))
                if due_at.tzinfo is None:
                    raise ValueError("timezone missing")
            except (TypeError, ValueError):
                db.execute(
                    "UPDATE orders SET due_at=? WHERE id=?",
                    ((datetime.now(timezone.utc) + timedelta(hours=24)).isoformat(), order["id"]),
                )
        if db.execute("SELECT COUNT(*) FROM vehicles").fetchone()[0] == 0:
            seed(db)
        db.commit()


def seed(db: sqlite3.Connection) -> None:
    stamp = now_utc()
    due_times = [
        (datetime.now(timezone.utc) + timedelta(hours=hours)).isoformat()
        for hours in (3, 5, 4, 20, 22)
    ]
    vehicles = [
        ("truck-01", "LKW 01 · Nord", "unterwegs", 53.5511, 9.9937, 68, 110, 12000, 48, 96),
        ("truck-02", "LKW 02 · Ost", "unterwegs", 52.5200, 13.4050, 74, 215, 10000, 42, 138),
        ("truck-03", "LKW 03 · Mitte", "wartend", 51.2277, 6.7735, 0, 0, 15000, 55, 202),
        ("truck-04", "LKW 04 · Süd", "Pause", 48.1351, 11.5820, 0, 0, 12000, 48, 72),
        ("truck-05", "LKW 05 · West", "unterwegs", 50.1109, 8.6821, 61, 305, 8000, 36, 254),
    ]
    db.executemany(
        "INSERT INTO vehicles (id,label,status,lat,lon,speed_kmh,heading,accuracy_m,max_weight_kg,max_volume_m3,driven_minutes,updated_at) "
        "VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
        [(v[0], v[1], v[2], v[3], v[4], v[5], v[6], 10, v[7], v[8], v[9], stamp) for v in vehicles],
    )
    warehouses = [
        ("wh-ham", "Hafenlager Nord", "Hamburg", 53.5511, 9.9937, 8, 5, 3, 18),
        ("wh-ber", "Zentrallager Ost", "Berlin", 52.5200, 13.4050, 10, 7, 2, 24),
        ("wh-fra", "Verteilzentrum Mitte", "Frankfurt", 50.1109, 8.6821, 6, 2, 1, 8),
    ]
    db.executemany("INSERT INTO warehouses VALUES (?,?,?,?,?,?,?,?,?)", warehouses)
    orders = [
        ("ord-1001", "Hamburg", "Berlin", 53.5511, 9.9937, 52.5200, 13.4050, 4200, 18, "hoch", due_times[0], "zugewiesen"),
        ("ord-1002", "Frankfurt", "München", 50.1109, 8.6821, 48.1351, 11.5820, 2800, 12, "normal", due_times[1], "offen"),
        ("ord-1003", "Düsseldorf", "Frankfurt", 51.2277, 6.7735, 50.1109, 8.6821, 5600, 22, "hoch", due_times[2], "offen"),
        ("ord-1004", "Berlin", "Hamburg", 52.5200, 13.4050, 53.5511, 9.9937, 1800, 8, "normal", due_times[3], "offen"),
        ("ord-1005", "München", "Frankfurt", 48.1351, 11.5820, 50.1109, 8.6821, 3300, 14, "normal", due_times[4], "offen"),
    ]
    db.executemany("INSERT INTO orders VALUES (?,?,?,?,?,?,?,?,?,?,?,?)", orders)
    db.execute(
        "INSERT INTO alerts VALUES (?,?,?,?,?,?,0)",
        ("alert-seed-01", "warning", "lager", "Hamburg: Rampenauslastung bei 63 %, Wartezeit 18 Min.", "wh-ham", stamp),
    )
    db.execute(
        "INSERT INTO alerts VALUES (?,?,?,?,?,?,0)",
        ("alert-seed-02", "critical", "lenkzeit", "LKW 05 nähert sich der empfohlenen Pausenzeit.", "truck-05", stamp),
    )
    db.execute(
        "INSERT INTO routes (id,vehicle_id,order_ids,distance_km,fuel_l,co2_kg,toll_eur,break_minutes,status,explanation,created_at) "
        "VALUES (?,?,?,?,?,?,?,?,?,?,?)",
        ("route-seed-01", "truck-01", '["ord-1001"]', 289, 87, 232, 46, 45, "aktiv",
         "Baseline-Demo: bestehende Zuordnung für den Vergleich.", stamp),
    )


@app.exception_handler(HTTPException)
async def problem_details(_, exc: HTTPException):
    detail = exc.detail if isinstance(exc.detail, dict) else {"title": str(exc.detail)}
    return JSONResponse(
        status_code=exc.status_code,
        content={"type": detail.get("type", "about:blank"), "title": detail.get("title", "Request failed"),
                 "status": exc.status_code, "detail": detail.get("detail")},
        media_type="application/problem+json",
        headers=exc.headers,
    )


@app.exception_handler(RequestValidationError)
async def validation_problem_details(_, exc: RequestValidationError):
    errors = [
        {"location": list(error["loc"]), "message": error["msg"], "code": error["type"]}
        for error in exc.errors()
    ]
    return JSONResponse(
        status_code=422,
        content={
            "type": "about:blank",
            "title": "Request validation failed",
            "status": 422,
            "errors": errors,
        },
        media_type="application/problem+json",
    )


class Position(BaseModel):
    vehicle_id: str = Field(min_length=1, max_length=80)
    lat: float = Field(ge=-90, le=90)
    lon: float = Field(ge=-180, le=180)
    speed_kmh: float = Field(ge=0, le=180)
    heading: float = Field(ge=0, lt=360)
    accuracy_m: float = Field(default=10, ge=0, le=10000)
    timestamp: datetime | None = None

    @field_validator("timestamp")
    @classmethod
    def timestamp_must_include_timezone(cls, value: datetime | None) -> datetime | None:
        if value is not None and value.utcoffset() is None:
            raise ValueError("timestamp must include a timezone offset")
        return value


class TelemetryBatch(BaseModel):
    positions: list[Position] = Field(min_length=1, max_length=1000)


class OrderInput(BaseModel):
    id: str | None = Field(default=None, max_length=80)
    pickup: str = Field(min_length=1, max_length=120)
    delivery: str = Field(min_length=1, max_length=120)
    pickup_lat: float = Field(ge=-90, le=90)
    pickup_lon: float = Field(ge=-180, le=180)
    delivery_lat: float = Field(ge=-90, le=90)
    delivery_lon: float = Field(ge=-180, le=180)
    weight_kg: float = Field(gt=0, le=100000)
    volume_m3: float = Field(gt=0, le=1000)
    priority: Literal["normal", "hoch"] = "normal"
    due_at: datetime | None = None

    @field_validator("due_at")
    @classmethod
    def due_at_must_include_timezone(cls, value: datetime | None) -> datetime | None:
        if value is not None and value.utcoffset() is None:
            raise ValueError("due_at must include a timezone offset")
        return value


class DecisionInput(BaseModel):
    decision: Literal["confirm", "reject"]


class WarehouseStatus(BaseModel):
    occupied_ramps: int = Field(ge=0, le=1000)
    queue_length: int = Field(ge=0, le=10000)
    wait_minutes: int = Field(ge=0, le=10080)


def log_audit(db: sqlite3.Connection, actor: str, action: str, entity: str) -> None:
    db.execute("INSERT INTO audit_log VALUES (?,?,?, ?,?)", (str(uuid.uuid4()), actor, action, entity, now_utc()))


def dashboard_data(db: sqlite3.Connection) -> dict:
    vehicles = fetch_all(db, "SELECT * FROM vehicles ORDER BY id")
    warehouses = fetch_all(db, "SELECT * FROM warehouses ORDER BY city")
    orders = fetch_all(db, "SELECT * FROM orders ORDER BY priority DESC, id")
    alerts = fetch_all(db, "SELECT * FROM alerts ORDER BY created_at DESC LIMIT 50")
    routes = fetch_all(db, "SELECT * FROM routes ORDER BY created_at DESC LIMIT 20")
    for route in routes:
        route["order_ids"] = json.loads(route["order_ids"])
        route["geometry"] = json.loads(route.pop("geometry_json"))
        route["stops"] = json.loads(route.pop("stops_json"))
    open_orders = sum(order["status"] == "offen" for order in orders)
    distance = sum(route["distance_km"] for route in routes if route["status"] in ("aktiv", "vorgeschlagen"))
    fuel = sum(route["fuel_l"] for route in routes if route["status"] in ("aktiv", "vorgeschlagen"))
    return {
        "generated_at": now_utc(), "vehicles": vehicles, "warehouses": warehouses,
        "orders": orders, "alerts": alerts, "routes": routes,
        "kpis": {
            "vehicles_active": sum(v["status"] == "unterwegs" for v in vehicles),
            "orders_open": open_orders, "distance_km": round(distance),
            "fuel_l": round(fuel, 1), "otd_percent": None,
            "co2_kg": round(fuel * 2.68), "baseline_saving_percent": None,
        },
    }


@app.get("/health")
def health():
    return {
        "status": "ok",
        "timestamp": now_utc(),
        "auth_mode": AUTH_MODE,
        "routing_configured": bool(os.getenv("VALHALLA_URL")),
        "traffic_configured": bool(os.getenv("TOMTOM_API_KEY")),
    }


@app.get("/api/v1/config")
def public_config():
    return {
        "auth_mode": AUTH_MODE,
        "api_key": API_KEY if AUTH_MODE == "api_key" else None,
        "oidc_issuer": os.getenv("OIDC_BROWSER_ISSUER", OIDC_ISSUER) if AUTH_MODE == "oidc" else None,
        "oidc_client_id": OIDC_CLIENT_ID if AUTH_MODE == "oidc" else None,
        "map_style_url": MAP_STYLE_URL,
    }


@app.get("/", include_in_schema=False)
def home():
    return FileResponse(ROOT / "static" / "index.html")


app.mount("/static", StaticFiles(directory=ROOT / "static"), name="static")


@app.get("/api/v1/dashboard")
def get_dashboard(_: READ_ACTOR):
    with closing(connect()) as db:
        return dashboard_data(db)


@app.get("/api/v1/traffic")
async def get_live_traffic(_: READ_ACTOR):
    with closing(connect()) as db:
        vehicles = fetch_all(db, "SELECT lat, lon FROM vehicles WHERE status='unterwegs'")
    try:
        return await live_traffic_segments([(vehicle["lat"], vehicle["lon"]) for vehicle in vehicles])
    except RoutingUnavailable as exc:
        raise HTTPException(
            status_code=503,
            detail={"title": "Live traffic data is unavailable.", "detail": str(exc)},
        ) from exc


@app.post("/api/v1/telemetry/positions", status_code=202)
def ingest_positions(batch: TelemetryBatch, actor: DISPATCH_ACTOR, idempotency_key: Annotated[str | None, Header()] = None):
    payload = batch.model_dump(mode="json")
    digest = hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()
    key = idempotency_key or str(uuid.uuid4())
    with closing(connect()) as db:
        prior = fetch_one(db, "SELECT payload_hash, response FROM idempotency WHERE key=?", (key,))
        if prior:
            if prior["payload_hash"] != digest:
                raise HTTPException(409, detail={"title": "Idempotency-Key wurde mit anderem Inhalt wiederverwendet."})
            return json.loads(prior["response"])
        accepted = 0
        for pos in batch.positions:
            cur = db.execute(
                "UPDATE vehicles SET lat=?, lon=?, speed_kmh=?, heading=?, accuracy_m=?, status=?, updated_at=? WHERE id=?",
                (pos.lat, pos.lon, pos.speed_kmh, pos.heading, pos.accuracy_m,
                 "unterwegs" if pos.speed_kmh > 0 else "wartend",
                 (pos.timestamp or datetime.now(timezone.utc)).astimezone(timezone.utc).isoformat(), pos.vehicle_id),
            )
            if not cur.rowcount:
                raise HTTPException(404, detail={"title": f"Unbekanntes Fahrzeug: {pos.vehicle_id}"})
            db.execute(
                "INSERT INTO audit_log VALUES (?,?,?,?,?)",
                (str(uuid.uuid4()), actor.subject, "telemetry.ingested", pos.vehicle_id, now_utc()),
            )
            accepted += 1
        result = {"accepted": accepted, "idempotency_key": key}
        db.execute("INSERT INTO idempotency VALUES (?,?,?,?)", (key, digest, json.dumps(result), now_utc()))
        db.commit()
        return result


@app.post("/api/v1/orders", status_code=201)
def create_order(order: OrderInput, actor: DISPATCH_ACTOR):
    order_id = order.id or f"ord-{uuid.uuid4().hex[:8]}"
    data = order.model_dump()
    due_at = data["due_at"] or (datetime.now(timezone.utc) + timedelta(hours=24))
    with closing(connect()) as db:
        try:
            db.execute(
                "INSERT INTO orders VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                (order_id, data["pickup"], data["delivery"], data["pickup_lat"], data["pickup_lon"],
                 data["delivery_lat"], data["delivery_lon"], data["weight_kg"], data["volume_m3"],
                 data["priority"], due_at.astimezone(timezone.utc).isoformat(), "offen"),
            )
            log_audit(db, actor.subject, "order.created", order_id)
            db.commit()
        except sqlite3.IntegrityError:
            raise HTTPException(409, detail={"title": "Auftrags-ID existiert bereits."}) from None
        return fetch_one(db, "SELECT * FROM orders WHERE id=?", (order_id,))


@app.put("/api/v1/warehouses/{warehouse_id}/status")
def update_warehouse(warehouse_id: str, status: WarehouseStatus, actor: DISPATCH_ACTOR):
    with closing(connect()) as db:
        cur = db.execute(
            "UPDATE warehouses SET occupied_ramps=?, queue_length=?, wait_minutes=? WHERE id=?",
            (status.occupied_ramps, status.queue_length, status.wait_minutes, warehouse_id),
        )
        if not cur.rowcount:
            raise HTTPException(404, detail={"title": "Lager nicht gefunden."})
        log_audit(db, actor.subject, "warehouse.status_updated", warehouse_id)
        db.commit()
        return fetch_one(db, "SELECT * FROM warehouses WHERE id=?", (warehouse_id,))


@app.post("/api/v1/optimizations", status_code=201)
async def optimize(
    actor: DISPATCH_ACTOR,
    time_limit_seconds: Annotated[int, Query(ge=1, le=30)] = 8,
):
    started = time.perf_counter()
    with closing(connect()) as db:
        vehicles = fetch_all(db, "SELECT * FROM vehicles ORDER BY driven_minutes")
        orders = fetch_all(db, "SELECT * FROM orders WHERE status='offen' ORDER BY CASE priority WHEN 'hoch' THEN 0 ELSE 1 END, id")
        try:
            result = await optimize_routes(vehicles, orders, time_limit_seconds)
        except RoutingUnavailable as exc:
            raise HTTPException(
                status_code=503,
                detail={"title": "Live routing/traffic integrations are unavailable.", "detail": str(exc)},
            ) from exc
        except ValueError as exc:
            raise HTTPException(status_code=422, detail={"title": "Optimization input is invalid.", "detail": str(exc)}) from exc
        except RuntimeError as exc:
            raise HTTPException(status_code=422, detail={"title": "No feasible route proposal was found.", "detail": str(exc)}) from exc

        proposed = []
        for route in result.routes:
            route_id = f"route-{uuid.uuid4().hex[:10]}"
            order_ids = route["order_ids"]
            explanation = (
                f"OR-Tools mit Valhalla truck-road matrix und TomTom live flow an "
                f"{result.traffic_coverage['live']} Matrix-Standorten; "
                f"{route['travel_minutes']} geschätzte Fahrminuten. "
                "Verkehr auf jedem Straßenabschnitt und gesetzliche Pausen sind nicht garantiert."
            )
            db.execute(
                "INSERT INTO routes (id,vehicle_id,order_ids,distance_km,fuel_l,co2_kg,toll_eur,break_minutes,"
                "travel_minutes,geometry_json,stops_json,status,explanation,created_at) "
                "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (route_id, route["vehicle_id"], json.dumps(order_ids), route["distance_km"],
                 route["fuel_l"], route["co2_kg"], route["toll_eur"], route["break_minutes"],
                 route["travel_minutes"], json.dumps(route["geometry"]), json.dumps(route["stops"]),
                 "vorgeschlagen", explanation, now_utc()),
            )
            for order_id in order_ids:
                db.execute("UPDATE orders SET status='vorgeschlagen' WHERE id=?", (order_id,))
            proposed.append({"id": route_id, **route, "status": "vorgeschlagen", "explanation": explanation})

        if result.unassigned_order_ids:
            db.execute(
                "INSERT INTO alerts VALUES (?,?,?,?,?,?,0)",
                (f"alert-{uuid.uuid4().hex[:8]}", "warning", "optimierung",
                 f"{len(result.unassigned_order_ids)} Auftrag/Aufträge wegen Kapazität, Zeitfenster oder Fahrzeit nicht zugewiesen: "
                 f"{', '.join(result.unassigned_order_ids)}",
                 None, now_utc()),
            )
        log_audit(db, actor.subject, "optimization.proposed", f"{len(proposed)} routes")
        db.commit()
        return {"run_id": str(uuid.uuid4()), "solver": result.solver,
                "duration_ms": round((time.perf_counter() - started) * 1000),
                "routes": proposed, "unassigned_order_ids": result.unassigned_order_ids,
                "total_distance_km": result.distance_km,
                "traffic": {
                    "provider": "TomTom Traffic Flow Segment Data",
                    "live_points": result.traffic_coverage["live"],
                    "missing_points": result.traffic_coverage["missing"],
                    "cache_ttl_seconds": int(os.getenv("TRAFFIC_CACHE_TTL_SECONDS", "60")),
                },
                "explanation": "Fahrzeugzuordnung und Stoppreihenfolge werden durch OR-Tools berechnet; "
                "Vorschläge sind erst nach Disponentenfreigabe aktiv.",
                "limitations": [
                    "Live-Verkehr verwendet TomTom-Geschwindigkeitsdaten an Matrix-Standorten; "
                    "es ist keine abschnittsgenaue TomTom-Routenzeit.",
                    "Die Tageslenkzeit wird auf 9 Stunden begrenzt; 4,5-Stunden-Pausenintervalle "
                    "werden nicht solver-seitig garantiert.",
                    "Umweltzonen, ADR, Feiertagsfahrverbote, Maut und Echtzeit-Sperrungen benötigen "
                    "zusätzliche Fahrzeug- und Rechtsdaten.",
                ]}


@app.post("/api/v1/routes/{route_id}/decision")
def decide_route(route_id: str, decision: DecisionInput, actor: DISPATCH_ACTOR):
    with closing(connect()) as db:
        route = fetch_one(db, "SELECT * FROM routes WHERE id=?", (route_id,))
        if not route or route["status"] != "vorgeschlagen":
            raise HTTPException(404, detail={"title": "Offener Routenvorschlag nicht gefunden."})
        order_ids = json.loads(route["order_ids"])
        status = "aktiv" if decision.decision == "confirm" else "abgelehnt"
        db.execute("UPDATE routes SET status=? WHERE id=?", (status, route_id))
        order_status = "zugewiesen" if status == "aktiv" else "offen"
        db.executemany("UPDATE orders SET status=? WHERE id=?", [(order_status, order_id) for order_id in order_ids])
        log_audit(db, actor.subject, f"route.{decision.decision}", route_id)
        db.commit()
        route["order_ids"] = order_ids
        route["geometry"] = json.loads(route.pop("geometry_json"))
        route["stops"] = json.loads(route.pop("stops_json"))
        route["status"] = status
        return route


@app.get("/api/v1/routes")
def get_routes(_: READ_ACTOR, status: str | None = None):
    with closing(connect()) as db:
        routes = fetch_all(db, "SELECT * FROM routes WHERE status=? ORDER BY created_at DESC" if status else
                           "SELECT * FROM routes ORDER BY created_at DESC", (status,) if status else ())
        for route in routes:
            route["order_ids"] = json.loads(route["order_ids"])
            route["geometry"] = json.loads(route.pop("geometry_json"))
            route["stops"] = json.loads(route.pop("stops_json"))
        return routes


@app.get("/api/v1/alerts")
def get_alerts(_: READ_ACTOR, severity: str | None = None):
    with closing(connect()) as db:
        return fetch_all(db, "SELECT * FROM alerts WHERE severity=? ORDER BY created_at DESC" if severity else
                         "SELECT * FROM alerts ORDER BY created_at DESC", (severity,) if severity else ())


@app.post("/api/v1/alerts/{alert_id}/acknowledge")
def acknowledge_alert(alert_id: str, actor: DISPATCH_ACTOR):
    with closing(connect()) as db:
        cur = db.execute("UPDATE alerts SET acknowledged=1 WHERE id=?", (alert_id,))
        if not cur.rowcount:
            raise HTTPException(404, detail={"title": "Alert nicht gefunden."})
        log_audit(db, actor.subject, "alert.acknowledged", alert_id)
        db.commit()
        return fetch_one(db, "SELECT * FROM alerts WHERE id=?", (alert_id,))


@app.get("/api/v1/audit")
def get_audit(_: AUDIT_ACTOR, limit: Annotated[int, Query(ge=1, le=500)] = 100):
    with closing(connect()) as db:
        return fetch_all(db, "SELECT actor, action, entity, created_at FROM audit_log ORDER BY created_at DESC LIMIT ?", (limit,))


@app.websocket("/ws/v1/live")
async def live_socket(websocket: WebSocket, api_key: str = Query(default="")):
    protocols = websocket.scope.get("subprotocols", [])
    token_protocol = next((value for value in protocols if value.startswith("bearer.")), None)
    token = token_protocol.removeprefix("bearer.") if token_protocol else None
    try:
        await websocket_principal(token, api_key)
    except HTTPException:
        await websocket.close(code=1008)
        return
    await websocket.accept(subprotocol="nordroute" if "nordroute" in protocols else None)
    try:
        while True:
            with closing(connect()) as db:
                data = dashboard_data(db)
            await websocket.send_json(data)
            await asyncio.sleep(2)
    except WebSocketDisconnect:
        return
