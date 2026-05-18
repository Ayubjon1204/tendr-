"""Geo utility testlari — DB kerak emas."""
import pytest

from app.core.cities import city
from app.schemas.common import GeoPoint
from app.services.geo import estimate_drive_hours, haversine_km


def test_haversine_toshkent_samarqand():
    """Toshkent-Samarqand taxminan 270 km (great-circle)."""
    distance = haversine_km(city("Toshkent"), city("Samarqand"))
    assert 260 < distance < 290


def test_haversine_same_point_is_zero():
    point = GeoPoint(lat=41.0, lng=69.0)
    assert haversine_km(point, point) == pytest.approx(0.0, abs=0.001)


def test_haversine_symmetric():
    a = city("Toshkent")
    b = city("Buxoro")
    assert haversine_km(a, b) == pytest.approx(haversine_km(b, a), abs=0.001)


def test_estimate_drive_hours_default_speed():
    # 300 km / 60 km/h = 5 soat
    assert estimate_drive_hours(300) == pytest.approx(5.0)


def test_estimate_drive_hours_custom_speed():
    assert estimate_drive_hours(120, avg_speed_kmh=80) == pytest.approx(1.5)
