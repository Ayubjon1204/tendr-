"""Seed script — sinov uchun realistik O'zbekiston logistika ssenariysi.

Ishga tushirish:
    python -m app.scripts.seed

Yaratadi:
- 1 admin foydalanuvchi (admin@tendr.local / admin123)
- 1 dispatcher (dispatcher@tendr.local / disp123)
- 5 carrier kompaniyalari (transport)
- 6 shipper kompaniyalari (yuk egalari)
- 30 mashina (turli body_type, sig'im, joylashuv)
- 60 haydovchi
- 40 yuk (turli statusda — yangi, biriktirilgan, yo'lda, yetkazilgan)
"""
from __future__ import annotations

import asyncio
import random
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from sqlalchemy import delete, select

from app.core.cities import UZ_CITIES, city
from app.core.security import hash_password
from app.db.session import AsyncSessionLocal
from app.models.assignment import Assignment
from app.models.cargo import Cargo, CargoStatus
from app.models.company import Company, CompanyKind
from app.models.driver import Driver
from app.models.enums import BodyType
from app.models.location_history import LocationHistory
from app.models.truck import Truck, TruckStatus
from app.models.truck_schedule import TruckSchedule
from app.models.user import User, UserRole
from app.services.geo import geopoint_to_wkt


# ---------------- Sinov ma'lumotlari ----------------

CARRIERS = [
    ("Tashkent Logistics LLC", "Toshkent", "+998901112233"),
    ("Samarqand Transport Group", "Samarqand", "+998902223344"),
    ("Buxoro Trans Service", "Buxoro", "+998903334455"),
    ("Vodiy Cargo Plus", "Andijon", "+998904445566"),
    ("Karavan Logistik", "Toshkent", "+998905556677"),
]

SHIPPERS = [
    ("UzAuto Motors", "Andijon"),
    ("Coca-Cola Uzbekistan", "Toshkent"),
    ("Korzinka.uz", "Toshkent"),
    ("Artel Electronics", "Toshkent"),
    ("Tashkent Cement", "Toshkent"),
    ("Bukhara Textile", "Buxoro"),
]

UZBEK_NAMES = [
    "Akmal Yusupov", "Bekzod Karimov", "Davron Tursunov", "Eldor Saidov",
    "Farrukh Tolipov", "Ganijon Mirzaev", "Husniddin Olimov", "Islom Rahimov",
    "Jamshid Yo'ldoshev", "Komiljon Asadov", "Lutfullo Nazarov", "Mansurbek Qodirov",
    "Nodirbek Hakimov", "Otabek Shukurov", "Pulat Eshmatov", "Rustam Sobirov",
    "Shavkat Tursunov", "Temur Norqulov", "Ulug'bek Egamberdiyev", "Vohid Po'latov",
    "Xushnud Salohiddinov", "Yodgor Tursunaliyev", "Zafar Mahmudov", "Abdulaziz Karimov",
    "Behruz Ergashev", "Doniyor Bobomurodov", "Elyor Soliyev", "Faxriddin Qulmatov",
    "Gulom Rajabov", "Husan To'raqulov",
]

# Body type taxminiy taqsimot
BODY_TYPE_WEIGHTS = [
    (BodyType.TENT, 0.50),
    (BodyType.REFRIGERATOR, 0.15),
    (BodyType.FLATBED, 0.15),
    (BodyType.CONTAINER, 0.10),
    (BodyType.TANK, 0.05),
    (BodyType.OTHER, 0.05),
]


def random_body_type() -> BodyType:
    r = random.random()
    cum = 0.0
    for bt, w in BODY_TYPE_WEIGHTS:
        cum += w
        if r <= cum:
            return bt
    return BodyType.TENT


def random_plate(idx: int) -> str:
    """01A123BC — O'zbekiston standart format."""
    region = random.choice(["01", "10", "20", "25", "30", "40", "50", "60", "70", "75", "80", "85", "90"])
    letters1 = random.choice("ABCDEFGHKLMN")
    letters2 = "".join(random.sample("ABCDEFGHKLMN", 2))
    return f"{region}{letters1}{100+idx:03d}{letters2}"


