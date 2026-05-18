"""O'zbekiston shaharlari + koordinatalari.

Logistika sinovi uchun: 12 ta yirik markaz, asosiy yo'nalishlar shu yerdan.
"""
from app.schemas.common import GeoPoint

UZ_CITIES: dict[str, GeoPoint] = {
    "Toshkent": GeoPoint(lat=41.2995, lng=69.2401),
    "Samarqand": GeoPoint(lat=39.6542, lng=66.9597),
    "Buxoro": GeoPoint(lat=39.7747, lng=64.4286),
    "Andijon": GeoPoint(lat=40.7821, lng=72.3442),
    "Namangan": GeoPoint(lat=40.9983, lng=71.6726),
    "Farg'ona": GeoPoint(lat=40.3864, lng=71.7864),
    "Qarshi": GeoPoint(lat=38.8606, lng=65.7886),
    "Termiz": GeoPoint(lat=37.2242, lng=67.2783),
    "Nukus": GeoPoint(lat=42.4531, lng=59.6103),
    "Urganch": GeoPoint(lat=41.5503, lng=60.6311),
    "Jizzax": GeoPoint(lat=40.1158, lng=67.8422),
    "Navoiy": GeoPoint(lat=40.0844, lng=65.3792),
}


def city(name: str) -> GeoPoint:
    """Shahar nomidan koordinata olish."""
    if name not in UZ_CITIES:
        raise KeyError(f"Unknown city: {name}")
    return UZ_CITIES[name]
