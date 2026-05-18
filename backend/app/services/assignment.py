"""Avtomatik truck biriktirish servisi (carrier ichida).

Phase 2 refactor: endi `carrier_id` majburiy — bu carrier ichidagi truck'larga
biriktiradi.

Full lifecycle (factory distribution → carrier accept → truck assignment) Phase 4'da.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import NamedTuple
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.assignment import Assignment, AssignmentSource, AssignmentStatus
from app.models.cargo import Cargo, CargoStatus
from app.models.truck import Truck, TruckStatus
from app.models.truck_schedule import ScheduleKind, TruckSchedule
from app.schemas.assignment import AutoAssignResult, TruckCandidate
from app.schemas.common import GeoPoint
from app.services.geo import (
    coords_to_geopoint,
    estimate_drive_hours,
    haversine_km,
)

MAX_PICKUP_DISTANCE_KM = 500.0
DISTANCE_WEIGHT = 1.0
CAPACITY_WEIGHT = 0.5
SCHEDULE_WEIGHT = 0.7
BACKHAUL_WEIGHT = 0.3


class ScoredCandidate(NamedTuple):
    truck: Truck
    score: float
    distance_to_pickup_km: float
    reasons: list[str]


async def find_candidates_for_cargo(
    db: AsyncSession,
    cargo: Cargo,
    carrier_id: UUID,
    max_results: int = 5,
) -> list[ScoredCandidate]:
    """Berilgan carrier'ning fleet ichidan yukga mos truck'larni topish."""
    pickup = coords_to_geopoint(cargo.origin_lat, cargo.origin_lng)
    destination = coords_to_geopoint(cargo.destination_lat, cargo.destination_lng)
    if pickup is None or destination is None:
        return []

    stmt = (
        select(Truck)
        .where(
            Truck.carrier_id == carrier_id,
            Truck.is_active.is_(True),
            Truck.status.in_([TruckStatus.AVAILABLE, TruckStatus.UNLOADING]),
            Truck.capacity_kg >= cargo.weight_kg,
        )
        .options(selectinload(Truck.schedules))
    )
    if cargo.required_body_type is not None:
        stmt = stmt.where(Truck.body_type == cargo.required_body_type)

    trucks = (await db.scalars(stmt)).all()

    scored: list[ScoredCandidate] = []
    for truck in trucks:
        cand = _score_truck(truck, cargo, pickup, destination)
        if cand is not None:
            scored.append(cand)

    scored.sort(key=lambda c: c.score, reverse=True)
    return scored[:max_results]


def _score_truck(
    truck: Truck,
    cargo: Cargo,
    pickup: GeoPoint,
    destination: GeoPoint,
) -> ScoredCandidate | None:
    reasons: list[str] = []

    truck_loc = coords_to_geopoint(truck.current_lat, truck.current_lng)
    if truck_loc is None:
        truck_loc = coords_to_geopoint(truck.home_base_lat, truck.home_base_lng)
        if truck_loc is None:
            return None
        reasons.append("joylashuv noma'lum, home_base ishlatildi")

    distance_km = haversine_km(truck_loc, pickup)
    if distance_km > MAX_PICKUP_DISTANCE_KM:
        return None

    if _has_schedule_conflict(truck, cargo.pickup_window_start, cargo.delivery_deadline):
        return None
    reasons.append("jadval bo'sh")

    drive_hours = estimate_drive_hours(distance_km)
    can_arrive_by = datetime.now(tz=timezone.utc) + timedelta(hours=drive_hours)
    if can_arrive_by > cargo.pickup_window_end:
        return None
    reasons.append(f"~{drive_hours:.1f} soatda yetib boradi")

    distance_score = max(0.0, 1.0 - distance_km / MAX_PICKUP_DISTANCE_KM)

    fill_ratio = cargo.weight_kg / truck.capacity_kg
    if fill_ratio >= 0.8:
        capacity_score = 1.0
        reasons.append(f"sig'im {fill_ratio:.0%} to'ladi")
    elif fill_ratio >= 0.5:
        capacity_score = 0.7
    else:
        capacity_score = 0.3
        reasons.append(f"sig'im atigi {fill_ratio:.0%} — katta mashina")

    window_hours = (cargo.pickup_window_end - cargo.pickup_window_start).total_seconds() / 3600
    schedule_score = min(1.0, window_hours / 8.0)

    backhaul_score = 0.0
    home_base = coords_to_geopoint(truck.home_base_lat, truck.home_base_lng)
    if home_base is not None:
        home_to_dest_km = haversine_km(home_base, destination)
        if home_to_dest_km < 100:
            backhaul_score = 1.0
            reasons.append("uy bazasi destination'ga yaqin")
        elif home_to_dest_km < 300:
            backhaul_score = 0.5

    total = (
        DISTANCE_WEIGHT * distance_score
        + CAPACITY_WEIGHT * capacity_score
        + SCHEDULE_WEIGHT * schedule_score
        + BACKHAUL_WEIGHT * backhaul_score
    )

    return ScoredCandidate(
        truck=truck,
        score=round(total, 4),
        distance_to_pickup_km=round(distance_km, 2),
        reasons=reasons,
    )


def _has_schedule_conflict(
    truck: Truck, window_start: datetime, window_end: datetime
) -> bool:
    for entry in truck.schedules:
        if entry.kind == ScheduleKind.WORK:
            continue
        if not (window_end <= entry.start_at or window_start >= entry.end_at):
            return True
    return False


async def auto_assign_cargo(
    db: AsyncSession,
    cargo_id: UUID,
    carrier_id: UUID,
    max_candidates: int = 5,
    create_assignment: bool = True,
) -> AutoAssignResult:
    """Yukni carrier ichida eng yaxshi mashinaga avto-biriktirish."""
    cargo = await db.scalar(select(Cargo).where(Cargo.id == cargo_id))
    if cargo is None:
        return AutoAssignResult(cargo_id=cargo_id, message="Yuk topilmadi")

    candidates = await find_candidates_for_cargo(
        db, cargo, carrier_id, max_results=max_candidates
    )
    if not candidates:
        return AutoAssignResult(
            cargo_id=cargo_id,
            message="Mos mashina topilmadi (sig'im/body_type/masofa/jadval bo'yicha)",
            candidates=[],
        )

    cand_list = [
        TruckCandidate(
            truck_id=c.truck.id,
            plate_number=c.truck.plate_number,
            score=c.score,
            distance_to_pickup_km=c.distance_to_pickup_km,
            capacity_kg=c.truck.capacity_kg,
            body_type=c.truck.body_type.value,
            reasons=c.reasons,
        )
        for c in candidates
    ]

    if not create_assignment:
        return AutoAssignResult(
            cargo_id=cargo_id,
            chosen=cand_list[0],
            candidates=cand_list,
            message="Dry-run — biriktirish yaratilmadi",
        )

    best = candidates[0]
    pickup_planned = max(
        cargo.pickup_window_start,
        datetime.now(tz=timezone.utc)
        + timedelta(hours=estimate_drive_hours(best.distance_to_pickup_km)),
    )
    origin_gp = coords_to_geopoint(cargo.origin_lat, cargo.origin_lng)
    dest_gp = coords_to_geopoint(cargo.destination_lat, cargo.destination_lng)
    delivery_distance = haversine_km(origin_gp, dest_gp) if origin_gp and dest_gp else 0  # type: ignore[arg-type]
    delivery_planned = pickup_planned + timedelta(
        hours=estimate_drive_hours(delivery_distance) + 2
    )

    assignment = Assignment(
        cargo_id=cargo.id,
        carrier_id=carrier_id,
        truck_id=best.truck.id,
        driver_id=None,
        status=AssignmentStatus.PROPOSED,
        assigned_by=AssignmentSource.SYSTEM,
        planned_pickup_at=pickup_planned,
        planned_delivery_at=delivery_planned,
        optimization_score=best.score,  # type: ignore[arg-type]
        notes=" | ".join(best.reasons),
    )
    db.add(assignment)
    cargo.status = CargoStatus.ASSIGNED_TRUCK

    schedule_entry = TruckSchedule(
        truck_id=best.truck.id,
        start_at=pickup_planned,
        end_at=delivery_planned,
        kind=ScheduleKind.ASSIGNMENT,
        assignment_id=assignment.id,
    )
    db.add(schedule_entry)

    await db.flush()
    await db.commit()
    await db.refresh(assignment)

    return AutoAssignResult(
        cargo_id=cargo_id,
        chosen=cand_list[0],
        candidates=cand_list,
        assignment_id=assignment.id,
        message=f"Biriktirildi: {best.truck.plate_number} (score {best.score})",
    )