async def reset(db) -> None:
    """Mavjud ma'lumotlarni o'chirish (toza seed uchun)."""
    print("Eski ma'lumotlarni o'chiryapman...")
    await db.execute(delete(LocationHistory))
    await db.execute(delete(TruckSchedule))
    await db.execute(delete(Assignment))
    await db.execute(delete(Cargo))
    await db.execute(delete(Driver))
    await db.execute(delete(Truck))
    await db.execute(delete(Company))
    await db.execute(delete(User))
    await db.commit()


async def seed_users(db) -> None:
    print("Foydalanuvchilar...")
    db.add_all([
        User(
            email="admin@tendr.local",
            password_hash=hash_password("admin123"),
            full_name="Admin Tendr",
            role=UserRole.ADMIN,
        ),
        User(
            email="dispatcher@tendr.local",
            password_hash=hash_password("disp123"),
            full_name="Dispatcher Demo",
            role=UserRole.DISPATCHER,
        ),
    ])
    await db.commit()


async def seed_companies(db) -> tuple[list[Company], list[Company]]:
    print("Kompaniyalar...")
    carriers = [
        Company(
            name=name,
            kind=CompanyKind.CARRIER,
            phone=phone,
            address=f"{home_city} sh.",
            tax_id=f"30{random.randint(1000000, 9999999)}",
        )
        for name, home_city, phone in CARRIERS
    ]
    shippers = [
        Company(
            name=name,
            kind=CompanyKind.SHIPPER,
            address=f"{home_city} sh.",
            tax_id=f"20{random.randint(1000000, 9999999)}",
        )
        for name, home_city in SHIPPERS
    ]
    db.add_all(carriers + shippers)
    await db.commit()
    for c in carriers + shippers:
        await db.refresh(c)
    return carriers, shippers


async def seed_trucks(db, carriers: list[Company]) -> list[Truck]:
    print("Mashinalar...")
    trucks: list[Truck] = []
    for idx, carrier in enumerate(carriers):
        carrier_home = CARRIERS[idx][1]
        home_point = city(carrier_home)
        truck_count = random.randint(4, 8)
        for i in range(truck_count):
            bt = random_body_type()
            capacity = random.choice([1500, 3000, 5000, 8000, 12000, 20000])
            # 80% mashina home_city atrofida, 20% boshqa shaharda
            current_city = (
                carrier_home
                if random.random() < 0.8
                else random.choice(list(UZ_CITIES.keys()))
            )
            current = city(current_city)
            # Sal yon-atrofda (10 km radius)
            current_jittered = type(current)(
                lat=current.lat + random.uniform(-0.1, 0.1),
                lng=current.lng + random.uniform(-0.1, 0.1),
            )
            status = random.choices(
                [TruckStatus.AVAILABLE, TruckStatus.BUSY, TruckStatus.OFF_DUTY],
                weights=[0.65, 0.25, 0.10],
            )[0]
            t = Truck(
                carrier_id=carrier.id,
                plate_number=random_plate(idx * 10 + i),
                model=random.choice(
                    ["MAN TGX", "Volvo FH", "Mercedes Actros", "Isuzu NQR", "Scania R450", "Kamaz 5490"]
                ),
                capacity_kg=capacity,
                capacity_volume_m3=Decimal(str(round(capacity / 250, 2))),
                body_type=bt,
                status=status,
                current_location=geopoint_to_wkt(current_jittered),
                home_base_location=geopoint_to_wkt(home_point),
                last_location_update=datetime.now(tz=timezone.utc)
                - timedelta(minutes=random.randint(5, 240)),
            )
            db.add(t)
            trucks.append(t)
    await db.commit()
    for t in trucks:
        await db.refresh(t)
    return trucks


