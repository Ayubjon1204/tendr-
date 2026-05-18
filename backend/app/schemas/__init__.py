from app.schemas.assignment import (
    AssignmentCreate,
    AssignmentOut,
    AssignmentUpdate,
    AutoAssignRequest,
    AutoAssignResult,
)
from app.schemas.auth import LoginRequest, TokenResponse
from app.schemas.cargo import CargoCreate, CargoOut, CargoUpdate
from app.schemas.common import GeoPoint, Pagination
from app.schemas.company import CompanyCreate, CompanyOut, CompanyUpdate
from app.schemas.dashboard import (
    BackHaulOpportunity,
    DashboardSummary,
    IdleTruck,
    UrgentCargo,
)
from app.schemas.driver import DriverCreate, DriverOut, DriverUpdate
from app.schemas.truck import TruckCreate, TruckLocationUpdate, TruckOut, TruckUpdate
from app.schemas.user import UserCreate, UserOut

__all__ = [
    "AssignmentCreate",
    "AssignmentOut",
    "AssignmentUpdate",
    "AutoAssignRequest",
    "AutoAssignResult",
    "BackHaulOpportunity",
    "CargoCreate",
    "CargoOut",
    "CargoUpdate",
    "CompanyCreate",
    "CompanyOut",
    "CompanyUpdate",
    "DashboardSummary",
    "DriverCreate",
    "DriverOut",
    "DriverUpdate",
    "GeoPoint",
    "IdleTruck",
    "LoginRequest",
    "Pagination",
    "TokenResponse",
    "TruckCreate",
    "TruckLocationUpdate",
    "TruckOut",
    "TruckUpdate",
    "UrgentCargo",
    "UserCreate",
    "UserOut",
]
