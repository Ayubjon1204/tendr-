"""Geo utilities.

Haversine — buyuk doira (great-circle) bo'yicha masofa.
Yandex Routing API (haqiqiy yo'l vaqti/masofasi) Phase 5'da.
"""
from __future__ import annotations

import math
from decimal import Decimal

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


def coords_to_geopoint(
    lat: Decimal | float | None, lng: Decimal | float | None
) -> GeoPoint | None:
    """DB ustunlardan GeoPoint yig'ish."""
    if lat is None or lng is None:
        return None
    return GeoPoint(lat=float(lat), lng=float(lng))
