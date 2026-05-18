# Tendr — bir-bosh dev ishga tushirish skripti.
# Foydalanish: .\dev-start.ps1
#
# Bajaradi:
# 1. Docker'da Postgres+PostGIS va Redis'ni ishga tushiradi
# 2. Backend venv'ini tekshiradi/yaratadi
# 3. Migrationlarni qo'llaydi
# 4. Seed data yaratadi (agar ilgari yaratilmagan bo'lsa)
# 5. Backend (uvicorn) va frontend (vite) ni alohida oynalarda ishga tushiradi

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $MyInvocation.MyCommand.Definition

Write-Host "=== Tendr dev environment ===" -ForegroundColor Cyan

# 1. Docker
Write-Host "`n[1/5] Docker konteynerlarini ishga tushirish..." -ForegroundColor Yellow
Push-Location $root
docker compose up -d db redis
if ($LASTEXITCODE -ne 0) {
    Write-Host "Docker ishga tushirilmadi. Docker Desktop ochiqligini tekshiring." -ForegroundColor Red
    Pop-Location
    exit 1
}

# Postgres tayyor bo'lishini kutish
Write-Host "Postgres tayyor bo'lishini kutmoqdaman..."
$attempts = 0
while ($attempts -lt 30) {
    $health = docker inspect --format='{{.State.Health.Status}}' tendr-db 2>$null
    if ($health -eq "healthy") { break }
    Start-Sleep -Seconds 2
    $attempts++
}
if ($attempts -ge 30) {
    Write-Host "Postgres 60 soniya ichida tayyor bo'lmadi" -ForegroundColor Red
    Pop-Location
    exit 1
}
Pop-Location

# 2. Backend venv
Write-Host "`n[2/5] Backend venv tekshiruvi..." -ForegroundColor Yellow
$venvPython = Join-Path $root "backend\.venv\Scripts\python.exe"
if (-not (Test-Path $venvPython)) {
    Write-Host "Venv yo'q — yaratyapman..."
    Push-Location (Join-Path $root "backend")
    python3.14 -m venv .venv
    if (-not (Test-Path $venvPython)) {
        # python3.14 yo'q bo'lsa python ishlatish
        python -m venv .venv
    }
    & $venvPython -m pip install --upgrade pip wheel
    & $venvPython -m pip install -r requirements.txt
    Pop-Location
}

# 3. .env
$envFile = Join-Path $root "backend\.env"
if (-not (Test-Path $envFile)) {
    Copy-Item (Join-Path $root "backend\.env.example") $envFile
    Write-Host ".env yaratildi"
}

# 4. Migrations
Write-Host "`n[3/5] Migration'lar..." -ForegroundColor Yellow
Push-Location (Join-Path $root "backend")
& $venvPython -m alembic upgrade head
Pop-Location

# 5. Seed (faqat birinchi marta)
Write-Host "`n[4/5] Seed data..." -ForegroundColor Yellow
Push-Location (Join-Path $root "backend")
$seedCheck = & $venvPython -c "import asyncio; from app.db.session import AsyncSessionLocal; from app.models.user import User; from sqlalchemy import select
async def main():
    async with AsyncSessionLocal() as db:
        u = await db.scalar(select(User).limit(1))
        print('YES' if u else 'NO')
asyncio.run(main())" 2>$null
if ($seedCheck -match "NO") {
    Write-Host "Birinchi marta — seed qilyapman..."
    & $venvPython -m app.scripts.seed
} else {
    Write-Host "Seed data mavjud (qayta yaratish kerak bo'lsa: python -m app.scripts.seed)"
}
Pop-Location

# 6. Backend + frontend ishga tushirish (alohida oynalar)
Write-Host "`n[5/5] Serverlarni ishga tushiryapman..." -ForegroundColor Yellow

$backendCmd = "cd '$root\backend'; .\.venv\Scripts\activate; uvicorn app.main:app --reload"
$frontendCmd = "cd '$root\frontend'; npm run dev"

Start-Process powershell -ArgumentList "-NoExit", "-Command", $backendCmd
Start-Sleep -Seconds 2
Start-Process powershell -ArgumentList "-NoExit", "-Command", $frontendCmd

Write-Host "`n=== TAYYOR ===" -ForegroundColor Green
Write-Host "Backend:  http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host "Frontend: http://localhost:5173" -ForegroundColor Cyan
Write-Host ""
Write-Host "Login:"
Write-Host "  admin@tendr.local / admin123" -ForegroundColor White
Write-Host "  dispatcher@tendr.local / disp123" -ForegroundColor White
Write-Host ""
Write-Host "To'xtatish: ikkala terminal oynani yoping + docker compose down"
