"""Avtomatik yuk biriktirish servisi.

MVP yondashuvi: **greedy + scoring**.
VRP (vehicle routing) Phase 4'da Yandex Routing API bilan keladi.

Algoritm (yangi yuk uchun):
1. Filter — yukga mos mashinalarni topish (capacity, body_type, sxedjul, active)
2. Score — har bir nomzodga ball berish (yaqinlik, sig'im samaradorligi,
   back-haul potensiali, jadval bo'shligi)
3. Top-N nomzod qaytarish; eng yaxshisi `chosen` bo'lib biriktiriladi

Score komponentlari (yuqori = yaxshi):
- distance_score:    yaqinroq pickup'ga = yaxshi
- capacity_score:    kerakli sig'imga yaqin = yaxshi (uloqdek katta mashinani
                     kichik yukga qo'yish — empty volume isrofi)
- schedule_score:    pickup_window'ga mos = yaxshi
- backhaul_score:    truck home_base destination'ga yaqin bo'lsa = bonus

Eslatma: bu skor — 30 yillik logistika qoidasi:
- 100 km bo'sh yurish = 1 ta past-marja yuk daromadi
- Shuning uchun distance og'irligi katta (bo'sh probeg = pul yo'qotish)
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import NamedTuple
from uuid import UUID

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.assignment import Assignment, AssignmentSource, AssignmentStatus
from app.models.cargo import Cargo, CargoStatus
from app.models.truck import Truck, TruckStatus
from app.models.truck_schedule import ScheduleKind, TruckSchedule
from app.schemas.assignment import AutoAssignResult, TruckCandidate
from app.schemas.common import GeoPoint
from app.services.geo import (
    estimate_drive_hours,
    haversine_km,
    geopoint_to_wkt,
    wkb_to_geopoint,
)

# Hardcoded knobs — keyinchalik DB sozlamasiga ko'chiriladi
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
    max_results: int = 5,
) -> list[ScoredCandidate]:
    """Yukga mos eng yaxshi mashinalarni topish."""
    pickup = wkb_to_geopoint(cargo.origin_location)
    destination = wkb_to_geopoint(cargo.destination_location)
    if pickup is None or destination is None:
        return []

    # 1. Asosiy filter: active, yetarli sig'im, body_type mos
    stmt = (
        select(Truck)
        .where(
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
    """Bitta truck'ni baholash. None qaytarsa — biriktirib bo'lmaydi."""
    reasons: list[str] = []

    truck_loc = wkb_to_geopoint(truck.current_location)
    if truck_loc is None:
        # Joylashuv noma'lum — home_base'dan foydalanamiz
        truck_loc = wkb_to_geopoint(truck.home_base_location)
        if truck_loc is None:
            return None
        reasons.append("joylashuv noma'lum, home_base ishlatildi")

    distance_km = haversine_km(truck_loc, pickup)
    if distance_km > MAX_PICKUP_DISTANCE_KM:
        return None  # Juda uzoq — yuborish foydasiz

    # 2. Schedule conflict tekshirish
    if _has_schedule_conflict(truck, cargo.pickup_window_start, cargo.delivery_deadline):
        return None
    reasons.append("jadval bo'sh")

    # 3. Mashina pickup_window boshlanguncha yetib bora oladimi?
    drive_hours = estimate_drive_hours(distance_km)
    can_arrive_by = datetime.now(tz=timezone.utc) + timedelta(hours=drive_hours)
    if can_arrive_by > cargo.pickup_window_end:
        return None
    if can_arrive_by <= cargo.pickup_window_end:
        reasons.append(f"~{drive_hours:.1f} soatda yetib boradi")

    # --- Score komponentlari ---
    # Distance score: 1.0 (yaqin) -> 0.0 (uzoq)
    distance_score = max(0.0, 1.0 - distance_km / MAX_PICKUP_DISTANCE_KM)

    # Capacity score: 1.0 (aniq mos) -> 0.0 (juda katta)
    # 30 yillik qoida: 80% sig'im to'ldirilsa optimal
    fill_ratio = cargo.weight_kg / truck.capacity_kg
    if fill_ratio >= 0.8:
        capacity_score = 1.0
        reasons.append(f"sig'im {fill_ratio:.0%} to'ladi")
    elif fill_ratio >= 0.5:
        capacity_score = 0.7
    else:
        capacity_score = 0.3
        reasons.append(f"sig'im atigi {fill_ratio:.0%} — katta mashina")

    # Schedule score: pickup_window keng bo'lsa yaxshi
    window_hours = (cargo.pickup_window_end - cargo.pickup_window_start).total_seconds() / 3600
    schedule_score = min(1.0, window_hours / 8.0)

    # Backhaul score: home_base destination'ga yaqinmi?
    backhaul_score = 0.0
    home_base = wkb_to_geopoint(truck.home_base_location)
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
    """Truck jadvalida mavjud band/dam vaqtlar bilan to'qnashuv borligini tekshirish."""
    for entry in truck.schedules:
        if entry.kind == ScheduleKind.WORK:
            continue  # ish vaqti — to'qnashuv emas
        # Overlap: NOT (end <= start_existing OR start >= end_existing)
        if not (window_end <= entry.start_at or window_start >= entry.end_at):
            return True
    return False


