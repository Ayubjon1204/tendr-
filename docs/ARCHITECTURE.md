# Tendr — Arxitektura

## Maqsad

Logistika brokerligi/dispatcher tizimi. Asosiy qiymat — **fleet utilization optimization**:
1000 ga yaqin mashina doim ish bilan band, bo'sh yurmaydi, yuksiz qaytmaydi.

## Yuqori darajadagi sxema

```
┌──────────────────────────────┐         ┌──────────────────────────────┐
│  Dispatcher Web UI           │         │  Driver Mobile App (Phase 6) │
│  React + Vite + TS           │         │  React Native (rejada)       │
│  Yandex Maps                 │         │  GPS tracker, status update  │
└──────────────┬───────────────┘         └──────────────┬───────────────┘
               │ REST + WebSocket                       │ REST
               ▼                                        ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                   FastAPI (Python 3.11+)                                │
│  ┌─────────────┐  ┌─────────────┐  ┌──────────────────────────────────┐ │
│  │ /api/v1     │  │ WebSockets  │  │  Background Tasks (Celery)       │ │
│  │ - companies │  │ live updates│  │  - assignment_optimizer          │ │
│  │ - trucks    │  │             │  │  - schedule_recalculator         │ │
│  │ - cargo     │  │             │  │  - location_processor            │ │
│  │ - assigns   │  │             │  │                                  │ │
│  │ - auth      │  │             │  └──────────────────────────────────┘ │
│  └─────────────┘  └─────────────┘                                       │
└──────┬─────────────────────────────────┬──────────────────────────┬─────┘
       │ SQLAlchemy async                │                          │
       ▼                                 ▼                          ▼
┌──────────────────┐              ┌────────────────┐       ┌────────────────┐
│ PostgreSQL 16    │              │  Redis         │       │ OR-Tools VRP   │
│ + PostGIS 3.4    │              │  (queue+cache) │       │ (in-process)   │
└──────────────────┘              └────────────────┘       └────────────────┘
                                                                   │
                                                          ┌────────▼───────┐
                                                          │ Yandex Routing │
                                                          │ Distance API   │
                                                          └────────────────┘
```

## Modullar (backend)

```
backend/app/
├── api/v1/
│   ├── auth.py          # /auth/login, /auth/me
│   ├── companies.py     # carriers + shippers CRUD
│   ├── trucks.py        # trucks CRUD + location update
│   ├── drivers.py       # drivers CRUD
│   ├── cargo.py         # cargo CRUD + filter by status
│   ├── assignments.py   # manual + auto assignment endpoints
│   └── schedule.py      # truck schedule view/edit
├── core/
│   ├── config.py        # pydantic Settings
│   └── security.py      # JWT, password hashing
├── db/
│   ├── base.py          # Base, mixins
│   └── session.py       # async engine, get_db
├── models/              # SQLAlchemy ORM
├── schemas/             # Pydantic request/response (Phase 2)
├── services/
│   ├── assignment.py    # biriktirish biznes logikasi
│   ├── optimizer.py     # OR-Tools wrapper
│   └── routing.py       # Yandex Routing API client
├── workers/
│   ├── celery_app.py
│   └── tasks/
│       ├── optimize.py  # periodic full re-optimization
│       └── geocode.py
└── main.py
```

## Asosiy oqimlar

### Oqim 1: Yangi yuk kelganda
```
Dispatcher → POST /api/v1/cargo
   ├─ DB ga yoziladi (status=new)
   ├─ Celery task: optimize_for_new_cargo(cargo_id)
   │     ├─ Eng mos truck'larni topadi (OR-Tools)
   │     ├─ Eng yaxshi variantni tanlaydi
   │     └─ Assignment yaratadi (status=proposed)
   └─ WebSocket: dispatcher ekraniga "Yangi assignment" push
```

### Oqim 2: Truck joylashuvi yangilanganda (Phase 6 — mobile app)
```
Driver app → POST /api/v1/trucks/{id}/location
   ├─ location_history ga insert
   ├─ truck.current_location UPDATE
   └─ Agar yetib keldi: status = LOADING/UNLOADING auto-transition
```

### Oqim 3: Schedule-aware optimization
```
Har soatda Celery beat:
   ├─ Kelgusi 7 kun uchun re-optimize
   ├─ Dam olish kunlarini hisobga oladi
   └─ Maintenance/off_duty oraliqlarini bloklaydi
```

## Avtomatik biriktirish algoritmi (qisqacha)

**Vehicle Routing Problem with Time Windows (VRPTW)** — klassik OR-Tools.

Input:
- N ta truck (joylashuv, capacity, schedule)
- M ta cargo (origin, dest, weight, time window)
- Distance matrix (Yandex Routing yoki Haversine fallback)

Constraints:
- Truck capacity ≥ cargo weight
- Truck body_type ↔ cargo.required_body_type
- Truck home base ↔ kechqurun qaytish (optional)
- Cargo pickup_window
- Cargo delivery_deadline
- Truck schedule (day_off, maintenance)

Objective (minimize):
- Empty miles (back-haul minimization)
- Total wait time
- Late deliveries (high penalty)
- Idle time

Output:
- Har bir truck uchun cargo sequence + ETA
- Assignment yoziladi

**Tezlik:** 1000 truck × ~500 yangi yuk uchun re-solve = ~30-60s (OR-Tools metaheuristics). Yangi bitta yuk uchun **incremental** insertion = <2s.

## Fronend (alohida hujjat kelgusi)

- React Router 6
- TanStack Query (server state)
- Zustand (UI state)
- Tailwind CSS yoki shadcn/ui
- Yandex Maps JS API v3

## Bosqichlar (rejada)

| Phase | Mavzu | Holat |
|-------|-------|-------|
| 1 | Foundation: monorepo, DB schema, FastAPI skeleton | ✅ Done |
| 2 | Auth + CRUD endpoints + seed data | ⏳ Keyingi |
| 3 | Frontend: layout, routing, asosiy ekranlar | ⏳ |
| 4 | Auto-assignment algoritm (OR-Tools) | ⏳ |
| 5 | Yandex Maps + xarita ekrani + jadval | ⏳ |
| 6 | Driver mobile app (React Native) | 🔮 Kelajak |

## Xavfsizlik
- JWT bearer token (1 kunlik expire)
- Parol — bcrypt
- Role-based access: admin / dispatcher / viewer
- HTTPS (production'da reverse proxy orqali)

## Deployment (kelgusida)
- Backend + DB: Docker, server (DigitalOcean / Hetzner / Yandex Cloud)
- Frontend: Vercel yoki Nginx static
- Yandex Maps API key — production'da domain restriction bilan
