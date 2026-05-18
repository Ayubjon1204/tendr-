"""Geo utilities.

Haversine — buyuk doira (great-circle) bo'yicha masofa.
PostGIS bilan ishlash uchun helper'lar.

Hozircha haqiqiy yo'l masofasi (routing) yo'q — Yandex Routing API Phase 5'da.
Haversine ~30% kam, lekin nisbiy taqqoslash uchun yetarli (eng yaqin truck'ni
topish kabi nisbiy operatsiyalar uchun aniq routing shart emas).
"""
from __future__ import annotations

import math
from typing import Any

from geoalchemy2.elements import WKBElement
from geoalchemy2.shape import to_shape

from app.schemas.common import GeoPoint

EARTH_RADIUS_KM = 6371.0088


def haversine_km(a: GeoPoint, b: GeoPoint) -> float:
    """Two geo-points orasidagi masofa (km)."""
    lat1, lon1 = math.radians(a.lat), math.radians(a.lng)
    lat2, lon2 = math.radians(b.lat), math.radians(b.lng)
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    h = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    c = 2 * math.asin(math.sqrt(h))
    return EARTH_RADIUS_KM * c


def estimate_drive_hours(distance_km: float, avg_speed_kmh: float = 60.0) -> float:
    """Yo'l vaqti taxminiy. O'zbekiston shartida ~60 km/soat realistik o'rtacha."""
    return distance_km / avg_speed_kmh


def wkb_to_geopoint(wkb: WKBElement | None) -> GeoPoint | None:
    """PostGIS Geography (POINT) -> GeoPoint."""
    if wkb is None:
        return None
    point = to_shape(wkb)
    return GeoPoint(lat=point.y, lng=point.x)


def geopoint_to_wkt(point: GeoPoint) -> str:
    """GeoPoint -> WKT (DB INSERT uchun)."""
    return f"SRID=4326;POINT({point.lng} {point.lat})"


def model_location_to_geopoint(value: Any) -> GeoPoint | None:
    """SQLAlchemy obyektning location ustunini GeoPoint'ga aylantirish."""
    if value is None:
        return None
    if isinstance(value, WKBElement):
        return wkb_to_geopoint(value)
    return None
