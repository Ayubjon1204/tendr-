"""Seed script — Phase 2 multi-tenant ssenariy.

Yaratadi:
- Super-admin (admin@tendr.local)
- 3 ta zavod (factory) + ularning dispatcher'lari
- 5 ta carrier (3 tip aralash) + ularning dispatcher'lari
- 4 ta distributor + ularning dispatcher'lari
- Har carrier'da: mashinalar va haydovchilar
- 40 ta yuk (turli factory'dan turli distributor'ga)

Ishga tushirish:
    python -m app.scripts.seed
"""
from __future__ import annotations

import asyncio
import random
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from sqlalchemy import delete

from app.core.cities import UZ_CITIES, city
from app.core.security import hash_password
from app.db.session import AsyncSessionLocal
from app.models.assignment import Assignment
from app.models.cargo import Cargo, CargoStatus
from app.models.company import CarrierType, Company, CompanyKind
from app.models.document import Document
from app.models.driver import Driver
from app.models.enums import BodyType
from app.models.location_history import LocationHistory
from app.models.truck import Truck, TruckStatus
from app.models.truck_schedule import TruckSchedule
from app.models.user import User, UserRole
from app.schemas.common import GeoPoint


FACTORIES = [
    ("UzAuto Motors", "Andijon"),
    ("Tashkent Cement", "Toshkent"),
    ("Bukhara Textile", "Buxoro"),
]

CARRIERS = [
    # (nom, home_city, telefon, carrier_type)
    ("Tashkent Logistics LLC", "Toshkent", "+998901112233", CarrierType.HYBRID),
    ("Samarqand Transport Group", "Samarqand", "+998902223344", CarrierType.ASSET_ONLY),
    ("Buxoro Trans Service", "Buxoro", "+998903334455", CarrierType.HYBRID),
    ("Vodiy Cargo Plus", "Andijon", "+998904445566", CarrierType.ASSET_ONLY),
    ("Karavan Logistik", "Toshkent", "+998905556677", CarrierType.FORWARDER),
]

