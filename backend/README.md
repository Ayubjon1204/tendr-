# Tendr Backend

FastAPI + SQLAlchemy + PostgreSQL/PostGIS + OR-Tools.

## Setup

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
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
