# Tendr — To'liq biznes konsepsiyasi

> Bu hujjat **biznes mantiqi** va **arxitektura qarorlari**ni belgilaydi.
> Texnik tafsilotlar: [ARCHITECTURE.md](ARCHITECTURE.md), DB: [DATABASE.md](DATABASE.md).

## 1. Loyiha vizyoni

Tendr — **multi-party logistika platformasi**. 4 ta foydalanuvchi turini bog'laydigan ekosistema:

```
┌─────────┐         ┌──────────────┐         ┌─────────┐         ┌─────────────┐
│  ZAVOD  │ ───────►│  TRANSPORT   │ ───────►│ HAYDOVCHI│ ───────►│ DISTRIBUTOR │
│         │         │  KOMPANIYA   │         │          │         │             │
└─────────┘         └──────┬───────┘         └─────────┘         └─────────────┘
                           │
                           ▼ (Type 2 — pure forwarder)
                    ┌──────────────┐
                    │  OSTKI       │
                    │  CARRIER     │
                    │  (Lorry/TG)  │
                    └──────────────┘
```

## 2. Personalar

### 2.1 Zavod (Factory) — buyurtma egasi
**Vazifalar:**
- Yuk buyurtmalarini yaratish (qaerdan → qaerga, og'irlik, vaqt)
- Transport kompaniyalarni tanlash (avto-tavsiya yoki qo'lda)
- Buyurtma statusini realtime kuzatish
- TTN va boshqa hujjatlarni saqlash
- Hisobot: oylik yuk hajmi, eng ishonchli carrier, kechikkanlar

**Asosiy ekranlar:**
1. Dashboard (bugungi yuklar, kechikkanlar, oylik xulosa)
2. Yangi buyurtma (factory'dan distributor'gacha)
3. Buyurtmalar ro'yxati (status filter)
4. Carrier'lar reytingi (ko'p ishlatilgan, ishonchli)
5. Distributor'lar ro'yxati (mijozlar)
6. Hujjatlar arxivi

### 2.2 Transport kompaniya (Carrier) — 3 tip

**Type 1 — Hybrid:** O'z mashinasi + ekspeditorlik
- Avval o'z mashinasini tekshiradi
- Bo'sh bo'lmasa — subcontract qiladi

**Type 2 — Pure forwarder:** Mashinasiz, faqat ekspeditor
- Buyurtmani qabul qilgach, **darhol** boshqa carrier yoki "ko'cha" mashinasi qidiradi
- Multi-hop assignment

**Type 3 — Asset-only:** Faqat o'z mashinasi
- Faqat o'z fleet'iga biriktiradi
- Bo'sh mashina bo'lmasa, buyurtmani **rad etadi**

**Asosiy ekranlar:**
1. Dashboard (yangi takliflar, jarayondagi yuklar, fleet utilization)
2. Buyurtma takliflar (yangi yuklar — qabul/rad qilish)
3. Mashina biriktirish (o'z fleet yoki "spot truck" qo'shish)
4. Mashinalar ro'yxati (status, joylashuv)
5. Haydovchilar
6. To'lovlar (qabul qilingan, kutilayotgan)

### 2.3 Haydovchi (Driver) — mobile

**Vazifalar:**
- Yangi job kelganda push notification
- Pickup'ga navigatsiya (Yandex Navi/Google Maps integratsiya)
- Yukni olganligini tasdiqlash (TTN photo, signature)
- Realtime GPS yuborish
- Delivery'da distributor imzosini olish (signature pad)
- Hujjat photo'sini yuborish

**Asosiy ekranlar (mobile, soddalashtirilgan):**
1. Aktiv job (xarita + checkpoints)
2. Mening jadvalim
3. Tarix (oxirgi 30 kun)
4. Profil + sozlamalar

### 2.4 Distributor (Consignee) — qabul qiluvchi

**Vazifalar:**
- Kelayotgan yuklarni ko'rish (ETA, mashina)
- Mashina kelganda qabul qilish (tushirish joyini tayyorlash)
- TTN tekshirish (qog'ozli yoki QR-scan)
- Farq bo'lsa belgilash (kam keldi, buzilgan)
- Imzo + qabul hujjati shakllantirish

**Asosiy ekranlar:**
1. Bugungi kelayotgan yuklar (ETA bo'yicha tartiblangan)
2. Qabul ekrani (mashina, TTN, miqdor tekshiruvi)
3. Tarix (oxirgi qabullar)
4. Hujjatlar (TTN'lar)
5. Hisobot

## 3. Yuk hayot-tsikli (status machine)

```
[NEW]            ←── Zavod yaratdi
   │
   ▼
[DISTRIBUTED]    ←── Zavod carrier'larga taklif yubordi
   │
   ▼
[CARRIER_ACCEPTED] ←── Carrier qabul qildi
   │
   ▼
[ASSIGNED_TRUCK]   ←── Mashina biriktirildi (o'z yoki spot)
   │
   ▼
[DRIVER_NOTIFIED]  ←── Haydovchi xabardor qilindi
   │
   ▼
[EN_ROUTE_PICKUP]  ←── Haydovchi pickup'ga yo'lda
   │
   ▼
[AT_PICKUP]        ←── Haydovchi zavod'da
   │
   ▼
[LOADING]          ←── Yuklanmoqda
   │
   ▼
[LOADED]           ←── Yuklandi, TTN imzolandi (factory + driver)
   │
   ▼
[IN_TRANSIT]       ←── Yo'lda
   │
   ▼
[AT_DELIVERY]      ←── Distributor'da
   │
   ▼
[UNLOADING]        ←── Tushirilmoqda
   │
   ▼
[DELIVERED]        ←── Tushirildi, TTN imzolandi (distributor + driver)
   │
   ▼
[COMPLETED]        ←── Hammasi yakunlandi, to'lov boshlandi
```

**Anomaliyalar:**
- `CARRIER_REJECTED` — carrier'lar rad etdi → qaytadan tarqatish
- `CANCELLED` — zavod bekor qildi
- `FAILED` — yetkazib bo'lmadi (mashina buzildi, h.k.)
- `DISCREPANCY` — distributor farq aniqladi (qo'shimcha hujjat)

## 4. Multi-hop assignment (Carrier Type 2 uchun)

Pure forwarder (Type 2) buyurtmani **boshqa carrier'ga** o'tkazganda:

```
Order O
  └─ Assignment A1 (factory → CarrierType2)  [status: forwarded]
       └─ Assignment A2 (CarrierType2 → CarrierType1/3)  [status: assigned_truck]
            └─ Truck T → Driver D
```

DB:
- `assignment` jadvaliga `parent_assignment_id` qo'shiladi
- "Mas'uliyat zanjiri" — har bir hop o'z marja/komissiyasiga ega bo'lishi mumkin

## 5. Spot truck (Lorry/Telegram)

Carrier "ko'cha"dan mashina topganda:
- `trucks` jadvaliga insert (lekin `is_spot = true`, `carrier_id = null`)
- `spot_source = 'lorry' | 'telegram' | 'manual'`
- Haydovchi ham `is_spot = true` bo'lishi mumkin (registrlanmagan)
- Hisobot: oyiga necha foiz "ko'cha" mashina ishlatilgan

## 6. Hujjatlar (TTN)

**Tovar-Transport Hujjati** — O'zbekiston qonuniy talab.

Maydonlar:
- TTN raqami (avto-generatsiya)
- Sana, vaqt
- Yuboruvchi (factory) — manzil, STIR
- Qabul qiluvchi (distributor) — manzil, STIR
- Tashuvchi (carrier) — STIR, mashina raqami, haydovchi F.I.O.
- Yuk: nomi, og'irlik, hajm, miqdor, narx
- Imzolar: zavod + haydovchi (yuklash) + distributor + haydovchi (tushirish)
- QR-kod (mobile scan uchun)

Hayot:
1. Zavod yuk yaratganda — TTN draft
2. Yuklash boshlanganda — TTN tasdiq, QR-kod
3. Yetkazilganda — distributor imzo, yakuniy hujjat
4. PDF saqlanadi, barcha tomonga yuboriladi (email, dastur ichi)

## 7. Arxitektura yondashuvi: 1 backend + 4 app

```
tendr-/
├── backend/                    ← 1 Python FastAPI (multi-tenant, role-based)
│   ├── app/
│   │   ├── api/v1/
│   │   │   ├── factory/        ← Factory-specific endpoints
│   │   │   ├── carrier/        ← Carrier-specific endpoints
│   │   │   ├── driver/         ← Driver-specific (mobile)
│   │   │   ├── distributor/    ← Distributor-specific endpoints
│   │   │   └── shared/         ← Auth, common
│   │   ├── models/             ← Shared DB models
│   │   ├── services/           ← Business logic
│   │   └── ...
│
├── apps/
│   ├── factory-web/            ← React + Vite + TS
│   ├── carrier-web/            ← React + Vite + TS  (hozirgi frontend bunga ko'chiriladi)
│   ├── driver-mobile/          ← React Native (Expo)
│   └── distributor-web/        ← React + Vite + TS
│
├── packages/
│   ├── api-client/             ← Shared TS SDK + types (OpenAPI auto-gen)
│   ├── ui/                     ← Shared design system
│   └── lib/                    ← Umumiy utilities (formatters, hooks)
│
└── docs/
```

## 8. Auth va rollar

**Multi-tenancy:** Har bir tashkilot — alohida tenant.

```
organizations
  - id, name, kind (factory | carrier | distributor)
  - carrier_type (hybrid | forwarder | asset_only)  -- faqat carrier uchun
  - tin (STIR)
  - ...

users
  - id, email, password
  - organization_id  -- qaysi tashkilotga tegishli
  - role (owner | admin | dispatcher | accountant | viewer)
  - kind (web_user | driver)   -- driver alohida

driver_profiles  -- userning kengaytmasi (faqat driver uchun)
  - user_id
  - license_number, photo, ...
```

**Frontend autentifikatsiyasi:**
- Har 4 app — bitta `/auth/login`
- Token ichida `organization_kind` + `role` claim
- Frontend o'sha asosida UI ko'rsatadi
- Backend ham har bir endpoint'da rol/kind tekshiradi

## 9. Integratsiyalar

| Tashqi | Ishlatilish | Bosqich |
|--------|-------------|---------|
| Yandex Maps | Xarita, navigatsiya | Phase 5 |
| Yandex Routing API | Aniq distance/ETA | Phase 5 |
| Lorry | Spot truck topish | Phase 7 (avtomatik scrape) |
| Telegram | Notifikatsiya + spot truck guruh | Phase 6 |
| SMS provider | Driver OTP, status notification | Phase 4 |
| Email | TTN PDF yuborish | Phase 3 |
| Payme/Click | To'lovlar (kelajakda) | Phase 8+ |

## 10. Bosqichlar — qayta ko'rib chiqilgan reja

| Phase | Mavzu | Status |
|-------|-------|--------|
| **0** | Foundation: monorepo, backend skeleton, SQLite | ✅ Done |
| **1** | Hozirgi carrier-only MVP (auth + CRUD + greedy assignment + dashboard) | ✅ Done |
| **2** | **Multi-tenant refactor** (organizations, role-based, 4 persona model) | ⏳ **Keyingi** |
| **3** | 4 ta frontend app skeleton + shared packages | ⏳ |
| **4** | Factory app: order creation + carrier distribution + tracking | ⏳ |
| **5** | Carrier app (kengaytirilgan): 3 tip + spot truck + multi-hop | ⏳ |
| **6** | Driver mobile (React Native): GPS + status + signature | ⏳ |
| **7** | Distributor app: receive + TTN + signature | ⏳ |
| **8** | TTN PDF generation + qonuniy hujjat oqimi | ⏳ |
| **9** | Real-time (WebSocket) + Lorry/Telegram integratsiya | ⏳ |
| **10** | Optimization (OR-Tools VRP) + analytics | ⏳ |

---

## Tasdiq kerak

Bu konsepsiya **siz aytgan biznes mantiqini to'liq qopladimi?** Quyidagilarni tasdiqlang:
- ✅ 4 persona to'g'rimi?
- ✅ Carrier 3 tipi to'g'rimi?
- ✅ Multi-hop assignment (Type 2 forwarder) to'g'rimi?
- ✅ TTN — sizning regionda haqiqatan ham kerakmi?
- ✅ 1 backend + 4 frontend yondashuvi qabulmi?
- ❓ Qaysi persona'dan boshlaymiz (factory yoki carrier'dan davom etamiz)?
- ❓ Mobile app — React Native yoki birinchi sinov uchun web mobile'ga moslashtirilgan?
