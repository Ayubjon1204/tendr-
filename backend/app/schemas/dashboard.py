from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class DashboardSummary(BaseModel):
    total_trucks: int
    available_trucks: int
    busy_trucks: int
    off_duty_trucks: int

    new_cargo: int
    assigned_cargo: int
    in_transit_cargo: int
    delivered_today: int

    pending_assignments: int
    active_carriers: int
    active_shippers: int

    fleet_utilization_pct: float


class IdleTruck(BaseModel):
    truck_id: UUID
    plate_number: str
    carrier_name: str
    idle_since: datetime | None
    last_location_address: str | None
    hours_idle: float


class UrgentCargo(BaseModel):
    cargo_id: UUID
    reference_code: str
    origin_address: str
    destination_address: str
    weight_kg: int
    delivery_deadline: datetime
    hours_until_deadline: float
    has_assignment: bool


class BackHaulOpportunity(BaseModel):
    truck_id: UUID
    plate_number: str
    arriving_at_address: str
    arriving_at: datetime
    nearby_cargo_id: UUID
    nearby_cargo_reference: str
    nearby_cargo_origin: str
    distance_km: float
