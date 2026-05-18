"""Dashboard endpointlar — dispatcher uchun "nima qilish kerak" ko'rsatmalari.

30 yillik logistika qoidasi:
- Dispatcher har soatda kamida 1 marta dashboard'ga qaraydi
- Qaragach 30 soniyada qaror qabul qilishi kerak
- Shuning uchun har endpoint **action-oriented** — "shu mashinaga qara" yoki
  "shu yukni biriktir" deydi, oddiy statistik ko'rsatmaslik kerak
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Query
from sqlalchemy import and_, func, or_, select

from app.api.deps import CurrentUser, DbSession
from app.models.assignment import Assignment, AssignmentStatus
from app.models.cargo import Cargo, CargoStatus
from app.models.company import Company, CompanyKind
from app.models.truck import Truck, TruckStatus
from app.schemas.dashboard import (
    BackHaulOpportunity,
    DashboardSummary,
    IdleTruck,
    UrgentCargo,
)
from app.services.geo import coords_to_geopoint, haversine_km

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/summary", response_model=DashboardSummary)
async def get_summary(db: DbSession, _user: CurrentUser) -> DashboardSummary:
    now = datetime.now(tz=timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

    total_trucks = await db.scalar(
        select(func.count(Truck.id)).where(Truck.is_active.is_(True))
    ) or 0
    available = await db.scalar(
        select(func.count(Truck.id)).where(
            Truck.is_active.is_(True), Truck.status == TruckStatus.AVAILABLE
        )
    ) or 0
    busy = await db.scalar(
        select(func.count(Truck.id)).where(
            Truck.is_active.is_(True),
            Truck.status.in_(
                [TruckStatus.BUSY, TruckStatus.LOADING, TruckStatus.UNLOADING]
            ),
        )
    ) or 0
    off_duty = await db.scalar(
        select(func.count(Truck.id)).where(
            Truck.is_active.is_(True),
            Truck.status.in_([TruckStatus.OFF_DUTY, TruckStatus.MAINTENANCE]),
        )
    ) or 0

    new_cargo = await db.scalar(
        select(func.count(Cargo.id)).where(Cargo.status == CargoStatus.NEW)
    ) or 0
    assigned_cargo = await db.scalar(
        select(func.count(Cargo.id)).where(
            Cargo.status.in_(
                [CargoStatus.CARRIER_ACCEPTED, CargoStatus.ASSIGNED_TRUCK]
            )
        )
    ) or 0
    in_transit = await db.scalar(
        select(func.count(Cargo.id)).where(Cargo.status == CargoStatus.IN_TRANSIT)
    ) or 0
    delivered_today = await db.scalar(
        select(func.count(Cargo.id)).where(
            Cargo.status == CargoStatus.DELIVERED, Cargo.updated_at >= today_start
        )
    ) or 0

    pending = await db.scalar(
        select(func.count(Assignment.id)).where(
            Assignment.status.in_(
                [AssignmentStatus.PROPOSED, AssignmentStatus.ACCEPTED]
            )
        )
    ) or 0

    carriers = await db.scalar(
        select(func.count(Company.id)).where(
            Company.kind == CompanyKind.CARRIER, Company.is_active.is_(True)
        )
    ) or 0
    factories = await db.scalar(
        select(func.count(Company.id)).where(
            Company.kind == CompanyKind.FACTORY, Company.is_active.is_(True)
        )
    ) or 0
    distributors = await db.scalar(
        select(func.count(Company.id)).where(
            Company.kind == CompanyKind.DISTRIBUTOR, Company.is_active.is_(True)
        )
    ) or 0

    # Fleet utilization: busy / total. Available ham "kutmoqda" — utilization emas.
    utilization = (busy / total_trucks * 100) if total_trucks else 0.0

    return DashboardSummary(
        total_trucks=total_trucks,
        available_trucks=available,
        busy_trucks=busy,
        off_duty_trucks=off_duty,
        new_cargo=new_cargo,
        assigned_cargo=assigned_cargo,
        in_transit_cargo=in_transit,
        delivered_today=delivered_today,
        pending_assignments=pending,
        active_carriers=carriers,
        active_factories=factories,
        active_distributors=distributors,
        fleet_utilization_pct=round(utilization, 1),
    )


@router.get("/idle-trucks", response_model=list[IdleTruck])
async def get_idle_trucks(
    db: DbSession,
    _user: CurrentUser,
    hours_threshold: float = Query(2.0, ge=0, le=72),
) -> list[IdleTruck]:
    """`hours_threshold` soatdan ko'p vaqt davomida bo'sh turgan mashinalar.
    Dispatcher uchun ogohlantirish — yo'q bo'lsa hammasi yaxshi."""
    now = datetime.now(tz=timezone.utc)
    cutoff = now - timedelta(hours=hours_threshold)

    stmt = (
        select(Truck, Company.name)
        .join(Company, Truck.carrier_id == Company.id)
        .where(
            Truck.is_active.is_(True),
            Truck.status == TruckStatus.AVAILABLE,
            or_(
                Truck.updated_at < cutoff,
                Truck.updated_at.is_(None),
            ),
        )
        .order_by(Truck.updated_at.asc().nulls_first())
        .limit(100)
    )
    rows = (await db.execute(stmt)).all()

    result: list[IdleTruck] = []
    for truck, carrier_name in rows:
        idle_since = truck.updated_at
        hours = (now - idle_since).total_seconds() / 3600 if idle_since else 999.0
        result.append(
            IdleTruck(
                truck_id=truck.id,
                plate_number=truck.plate_number,
                carrier_name=carrier_name,
                idle_since=idle_since,
                last_location_address=None,  # Geocoding Phase 5'da
                hours_idle=round(hours, 1),
            )
        )
    return result


@router.get("/urgent-cargo", response_model=list[UrgentCargo])
async def get_urgent_cargo(
    db: DbSession,
    _user: CurrentUser,
    hours_window: float = Query(24.0, ge=1, le=168),
) -> list[UrgentCargo]:
    """`hours_window` soat ichida muddat tugaydigan yuklar."""
    now = datetime.now(tz=timezone.utc)
    deadline_cutoff = now + timedelta(hours=hours_window)

    stmt = (
        select(Cargo)
        .where(
            Cargo.status.in_(
                [
                    CargoStatus.NEW,
                    CargoStatus.DISTRIBUTED,
                    CargoStatus.CARRIER_ACCEPTED,
                    CargoStatus.ASSIGNED_TRUCK,
                ]
            ),
            Cargo.delivery_deadline <= deadline_cutoff,
        )
        .order_by(Cargo.delivery_deadline.asc())
        .limit(100)
    )
    cargos = (await db.scalars(stmt)).all()

    # Aktiv assignment bormi tekshirish (batch)
    if not cargos:
        return []
    cargo_ids = [c.id for c in cargos]
    active_assigns_stmt = select(Assignment.cargo_id).where(
        Assignment.cargo_id.in_(cargo_ids),
        Assignment.status.in_(
            [AssignmentStatus.PROPOSED, AssignmentStatus.ACCEPTED,
             AssignmentStatus.IN_PROGRESS]
        ),
    )
    with_assigns = set((await db.scalars(active_assigns_stmt)).all())

    result: list[UrgentCargo] = []
    for c in cargos:
        hours_left = (c.delivery_deadline - now).total_seconds() / 3600
        result.append(
            UrgentCargo(
                cargo_id=c.id,
                reference_code=c.reference_code,
                origin_address=c.origin_address,
                destination_address=c.destination_address,
                weight_kg=c.weight_kg,
                delivery_deadline=c.delivery_deadline,
                hours_until_deadline=round(hours_left, 1),
                has_assignment=c.id in with_assigns,
            )
        )
    return result


@router.get("/back-haul", response_model=list[BackHaulOpportunity])
async def get_backhaul_opportunities(
    db: DbSession,
    _user: CurrentUser,
    radius_km: float = Query(50.0, ge=1, le=500),
) -> list[BackHaulOpportunity]:
    """Yetkazib bergan/borayotgan mashinalar yaqinida yangi yuklar bormi.

    Klassik back-haul matching: A→B yetkazib borayotgan mashina B yaqinida
    yangi B→C yuk topadi va bo'sh qaytmaydi.

    Bu Phase 2 uchun **soddalashtirilgan**: faqat IN_PROGRESS yoki recently
    DELIVERED assignment'larni va yaqin atrofdagi yangi cargo'larni mos qiladi.
    To'liq matching Phase 4'da OR-Tools'da.
    """
    now = datetime.now(tz=timezone.utc)
    recent = now - timedelta(hours=24)

    # Yetkazib berishga yaqin yoki yangi tushirilgan assignment'lar
    stmt = (
        select(Assignment, Cargo, Truck)
        .join(Cargo, Assignment.cargo_id == Cargo.id)
        .join(Truck, Assignment.truck_id == Truck.id)
        .where(
            or_(
                Assignment.status == AssignmentStatus.IN_PROGRESS,
                and_(
                    Assignment.status == AssignmentStatus.COMPLETED,
                    Assignment.actual_delivery_at >= recent,
                ),
            ),
        )
        .limit(200)
    )
    rows = (await db.execute(stmt)).all()
    if not rows:
        return []

    # Yangi yuklar — biriktirilmagan
    new_cargo_stmt = select(Cargo).where(Cargo.status == CargoStatus.NEW).limit(500)
    new_cargos = (await db.scalars(new_cargo_stmt)).all()

    opportunities: list[BackHaulOpportunity] = []
    for assignment, cargo, truck in rows:
        dest = coords_to_geopoint(cargo.destination_lat, cargo.destination_lng)
        if dest is None:
            continue
        for new_c in new_cargos:
            origin = coords_to_geopoint(new_c.origin_lat, new_c.origin_lng)
            if origin is None:
                continue
            dist = haversine_km(dest, origin)
            if dist > radius_km:
                continue
            opportunities.append(
                BackHaulOpportunity(
                    truck_id=truck.id,
                    plate_number=truck.plate_number,
                    arriving_at_address=cargo.destination_address,
                    arriving_at=assignment.planned_delivery_at,
                    nearby_cargo_id=new_c.id,
                    nearby_cargo_reference=new_c.reference_code,
                    nearby_cargo_origin=new_c.origin_address,
                    distance_km=round(dist, 2),
                )
            )

    opportunities.sort(key=lambda o: o.distance_km)
    return opportunities[:50]
