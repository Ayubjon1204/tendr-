# Tendr — Transport Management System

Logistika ERP/TMS — yuklar va transport mashinalari boshqaruvi tizimi.

## Maqsad

Transport kompaniyalarining mashinalarini "soatdek" ishlashini ta'minlash:
- Bo'sh turishni minimallashtirish
- Yuksiz qaytishni kamaytirish (back-haul matching)
- Yuklarni avtomatik biriktirish (Vehicle Routing optimization)
- Ertangi kun va dam olish kunlarini hisobga olgan rejalashtirish

## Tuzilish

```
tendr-/
├── frontend/          # React + Vite + TypeScript
├── backend/           # FastAPI + SQLAlchemy + OR-Tools
├── docs/              # Arxitektura, DB schema
└── docker-compose.yml # Postgres+PostGIS dev muhiti
```

## Talablar

- Node.js 20+
- Python 3.11+
- Docker Desktop (Postgres uchun)

## Ishga tushirish

### 1. Bazani ishga tushirish
```powershell
docker compose up -d db
```

### 2. Backend
```powershell
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload
```

### 3. Frontend
```powershell
cd frontend
npm install
npm run dev
```

## Hujjatlar

- [Arxitektura](docs/ARCHITECTURE.md)
- [Database schema](docs/DATABASE.md)
