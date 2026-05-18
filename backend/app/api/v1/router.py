from fastapi import APIRouter

from app.api.v1 import assignments, auth, cargo, companies, dashboard, drivers, trucks

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(companies.router)
api_router.include_router(trucks.router)
api_router.include_router(drivers.router)
api_router.include_router(cargo.router)
api_router.include_router(assignments.router)
api_router.include_router(dashboard.router)


@api_router.get("/ping")
async def ping() -> dict[str, str]:
    return {"pong": "tendr"}
