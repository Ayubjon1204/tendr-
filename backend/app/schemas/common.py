from typing import Annotated, Any

from pydantic import BaseModel, BeforeValidator, Field


class GeoPoint(BaseModel):
    lat: float = Field(..., ge=-90, le=90, description="Latitude")
    lng: float = Field(..., ge=-180, le=180, description="Longitude")


def _convert_geo(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, GeoPoint):
        return value
    if isinstance(value, dict):
        return value
    # PostGIS WKBElement -> dict
    try:
        from geoalchemy2.elements import WKBElement
        from geoalchemy2.shape import to_shape

        if isinstance(value, WKBElement):
            point = to_shape(value)
            return {"lat": point.y, "lng": point.x}
    except ImportError:
        pass
    return value


GeoPointOrNone = Annotated[GeoPoint | None, BeforeValidator(_convert_geo)]
GeoPointReq = Annotated[GeoPoint, BeforeValidator(_convert_geo)]


class Pagination(BaseModel):
    page: int = Field(1, ge=1)
    size: int = Field(50, ge=1, le=500)

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.size
