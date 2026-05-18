# Tendr Backend

FastAPI + SQLAlchemy + PostgreSQL/PostGIS + OR-Tools.

## Setup

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

> Python 3.14 ham qo'llab-quvvatlanadi (sinovdan o'tgan). Eski Python 3.12/3.13 ham ishlaydi.

## Sinovlar

```powershell
pytest -v
```

## Database (Docker)

Loyiha root'idan:
```powershell
docker compose up -d db
```

## Migrations

Birinchi marta (PostGIS yoqish):
```powershell
alembic upgrade head
```

Yangi model qo'shgandan keyin migration yaratish:
```powershell
alembic revision --autogenerate -m "add something"
alembic upgrade head
```

## Seed (sinov ma'lumotlari)

```powershell
python -m app.scripts.seed
```

Yaratadi: 5 carrier, 6 shipper, ~30 mashina, ~60 haydovchi, ~40 yuk.

Login (admin): `admin@tendr.local` / `admin123`
Login (dispatcher): `dispatcher@tendr.local` / `disp123`

## Ishga tushirish

```powershell
uvicorn app.main:app --reload
```

API hujjati: http://localhost:8000/docs
Health: http://localhost:8000/health
Ping: http://localhost:8000/api/v1/ping

## Tuzilish

```
backend/
├── app/
│   ├── api/v1/         # HTTP endpoints
│   ├── core/           # config, security
│   ├── db/             # session, base
│   ├── models/         # SQLAlchemy ORM
│   ├── schemas/        # Pydantic schemas (keyingi bosqich)
│   ├── services/       # biznes logika (keyingi bosqich)
│   └── main.py         # FastAPI app
├── alembic/            # DB migrations
├── alembic.ini
└── requirements.txt
```