async def auto_assign_cargo(
    db: AsyncSession,
    cargo_id: UUID,
    max_candidates: int = 5,
    create_assignment: bool = True,
) -> AutoAssignResult:
    """Yukni avtomatik biriktirish — eng yaxshi mashinaga.

    `create_assignment=False` bo'lsa — faqat nomzodlarni qaytaradi (dry-run).
    """
    cargo = await db.scalar(
        select(Cargo).where(Cargo.id == cargo_id)
    )
    if cargo is None:
        return AutoAssignResult(cargo_id=cargo_id, message="Yuk topilmadi")
    if cargo.status != CargoStatus.NEW:
        return AutoAssignResult(
            cargo_id=cargo_id,
            message=f"Yuk holati '{cargo.status.value}' — faqat 'new' uchun avto-biriktirish",
        )

    candidates = await find_candidates_for_cargo(db, cargo, max_results=max_candidates)
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

    # Eng yaxshi nomzodga biriktirish yaratish
    best = candidates[0]
    pickup_planned = max(
        cargo.pickup_window_start,
        datetime.now(tz=timezone.utc)
        + timedelta(hours=estimate_drive_hours(best.distance_to_pickup_km)),
    )
    delivery_distance = haversine_km(
        wkb_to_geopoint(cargo.origin_location),  # type: ignore[arg-type]
        wkb_to_geopoint(cargo.destination_location),  # type: ignore[arg-type]
    )
    delivery_planned = pickup_planned + timedelta(
        hours=estimate_drive_hours(delivery_distance) + 2  # +2 yuklash/tushirish vaqti
    )

    assignment = Assignment(
        cargo_id=cargo.id,
        truck_id=best.truck.id,
        driver_id=None,  # Driver — keyinchalik dispatcher tasdiqlashida
        status=AssignmentStatus.PROPOSED,
        assigned_by=AssignmentSource.SYSTEM,
        planned_pickup_at=pickup_planned,
        planned_delivery_at=delivery_planned,
        optimization_score=best.score,  # type: ignore[arg-type]
        notes=" | ".join(best.reasons),
    )
    db.add(assignment)

    # Cargo statusini yangilash
    cargo.status = CargoStatus.ASSIGNED
    # Truck statusini reserve (busy emas — hali jo'natilmagan)
    # busy bo'lishi assignment ACCEPTED bo'lganda

    # Schedule ga qo'shish
    schedule_entry = TruckSchedule(
        truck_id=best.truck.id,
        start_at=pickup_planned,
        end_at=delivery_planned,
        kind=ScheduleKind.ASSIGNMENT,
        assignment_id=assignment.id,
    )
    db.add(schedule_entry)

    await db.flush()  # ID lar uchun
    await db.commit()
    await db.refresh(assignment)

    return AutoAssignResult(
        cargo_id=cargo_id,
        chosen=cand_list[0],
        candidates=cand_list,
        assignment_id=assignment.id,
        message=f"Biriktirildi: {best.truck.plate_number} (score {best.score})",
    )
