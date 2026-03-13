# 🏛️ KOISK — Smart Civic Utility Kiosk

> **SUVIDHA 2026** — A touch-optimised, multilingual digital kiosk for government utility services.

---

## 📹 Demo Video

<!-- ► Replace the URL below with your video link -->
> 🎬 **[Watch Demo Video](#)**

---

## 📌 Overview

KOISK (Kiosk for Utility Services) is a full-stack civic tech platform that brings government utility services online — eliminating the need for citizens to visit offices or wait in queues. Built for deployment on public kiosks and web browsers, it supports bill payments, service requests, and citizen complaints across three departments.

| Layer | Technology |
|---|---|
| Frontend | React 18 · Vite · Tailwind CSS · Zustand · i18next |
| Backend  | FastAPI · SQLAlchemy · SQLite (dev) · Uvicorn |
| Payments | Mock gateway (dev) · PortOne / Razorpay (prod-ready adapters) |
| Storage  | IndexedDB (offline-first) · SQLite backend |

---

## ✨ Features

- 🌐 **7 languages** — English, Hindi, Kannada, Tamil, Telugu, Marathi, Odia
- 💳 **Bill payments** — Electricity, Water, Municipal property tax via UPI / Card / Net Banking
- 📋 **Service requests** — New connections, meter change, service transfer, trade licences, certificates
- 🚰 **Complaints & grievances** — Water leak, sanitation, general grievance
- 📡 **Offline-first** — Payments queue locally (IndexedDB) and sync when back online
- 🔐 **Auth** — Phone + 4-digit PIN with local session management
- 🖨️ **Printable receipts** — Payment receipts with print-optimised CSS
- 🖥️ **Virtual keyboard** — On-screen keyboard for touch kiosk hardware
- 👤 **Admin panel** — Super-admin and department-scoped admin views (backend)

---

## 🗂️ Repository Structure

```
KOISK_UI/
│
├── UI_UX/                          ← React frontend (Vite)
│   ├── src/
│   │   ├── App.jsx                 ← Router + route definitions
│   │   ├── index.css               ← Tailwind + custom design tokens
│   │   ├── components/
│   │   │   ├── kiosk/
│   │   │   │   ├── Dashboard.jsx   ← Main service hub after login
│   │   │   │   ├── Keyboard.jsx    ← Virtual touch keyboard
│   │   │   │   └── KOISK_demo.jsx  ← Standalone UI prototype
│   │   │   ├── payment/
│   │   │   │   ├── PaymentFlow.jsx         ← 3-step payment wizard
│   │   │   │   ├── PaymentMethodSelector.jsx
│   │   │   │   ├── CardInput.jsx
│   │   │   │   ├── UPIInput.jsx
│   │   │   │   ├── ReceiptScreen.jsx       ← Post-payment receipt
│   │   │   │   └── OfflineBanner.jsx
│   │   │   └── departments/
│   │   │       ├── ServiceLayout.jsx       ← Shared dept screen shell
│   │   │       ├── ServiceRequestForm.jsx  ← Generic form → backend POST
│   │   │       ├── ElectricityScreen.jsx   ← ⚡ 4 services
│   │   │       ├── WaterScreen.jsx         ← 💧 3 services
│   │   │       └── MunicipalScreen.jsx     ← 🏛️ 7 services
│   │   ├── modules/
│   │   │   ├── auth/               ← Login · Register · Zustand authStore
│   │   │   ├── language/           ← i18n + LanguageSelect screen
│   │   │   ├── localdb/            ← IndexedDB wrapper (localDB.js)
│   │   │   ├── orchestrator/       ← Backend connector (auto-probe)
│   │   │   └── payment/            ← paymentService · paymentStore · constants
│   │   ├── context/
│   │   │   └── KeyboardContext.jsx
│   │   ├── hooks/
│   │   │   └── useKeyboardInput.js
│   │   └── config/
│   │       └── languages.js
│   ├── package.json
│   ├── tailwind.config.js
│   └── vite.config.js
│
├── src/                            ← FastAPI backend
│   ├── api/
│   │   ├── admin/router.py         ← Admin endpoints (super + dept scoped)
│   │   ├── electricity/router.py   ← /api/v1/electricity/*
│   │   ├── water/router.py         ← /api/v1/water/*
│   │   ├── municipal/router.py     ← /api/v1/municipal/*
│   │   ├── kiosk/router.py         ← OTP session management
│   │   └── payments/router.py      ← /api/v1/payments/*
│   ├── department/
│   │   └── database/database.py    ← SQLAlchemy setup
│   └── payment/
│       └── mock_payment_engine.py
│
├── main.py                         ← FastAPI app factory
├── requirements.txt
├── test_backend.py                 ← End-to-end smoke test (15 sections)
└── docs/
    ├── departments/                ← Per-department API READMEs
    └── SUVIDHA_Architecture_Flow.html
```

---

## 🚀 Getting Started

### Prerequisites

- Python 3.11+
- Node.js 18+

---

### 1. Clone the repository

```bash
git clone https://github.com/premananda-cloud/KOISK_UI.git
cd KOISK_UI
```

---

### 2. Backend setup

```bash
# Create and activate virtual environment
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate

# Install dependencies
pip install fastapi uvicorn sqlalchemy passlib python-jose httpx

# Start the backend (runs on port 8877)
uvicorn main:app --host 0.0.0.0 --port 8877 --reload
```

Backend is live at `http://127.0.0.1:8877`  
Swagger docs at `http://127.0.0.1:8877/docs`

---

### 3. Frontend setup

```bash
cd UI_UX

# Install dependencies
npm install

# Create environment file
echo "VITE_API_URL=http://127.0.0.1:8877" > .env

# Start dev server
npm run dev
```

Frontend is live at `http://localhost:5173`

---

### 4. Run the smoke test

```bash
# From project root (with venv active)
python test_backend.py
```

Runs 15 test sections covering health, auth, OTP sessions, all 3 departments, payments, admin panel, and session management.

---

## 🔌 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET  | `/health` | Health check + department list |
| POST | `/admin/login` | Admin authentication |
| GET  | `/admin/requests` | All citizen requests (filterable) |
| GET  | `/admin/payments` | All payment records |
| GET  | `/kiosk/departments` | Department + service catalogue |
| POST | `/kiosk/session/start` | Send OTP to citizen phone |
| POST | `/kiosk/session/verify-otp` | Verify OTP → issue session token |
| GET  | `/api/v1/electricity/bills/{user_id}` | Fetch electricity bills |
| POST | `/api/v1/electricity/pay-bill` | Pay electricity bill |
| POST | `/api/v1/electricity/new-connection` | Apply for new connection |
| POST | `/api/v1/electricity/meter-change` | Meter replacement request |
| POST | `/api/v1/electricity/transfer-service` | Service ownership transfer |
| GET  | `/api/v1/water/bills/{user_id}` | Fetch water bills |
| POST | `/api/v1/water/pay-bill` | Pay water bill |
| POST | `/api/v1/water/new-connection` | Apply for new water connection |
| POST | `/api/v1/water/leak-complaint` | Report a water leak |
| GET  | `/api/v1/municipal/bills/{user_id}` | Fetch municipal bills |
| POST | `/api/v1/municipal/property-tax` | Pay property tax |
| POST | `/api/v1/municipal/trade-license` | Trade licence (new / renewal) |
| POST | `/api/v1/municipal/birth-certificate` | Birth certificate application |
| POST | `/api/v1/municipal/death-certificate` | Death certificate application |
| POST | `/api/v1/municipal/building-plan` | Building plan approval |
| POST | `/api/v1/municipal/complaint` | Sanitation complaint |
| POST | `/api/v1/municipal/grievance` | General grievance |
| POST | `/api/v1/payments/initiate` | Create payment order |
| POST | `/api/v1/payments/complete` | Confirm payment |
| GET  | `/api/v1/payments/history/{user_id}` | Payment history |

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────┐
│               React Frontend (Vite)             │
│  Language → Login → Dashboard → Dept Screen     │
│       ↕ Zustand stores  ↕ IndexedDB             │
│     Orchestrator (auto-probes backend)          │
└──────────────────┬──────────────────────────────┘
                   │ HTTP (axios / fetch)
                   │ VITE_API_URL=http://127.0.0.1:8877
                   ▼
┌─────────────────────────────────────────────────┐
│              FastAPI Backend                    │
│   /admin  /kiosk  /electricity  /water          │
│   /municipal  /payments                         │
│         ↕ SQLAlchemy ORM                        │
│              SQLite DB                          │
└─────────────────────────────────────────────────┘
```

**Offline-first flow:** If the backend is unreachable, the orchestrator automatically falls back to mock mode. Payments are queued in IndexedDB and replayed when connectivity is restored.

---

## 🌐 Supported Languages

| Code | Language | Native Name |
|------|----------|-------------|
| `en` | English  | English  |
| `hi` | Hindi    | हिन्दी   |
| `kn` | Kannada  | ಕನ್ನಡ    |
| `ta` | Tamil    | தமிழ்    |
| `te` | Telugu   | తెలుగు   |
| `mr` | Marathi  | मराठी    |
| `od` | Odia     | ଓଡ଼ିଆ    |

---

## 💳 Payment Flow

```
Dashboard
  └─ Dept Screen (Electricity / Water / Municipal)
       └─ "Pay Bill" tile
            └─ PaymentFlow modal
                 ├─ Step 1: Bill Summary   (amount, consumer no, due date)
                 ├─ Step 2: Method Select  (UPI · Card · Net Banking)
                 └─ Step 3: Receipt        (reference no, print option)
```

In **development**: mock gateway with 1-in-20 simulated failure rate.  
In **production**: swap orchestrator flags to connect PortOne or Razorpay adapters.

---

## 👤 Admin Panel

The backend exposes a full admin API:

- **Super Admin** — sees all departments, all requests, all payments, manages kiosk config
- **Department Admin** — scoped to their own department only

Default super-admin credentials (change before production):
```
Username : admin
Password : (set in your .env / database seed)
```

---

## 🧪 Test Coverage

`test_backend.py` covers 15 end-to-end sections:

1. Health check
2. Admin authentication (good + bad password, token guard)
3. Kiosk department catalogue
4. OTP session — new citizen
5. OTP session — returning citizen
6. Electricity department (bills, pay, new connection, meter change, transfer)
7. Water department (bills, pay, new connection, leak complaint)
8. Municipal department (bills, property tax, trade licence, certificates, complaints, grievance)
9. Payments API (initiate, complete, history)
10. Admin request management + filtering
11. Admin payments view + filtering
12. Kiosk config (super-admin)
13. Shared request lookup
14. Kiosk session end & token invalidation
15. Department admin scoped access

---

## 🔧 Known Issues / TODO

- [ ] Fix `payments.reference_no` UNIQUE collision when test DB is not wiped between runs (use UUID suffix or wipe DB before each test run)
- [ ] Fix `admins.email` UNIQUE error in test section 15 on second run (use upsert in test setup)
- [ ] Replace plain PIN hash with `bcrypt` before production
- [ ] Integrate real SMS provider for OTP (placeholder log line in kiosk router)
- [ ] Add `python-jose` + `passlib` for full JWT auth on admin endpoints
- [ ] Build Admin frontend (separate React app or route-gated section)

---

## 📦 Tech Stack

**Frontend**
- React 18 · React Router v6
- Vite 7
- Tailwind CSS 3
- Zustand (state management)
- i18next + react-i18next (multilingual)
- idb (IndexedDB wrapper)
- axios · lucide-react · clsx

**Backend**
- FastAPI 0.135
- SQLAlchemy 2.0
- Uvicorn
- SQLite (dev) — swap to PostgreSQL for production
- httpx (async HTTP in tests)

---

## 📄 Licence

This project was built for **SUVIDHA 2026**. All rights reserved to the respective contributors.

---

*KOISK — Making government services simple, one tap at a time.* 🏛️
