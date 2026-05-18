# Database Schema

PostgreSQL 16 + PostGIS 3.4. Birlamchi kalitlar — UUID.

## Asosiy mantiq (domain)

Tendr — bu **broker/dispatcher** rolida ishlaydi:
- Foydalanuvchining o'z **shipper**'lari (yuk egalari / mijozlar) bor
- Foydalanuvchi **carrier**'lar (transport kompaniyalari) bilan ishlaydi
- Har bir carrier'ning **truck**'lari va **driver**'lari bor
- Tendr **cargo** (yuk) larni avtomatik ravishda truck'larga **assign** qiladi

## Jadvallar

### `companies`
Transport kompaniyalari (carriers) **va** mijoz kompaniyalari (shippers).
Bitta jadval, `kind` ustuni orqali ajratiladi (`carrier` / `shipper`).

| Ustun | Tip | Izoh |
|-------|-----|------|
| id | UUID PK | |
| name | text | Kompaniya nomi |
| kind | enum | `carrier` yoki `shipper` |
| tax_id | text? | STIR |
| phone | text? | |
| email | text? | |
| address | text? | |
| is_active | bool | default true |
| created_at / updated_at | timestamptz | |

### `trucks`
Mashinalar. Faqat carrier kompaniyalarga tegishli.

| Ustun | Tip | Izoh |
|-------|-----|------|
| id | UUID PK | |
| carrier_id | UUID FK → companies.id | Kim mashinasi |
| plate_number | text UNIQUE | Davlat raqami |
| model | text? | "MAN TGX" kabi |
| capacity_kg | int | Maksimal yuk og'irligi |
| capacity_volume_m3 | numeric? | Hajm (kubometr) |
| body_type | enum | `tent`, `refrigerator`, `flatbed`, `tank`, `container`, `other` |
| status | enum | `available`, `busy`, `loading`, `unloading`, `maintenance`, `off_duty` |
| current_location | geography(Point,4326)? | Hozirgi joylashuvi |
| last_location_update | timestamptz? | |
| home_base_location | geography(Point,4326)? | "Uy" bazasi (kechqurun qaytadigan joy) |
| is_active | bool | |
| created_at / updated_at | timestamptz | |

### `drivers`
Haydovchilar. Truck bilan many-to-many bog'liq emas — bir haydovchi bir vaqtda bir mashinada.

| Ustun | Tip | Izoh |
|-------|-----|------|
| id | UUID PK | |
| carrier_id | UUID FK → companies.id | |
| full_name | text | |
| phone | text | Asosiy aloqa |
| license_number | text? | |
| current_truck_id | UUID FK? → trucks.id | Hozir qaysi mashinada |
| is_active | bool | |
| created_at / updated_at | timestamptz | |

### `cargo`
Yuklar. Shipper tomonidan tushadi, tizim truck'ga biriktiradi.

| Ustun | Tip | Izoh |
|-------|-----|------|
| id | UUID PK | |
| shipper_id | UUID FK → companies.id | Yuk egasi |
| reference_code | text UNIQUE | Foydalanuvchi raqami |
| description | text? | |
| weight_kg | int | |
| volume_m3 | numeric? | |
| required_body_type | enum? | `tent`, `refrigerator`, ... |
| origin_address | text | "Toshkent, ..." |
| origin_location | geography(Point,4326) | |
| destination_address | text | |
| destination_location | geography(Point,4326) | |
| pickup_window_start | timestamptz | Yuklash uchun erta vaqt |
| pickup_window_end | timestamptz | Yuklash uchun kech vaqt |
| delivery_deadline | timestamptz | Yetkazib berish so'nggi muddati |
| price | numeric? | Mijoz to'lovi |
| status | enum | `new`, `assigned`, `picked_up`, `in_transit`, `delivered`, `cancelled`, `failed` |
| created_at / updated_at | timestamptz | |

### `assignments`
Yuk ↔ Mashina biriktirish. Bitta cargo'da bitta active assignment, lekin tarix saqlanadi.

| Ustun | Tip | Izoh |
|-------|-----|------|
| id | UUID PK | |
| cargo_id | UUID FK → cargo.id | |
| truck_id | UUID FK → trucks.id | |
| driver_id | UUID FK? → drivers.id | Biriktirilgan haydovchi |
| status | enum | `proposed`, `accepted`, `rejected`, `in_progress`, `completed`, `cancelled` |
| assigned_by | enum | `system`, `dispatcher` |
| planned_pickup_at | timestamptz | |
| planned_delivery_at | timestamptz | |
| actual_pickup_at | timestamptz? | |
| actual_delivery_at | timestamptz? | |
| optimization_score | numeric? | Algoritm tomonidan berilgan ball |
| notes | text? | |
| created_at / updated_at | timestamptz | |

UNIQUE INDEX: `(cargo_id) WHERE status IN ('proposed','accepted','in_progress')` — bir vaqtda bir aktiv assignment.

### `truck_schedule`
Mashinalar jadvali (band/bo'sh vaqtlar, dam olish kunlari).
Schedule-aware optimization uchun zarur.

| Ustun | Tip | Izoh |
|-------|-----|------|
| id | UUID PK | |
| truck_id | UUID FK → trucks.id | |
| start_at | timestamptz | |
| end_at | timestamptz | |
| kind | enum | `work`, `day_off`, `maintenance`, `assignment` |
| assignment_id | UUID FK? → assignments.id | Agar `assignment` bo'lsa |
| notes | text? | |
| created_at | timestamptz | |

### `location_history`
Mashina joylashuvlari tarixi (mobile app'dan kelganda).

| Ustun | Tip | Izoh |
|-------|-----|------|
| id | bigserial PK | |
| truck_id | UUID FK → trucks.id | |
| location | geography(Point,4326) | |
| speed_kmh | numeric? | |
| heading | numeric? | |
| recorded_at | timestamptz | |

### `users`
Tizim foydalanuvchilari (dispatcherlar, adminlar).

| Ustun | Tip | Izoh |
|-------|-----|------|
| id | UUID PK | |
| email | text UNIQUE | |
| password_hash | text | bcrypt |
| full_name | text | |
| role | enum | `admin`, `dispatcher`, `viewer` |
| is_active | bool | |
| created_at / updated_at | timestamptz | |

## Indekslar (asosiy)

- `cargo (status)` — yangi yuklarni topish uchun
- `cargo (pickup_window_start, delivery_deadline)` — vaqt bo'yicha filter
- `cargo USING GIST(origin_location)` — geo-radius so'rovlar
- `cargo USING GIST(destination_location)` — back-haul matching
- `trucks (status)` — bo'sh mashinalar
- `trucks (carrier_id, status)` — carrier bo'yicha bo'sh mashinalar
- `trucks USING GIST(current_location)` — eng yaqin mashinani topish
- `assignments (truck_id, status)` — mashinaning aktiv ishlari
- `truck_schedule (truck_id, start_at, end_at)` — mashina jadvali so'rovi
- `location_history (truck_id, recorded_at DESC)` — so'nggi joylashuv

## Migratsiyalar

Alembic ishlatamiz. Har bir DB o'zgarishi — yangi migration.

```bash
cd backend
alembic revision --autogenerate -m "description"
alembic upgrade head
```