async def seed_drivers(db, carriers: list[Company], trucks: list[Truck]) -> None:
    print("Haydovchilar...")
    name_iter = iter(UZBEK_NAMES * 3)
    drivers: list[Driver] = []
    trucks_by_carrier: dict = {}
    for t in trucks:
        trucks_by_carrier.setdefault(t.carrier_id, []).append(t)

    for carrier in carriers:
        carrier_trucks = trucks_by_carrier.get(carrier.id, [])
        # Har truck'ga 1 haydovchi + zaxira
        for i, t in enumerate(carrier_trucks):
            try:
                name = next(name_iter)
            except StopIteration:
                name = f"Haydovchi #{i+1}"
            drivers.append(
                Driver(
                    carrier_id=carrier.id,
                    full_name=name,
                    phone=f"+9989{random.randint(10_000_000, 99_999_999)}",
                    license_number=f"AB{random.randint(1000000, 9999999)}",
                    current_truck_id=t.id,
                )
            )
        # +2 ta zaxira haydovchi
        for _ in range(2):
            try:
                name = next(name_iter)
            except StopIteration:
                continue
            drivers.append(
                Driver(
                    carrier_id=carrier.id,
                    full_name=name,
                    phone=f"+9989{random.randint(10_000_000, 99_999_999)}",
                    license_number=f"AB{random.randint(1000000, 9999999)}",
                )
            )
    db.add_all(drivers)
    await db.commit()


async def seed_cargo(db, shippers: list[Company]) -> None:
    print("Yuklar...")
    now = datetime.now(tz=timezone.utc)
    city_names = list(UZ_CITIES.keys())
    cargos: list[Cargo] = []

    for i in range(40):
        shipper = random.choice(shippers)
        origin_city = random.choice(city_names)
        destination_city = random.choice([c for c in city_names if c != origin_city])

        weight = random.choice([500, 1000, 2000, 3000, 5000, 8000, 12000, 18000])
        bt = random.choice([None, None, BodyType.TENT, BodyType.REFRIGERATOR, BodyType.FLATBED])

        # Pickup vaqti: -1 kun ... +3 kun
        pickup_offset_hours = random.randint(-24, 72)
        pickup_start = now + timedelta(hours=pickup_offset_hours)
        pickup_window = random.randint(2, 8)
        pickup_end = pickup_start + timedelta(hours=pickup_window)
        delivery_hours = random.randint(8, 36)
        deadline = pickup_end + timedelta(hours=delivery_hours)

        # Status taqsimoti
        status = random.choices(
            [
                CargoStatus.NEW,
                CargoStatus.ASSIGNED,
                CargoStatus.IN_TRANSIT,
                CargoStatus.DELIVERED,
            ],
            weights=[0.45, 0.20, 0.20, 0.15],
        )[0]

        c = Cargo(
            shipper_id=shipper.id,
            reference_code=f"TND-{2026000 + i}",
            description=f"{shipper.name} mahsulotlari",
            weight_kg=weight,
            volume_m3=Decimal(str(round(weight / 300, 2))),
            required_body_type=bt,
            origin_address=f"{origin_city}, {shipper.name} ombori",
            origin_location=geopoint_to_wkt(city(origin_city)),
            destination_address=f"{destination_city}, mijoz ombori",
            destination_location=geopoint_to_wkt(city(destination_city)),
            pickup_window_start=pickup_start,
            pickup_window_end=pickup_end,
            delivery_deadline=deadline,
            price=Decimal(str(weight * random.uniform(0.5, 1.5))),
            status=status,
        )
        cargos.append(c)
    db.add_all(cargos)
    await db.commit()


async def main() -> None:
    async with AsyncSessionLocal() as db:
        await reset(db)
        await seed_users(db)
        carriers, shippers = await seed_companies(db)
        trucks = await seed_trucks(db, carriers)
        await seed_drivers(db, carriers, trucks)
        await seed_cargo(db, shippers)

        # Hisobot
        users_n = await db.scalar(select(User.id).limit(1))
        print("\n=== Seed yakunlandi ===")
        print(f"Carriers: {len(carriers)}, Shippers: {len(shippers)}")
        print(f"Trucks: {len(trucks)}")
        print("Login:")
        print("  admin@tendr.local / admin123")
        print("  dispatcher@tendr.local / disp123")


if __name__ == "__main__":
    asyncio.run(main())
