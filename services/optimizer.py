from __future__ import annotations

import math
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from ortools.constraint_solver import pywrapcp, routing_enums_pb2

from services.routing import RoadMatrix, road_geometry, road_matrix

ROUTE_DISTANCE_WEIGHT = int(os.getenv("ROUTE_DISTANCE_WEIGHT", "1"))
ROUTE_TIME_WEIGHT = int(os.getenv("ROUTE_TIME_WEIGHT", "8"))
UNASSIGNED_PENALTY = int(os.getenv("UNASSIGNED_ORDER_PENALTY", "50000000"))
MAX_OPTIMIZATION_LOCATIONS = int(os.getenv("MAX_OPTIMIZATION_LOCATIONS", "450"))


@dataclass(frozen=True)
class OptimizationResult:
    routes: list[dict[str, Any]]
    unassigned_order_ids: list[str]
    distance_km: float
    traffic_coverage: dict[str, int]
    solver: str


def _due_seconds(value: str, now: datetime) -> int:
    due = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if due.tzinfo is None:
        raise ValueError(f"Order due_at must include a timezone: {value}")
    return max(0, round((due.astimezone(timezone.utc) - now).total_seconds()))


async def optimize_routes(
    vehicles: list[dict[str, Any]],
    orders: list[dict[str, Any]],
    time_limit_seconds: int,
) -> OptimizationResult:
    if not orders or not vehicles:
        return OptimizationResult([], [order["id"] for order in orders], 0.0, {"live": 0, "missing": 0}, "OR-Tools")

    locations: list[tuple[float, float]] = [(v["lat"], v["lon"]) for v in vehicles]
    order_nodes: dict[str, tuple[int, int]] = {}
    for order in orders:
        pickup_index = len(locations)
        locations.append((order["pickup_lat"], order["pickup_lon"]))
        delivery_index = len(locations)
        locations.append((order["delivery_lat"], order["delivery_lon"]))
        order_nodes[order["id"]] = (pickup_index, delivery_index)
    if len(locations) > MAX_OPTIMIZATION_LOCATIONS:
        raise ValueError(
            f"Optimization requires {len(locations)} matrix locations; configured limit is "
            f"{MAX_OPTIMIZATION_LOCATIONS}. Increase MAX_OPTIMIZATION_LOCATIONS only after checking "
            "Valhalla memory and TomTom API quotas."
        )

    matrix: RoadMatrix = await road_matrix(locations)
    manager = pywrapcp.RoutingIndexManager(
        len(locations),
        len(vehicles),
        list(range(len(vehicles))),
        list(range(len(vehicles))),
    )
    routing = pywrapcp.RoutingModel(manager)

    def distance_callback(from_index: int, to_index: int) -> int:
        source = manager.IndexToNode(from_index)
        target = manager.IndexToNode(to_index)
        return matrix.distances_m[source][target]

    def time_callback(from_index: int, to_index: int) -> int:
        source = manager.IndexToNode(from_index)
        target = manager.IndexToNode(to_index)
        return matrix.traffic_times_s[source][target]

    time_callback_index = routing.RegisterTransitCallback(time_callback)

    def weighted_cost(from_index: int, to_index: int) -> int:
        distance = distance_callback(from_index, to_index)
        travel_time = time_callback(from_index, to_index)
        if distance >= 1_000_000_000 or travel_time >= 1_000_000_000:
            return 1_000_000_000
        return ROUTE_DISTANCE_WEIGHT * distance + ROUTE_TIME_WEIGHT * travel_time

    cost_callback_index = routing.RegisterTransitCallback(weighted_cost)
    routing.SetArcCostEvaluatorOfAllVehicles(cost_callback_index)

    weight_demands = [0] * len(locations)
    volume_demands = [0] * len(locations)
    for order in orders:
        pickup_index, delivery_index = order_nodes[order["id"]]
        weight_demands[pickup_index] = round(order["weight_kg"])
        weight_demands[delivery_index] = -round(order["weight_kg"])
        volume_demands[pickup_index] = round(order["volume_m3"] * 100)
        volume_demands[delivery_index] = -round(order["volume_m3"] * 100)

    def add_capacity_dimension(demands: list[int], capacities: list[int], name: str) -> None:
        def demand_callback(index: int) -> int:
            return demands[manager.IndexToNode(index)]

        callback_index = routing.RegisterUnaryTransitCallback(demand_callback)
        routing.AddDimensionWithVehicleCapacity(callback_index, 0, capacities, True, name)

    add_capacity_dimension(
        weight_demands,
        [round(vehicle["max_weight_kg"]) for vehicle in vehicles],
        "CargoWeightKg",
    )
    add_capacity_dimension(
        volume_demands,
        [round(vehicle["max_volume_m3"] * 100) for vehicle in vehicles],
        "CargoVolumeCentiM3",
    )

    routing.AddDimension(time_callback_index, 6 * 60 * 60, 36 * 60 * 60, False, "ArrivalTime")
    arrival_dimension = routing.GetDimensionOrDie("ArrivalTime")
    now = datetime.now(timezone.utc)
    for vehicle_index in range(len(vehicles)):
        start = routing.Start(vehicle_index)
        arrival_dimension.CumulVar(start).SetRange(0, 36 * 60 * 60)

    routing.AddDimension(
        time_callback_index,
        0,
        9 * 60 * 60,
        True,
        "DailyDrivingTime",
    )
    drive_dimension = routing.GetDimensionOrDie("DailyDrivingTime")
    solver = routing.solver()
    for vehicle_index, vehicle in enumerate(vehicles):
        remaining_drive_seconds = max(0, (9 * 60 - int(vehicle["driven_minutes"])) * 60)
        drive_dimension.CumulVar(routing.End(vehicle_index)).SetMax(remaining_drive_seconds)

    for order in orders:
        pickup_node, delivery_node = order_nodes[order["id"]]
        pickup = manager.NodeToIndex(pickup_node)
        delivery = manager.NodeToIndex(delivery_node)
        due_seconds = _due_seconds(order["due_at"], now)
        arrival_dimension.CumulVar(pickup).SetRange(0, due_seconds)
        arrival_dimension.CumulVar(delivery).SetRange(0, due_seconds)
        routing.AddPickupAndDelivery(pickup, delivery)
        solver.Add(routing.VehicleVar(pickup) == routing.VehicleVar(delivery))
        solver.Add(arrival_dimension.CumulVar(pickup) <= arrival_dimension.CumulVar(delivery))
        routing.AddDisjunction([pickup, delivery], UNASSIGNED_PENALTY, 2)

    parameters = pywrapcp.DefaultRoutingSearchParameters()
    parameters.first_solution_strategy = routing_enums_pb2.FirstSolutionStrategy.PARALLEL_CHEAPEST_INSERTION
    parameters.local_search_metaheuristic = routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH
    parameters.time_limit.FromSeconds(time_limit_seconds)
    parameters.log_search = False
    solution = routing.SolveWithParameters(parameters)
    if solution is None:
        raise RuntimeError("OR-Tools could not construct a feasible proposal for the configured hard constraints.")

    routes: list[dict[str, Any]] = []
    assigned: set[str] = set()
    total_distance_m = 0
    for vehicle_index, vehicle in enumerate(vehicles):
        index = routing.Start(vehicle_index)
        node_sequence: list[int] = []
        driving_seconds = 0
        distance_m = 0
        previous_node = manager.IndexToNode(index)
        while not routing.IsEnd(index):
            index = solution.Value(routing.NextVar(index))
            node = manager.IndexToNode(index)
            node_sequence.append(node)
            distance_m += matrix.distances_m[previous_node][node]
            driving_seconds += matrix.traffic_times_s[previous_node][node]
            previous_node = node
        stops = []
        order_ids: list[str] = []
        for node in node_sequence:
            for order_id, (pickup_node, delivery_node) in order_nodes.items():
                if node == pickup_node:
                    assigned.add(order_id)
                    order_ids.append(order_id)
                    stops.append({"order_id": order_id, "type": "pickup", "point": list(locations[node])})
                elif node == delivery_node:
                    stops.append({"order_id": order_id, "type": "delivery", "point": list(locations[node])})
        if not order_ids:
            continue

        node_path = [vehicle_index, *node_sequence]
        geometry = await road_geometry([locations[node] for node in node_path])
        distance_km = distance_m / 1000
        fuel_l = distance_km * 0.30
        co2_kg = fuel_l * 2.68
        drive_minutes = round(driving_seconds / 60)
        break_minutes = max(0, math.ceil(driving_seconds / (4.5 * 60 * 60)) - 1) * 45
        routes.append(
            {
                "vehicle_id": vehicle["id"],
                "order_ids": order_ids,
                "distance_km": round(distance_km, 1),
                "travel_minutes": drive_minutes,
                "fuel_l": round(fuel_l, 1),
                "co2_kg": round(co2_kg, 1),
                "toll_eur": 0.0,
                "break_minutes": break_minutes,
                "geometry": geometry,
                "stops": stops,
                "traffic_factor": matrix.traffic_factors[vehicle_index],
            }
        )
        total_distance_m += distance_m

    return OptimizationResult(
        routes=routes,
        unassigned_order_ids=[order["id"] for order in orders if order["id"] not in assigned],
        distance_km=round(total_distance_m / 1000, 1),
        traffic_coverage={"live": matrix.live_traffic_points, "missing": matrix.missing_traffic_points},
        solver="OR-Tools RoutingModel (Guided Local Search)",
    )