DISTRIBUTORS = [
    ("Korzinka.uz Markaz", "Toshkent"),
    ("Coca-Cola Distribution", "Toshkent"),
    ("Artel Bukhara DC", "Buxoro"),
    ("Makro Vodiy", "Andijon"),
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
    region = random.choice(["01", "10", "20", "25", "30", "40", "50", "60", "70", "75", "80", "85", "90"])
    letters1 = random.choice("ABCDEFGHKLMN")
    letters2 = "".join(random.sample("ABCDEFGHKLMN", 2))
    return f"{region}{letters1}{100+idx:03d}{letters2}"


def dec(x: float) -> Decimal:
    return Decimal(str(round(x, 6)))


async def reset(db) -> None:
    print("Eski ma'lumotlarni o'chiryapman...")
    await db.execute(delete(Document))
    await db.execute(delete(LocationHistory))
    await db.execute(delete(TruckSchedule))
    await db.execute(delete(Assignment))
    await db.execute(delete(Cargo))
    await db.execute(delete(Driver))
    await db.execute(delete(Truck))
    await db.execute(delete(User))
    await db.execute(delete(Company))
    await db.commit()


async def seed_companies(db) -> tuple[list[Company], list[Company], list[Company]]:
    print("Kompaniyalar...")
    factories = [
        Company(
            name=name, kind=CompanyKind.FACTORY,
            address=f"{home_city} sh.",
            tax_id=f"20{random.randint(1000000, 9999999)}",
        )
        for name, home_city in FACTORIES
    ]
    carriers = [
        Company(
            name=name, kind=CompanyKind.CARRIER, carrier_type=ctype,
            phone=phone, address=f"{home_city} sh.",
            tax_id=f"30{random.randint(1000000, 9999999)}",
        )
        for name, home_city, phone, ctype in CARRIERS
    ]
    distributors = [
        Company(
            name=name, kind=CompanyKind.DISTRIBUTOR,
            address=f"{home_city} sh.",
            tax_id=f"40{random.randint(1000000, 9999999)}",
        )
        for name, home_city in DISTRIBUTORS
    ]
    db.add_all(factories + carriers + distributors)
    await db.commit()
    for c in factories + carriers + distributors:
        await db.refresh(c)
    return factories, carriers, distributors


async def seed_users(
    db, factories: list[Company], carriers: list[Company], distributors: list[Company]
) -> None:
    print("Foydalanuvchilar...")
    users: list[User] = [
        User(
            email="admin@tendr.local",
            password_hash=hash_password("admin123"),
            full_name="Super Admin",
            role=UserRole.OWNER,
            company_id=None,
        )
    ]
    # Har factory uchun dispatcher
    for f in factories:
        slug = f.name.lower().replace(" ", "").replace(".", "").replace("'", "")[:12]
        users.append(
            User(
                email=f"factory-{slug}@tendr.local",
                password_hash=hash_password("factory123"),
                full_name=f"{f.name} dispatcher",
                role=UserRole.DISPATCHER,
                company_id=f.id,
            )
        )
    # Har carrier uchun
    for c in carriers:
        slug = c.name.lower().replace(" ", "").replace(".", "").replace("'", "")[:12]
        users.append(
            User(
                email=f"carrier-{slug}@tendr.local",
                password_hash=hash_password("carrier123"),
                full_name=f"{c.name} dispatcher",
                role=UserRole.DISPATCHER,
                company_id=c.id,
            )
        )
    # Har distributor uchun
    for d in distributors:
        slug = d.name.lower().replace(" ", "").replace(".", "").replace("'", "")[:12]
        users.append(
            User(
                email=f"distributor-{slug}@tendr.local",
                password_hash=hash_password("dist123"),
                full_name=f"{d.name} dispatcher",
                role=UserRole.DISPATCHER,
                company_id=d.id,
            )
        )
    db.add_all(users)
    await db.commit()


async def seed_trucks(db, carriers: list[Company]) -> list[Truck]:
    print("Mashinalar...")
    trucks: list[Truck] = []
    for idx, carrier in enumerate(carriers):
        # FORWARDER tipidagi carrier mashinasiz
        if carrier.carrier_type == CarrierType.FORWARDER:
            continue
        carrier_home = CARRIERS[idx][1]
        home_point = city(carrier_home)
        truck_count = random.randint(4, 8)
        for i in range(truck_count):
            bt = random_body_type()
            capacity = random.choice([1500, 3000, 5000, 8000, 12000, 20000])
            current_city = (
                carrier_home if random.random() < 0.8
                else random.choice(list(UZ_CITIES.keys()))
            )
            cur = city(current_city)
            jittered = GeoPoint(
                lat=cur.lat + random.uniform(-0.1, 0.1),
                lng=cur.lng + random.uniform(-0.1, 0.1),
            )
            status = random.choices(
                [TruckStatus.AVAILABLE, TruckStatus.BUSY, TruckStatus.OFF_DUTY],
                weights=[0.65, 0.25, 0.10],
            )[0]
            t = Truck(
                carrier_id=carrier.id,
                is_spot=False,
                plate_number=random_plate(idx * 10 + i),
                model=random.choice(
                    ["MAN TGX", "Volvo FH", "Mercedes Actros", "Isuzu NQR", "Scania R450", "Kamaz 5490"]
                ),
                capacity_kg=capacity,
                capacity_volume_m3=Decimal(str(round(capacity / 250, 2))),
                body_type=bt,
                status=status,
                current_lat=dec(jittered.lat),
                current_lng=dec(jittered.lng),
                home_base_lat=dec(home_point.lat),
                home_base_lng=dec(home_point.lng),
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
        if t.carrier_id:
            trucks_by_carrier.setdefault(t.carrier_id, []).append(t)

    for carrier in carriers:
        if carrier.carrier_type == CarrierType.FORWARDER:
            continue
        carrier_trucks = trucks_by_carrier.get(carrier.id, [])
        for i, t in enumerate(carrier_trucks):
            try:
                name = next(name_iter)
            except StopIteration:
                name = f"Haydovchi #{i+1}"
            drivers.append(
                Driver(
                    carrier_id=carrier.id, full_name=name,
                    phone=f"+9989{random.randint(10_000_000, 99_999_999)}",
                    license_number=f"AB{random.randint(1000000, 9999999)}",
                    current_truck_id=t.id,
                )
            )
        for _ in range(2):
            try:
                name = next(name_iter)
            except StopIteration:
                continue
            drivers.append(
                Driver(
                    carrier_id=carrier.id, full_name=name,
                    phone=f"+9989{random.randint(10_000_000, 99_999_999)}",
                    license_number=f"AB{random.randint(1000000, 9999999)}",
                )
            )
    db.add_all(drivers)
    await db.commit()


async def seed_cargo(db, factories: list[Company], distributors: list[Company]) -> None:
    print("Yuklar...")
    now = datetime.now(tz=timezone.utc)
    city_names = list(UZ_CITIES.keys())
    cargos: list[Cargo] = []

    for i in range(40):
        factory = random.choice(factories)
        distributor = random.choice(distributors)

        origin_city = random.choice(city_names)
        destination_city = random.choice([c for c in city_names if c != origin_city])
        o, d = city(origin_city), city(destination_city)

        weight = random.choice([500, 1000, 2000, 3000, 5000, 8000, 12000, 18000])
        bt = random.choice([None, None, BodyType.TENT, BodyType.REFRIGERATOR, BodyType.FLATBED])

        pickup_offset_hours = random.randint(-24, 72)
        pickup_start = now + timedelta(hours=pickup_offset_hours)
        pickup_window = random.randint(2, 8)
        pickup_end = pickup_start + timedelta(hours=pickup_window)
        delivery_hours = random.randint(8, 36)
        deadline = pickup_end + timedelta(hours=delivery_hours)

        status = random.choices(
            [
                CargoStatus.NEW,
                CargoStatus.DISTRIBUTED,
                CargoStatus.ASSIGNED_TRUCK,
                CargoStatus.IN_TRANSIT,
                CargoStatus.DELIVERED,
            ],
            weights=[0.40, 0.10, 0.15, 0.20, 0.15],
        )[0]

        c = Cargo(
            factory_id=factory.id,
            distributor_id=distributor.id,
            reference_code=f"TND-{2026000 + i}",
            description=f"{factory.name} mahsulotlari",
            weight_kg=weight,
            volume_m3=Decimal(str(round(weight / 300, 2))),
            required_body_type=bt,
            origin_address=f"{origin_city}, {factory.name} ombori",
            origin_lat=dec(o.lat),
            origin_lng=dec(o.lng),
            destination_address=f"{destination_city}, {distributor.name}",
            destination_lat=dec(d.lat),
            destination_lng=dec(d.lng),
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
        factories, carriers, distributors = await seed_companies(db)
        await seed_users(db, factories, carriers, distributors)
        trucks = await seed_trucks(db, carriers)
        await seed_drivers(db, carriers, trucks)
        await seed_cargo(db, factories, distributors)

        print("\n=== Seed yakunlandi ===")
        print(f"Factories: {len(factories)}")
        print(f"Carriers: {len(carriers)} ({sum(1 for c in carriers if c.carrier_type == CarrierType.FORWARDER)} forwarder)")
        print(f"Distributors: {len(distributors)}")
        print(f"Trucks: {len(trucks)}")
        print("\nLogin'lar (parol 'factory123', 'carrier123', 'dist123'):")
        print("  admin@tendr.local / admin123  (super-admin)")
        for f in factories:
            slug = f.name.lower().replace(" ", "").replace(".", "").replace("'", "")[:12]
            print(f"  factory-{slug}@tendr.local  ({f.name})")
        for c in carriers:
            slug = c.name.lower().replace(" ", "").replace(".", "").replace("'", "")[:12]
            print(f"  carrier-{slug}@tendr.local  ({c.name} — {c.carrier_type.value})")
        for d in distributors:
            slug = d.name.lower().replace(" ", "").replace(".", "").replace("'", "")[:12]
            print(f"  distributor-{slug}@tendr.local  ({d.name})")


if __name__ == "__main__":
    asyncio.run(main())
