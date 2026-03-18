# Seva Mitra — सेवा मित्र

### Smart & Efficient Virtual Assistant for Multilingual Integrated Transparent Resource Access

> A unified, multilingual, offline-first digital kiosk for citizen–government interactions.
> Built for SUVIDHA 2026 — organized by C-DAC under MeitY | Smart City 2.0 Initiative.

---

## 🎬 Demo

[![Watch Demo](https://img.shields.io/badge/%E2%96%B6%20Watch%20Demo-YouTube-red?style=for-the-badge&logo=youtube)](https://your-demo-link-here)
[![Live Preview](https://img.shields.io/badge/%F0%9F%8C%90%20Live%20Preview-Click%20Here-blue?style=for-the-badge)](https://your-live-link-here)

---

## What is Seva Mitra?

Seva Mitra is a public-facing, touch-based kiosk platform designed for civic utility offices across India. It brings together Electricity, Water, Gas, and Municipal services into a single, accessible interface — built for every Indian citizen, including those the system has traditionally left behind.

Whether it's an elderly resident in a rural municipality, a Manipuri-speaking citizen in the Northeast, or someone in a low-connectivity area — Seva Mitra works for them.

---

## ✨ Key Features

### 🌐 Multilingual First — 8 Indian Languages

- **Meitei-Mayek (Manipuri script)** — the only civic kiosk platform in India with native Meitei-Mayek rendering
- Hindi · Bengali · Tamil · Telugu · Kannada · Malayalam · Odia
- Powered by `react-i18next` with full Unicode support

### ♿ Designed for Senior Citizens

- Large, high-contrast tap targets optimised for kiosk touchscreens
- Minimal text per screen — one action at a time
- Virtual keyboard via `KeyboardContext` for kiosk-mode input
- Simple, linear navigation — no hidden menus or nested flows

### 📡 Offline-First Architecture

- Service requests queued in **IndexedDB** when internet is unavailable
- Automatic sync on reconnect — zero lost interactions
- PWA-ready manifest for kiosk deployment

### 🔒 Secure by Design

- **JWT + bcrypt** authentication (cost factor 12)
- Role-based access: citizen / admin / department
- **Razorpay** payment gateway — PCI-DSS compliant, per-department keys
- Pydantic v2 strict validation on all API inputs
- HTTPS enforced via Nginx TLS in production

### 🏗️ Production-Grade Backend

- Modular **FastAPI** architecture — 7 domain routers, 40+ endpoints
- `src/api/` structure with app factory and shared dependency injection
- **102-check smoke test suite** across 15 API domains
- Alembic migrations for zero-downtime database updates
- Docker + docker-compose for reproducible deployments

---

## 🏛️ Departments Supported

| Department | Services |
|---|---|
| ⚡ Electricity | Bill payment, new connection, meter change, service transfer |
| 💧 Water Supply | Bill payment, leak reporting, new connection |
| 🔥 Gas | Bill payment, new connection |
| 🏙️ Municipal | Waste management, civic complaints |

---

## 🛠️ Tech Stack

**Frontend**
- React 18 + Vite
- Tailwind CSS
- react-i18next (i18n)
- Zustand (state management)
- Axios + IndexedDB offline queue

**Backend**
- FastAPI + Uvicorn
- SQLAlchemy 2.0 + PostgreSQL
- Alembic (migrations)
- bcrypt + JWT (OAuth2)
- Pydantic v2
- Razorpay SDK

**Infrastructure**
- Docker + docker-compose
- Nginx (TLS reverse proxy)
- GitHub CI

---

## 🚀 Getting Started

### Prerequisites

- Node.js 18+
- Python 3.11+
- PostgreSQL 15+
- Docker (recommended)

### Quick Start with Docker

```bash
git clone https://github.com/premananda-cloud/seva_mitra.git
cd seva_mitra
cp .env.example .env        # fill in your DB and Razorpay credentials
docker-compose up --build
```

Frontend: `http://localhost:5173`
API: `http://localhost:8000`
API Docs: `http://localhost:8000/docs`

### Manual Setup

**Backend**

```bash
cd project/backend
pip install -r requirements.txt
alembic upgrade head
uvicorn src.main:app --reload
```

**Frontend**

```bash
cd project/frontend
npm install
npm run dev
```

---

## 🧪 Running Tests

```bash
cd project/backend
python test_backend.py
```

102 checks across 15 API domains. All must pass before deployment.

---

## 🌍 Language Configuration

Language files live in `src/locales/`. To add a new language:

1. Create `src/locales/{code}.json`
2. Add the locale entry in `i18n.js`
3. Add the language option in the language selector component

Current locales: `en`, `hi`, `bn`, `ta`, `te`, `kn`, `ml`, `or`, `ma` (Meitei-Mayek)

---

## 📁 Project Structure

```
seva_mitra/
├── project/
│   ├── frontend/
│   │   ├── src/
│   │   │   ├── components/     # UI components
│   │   │   ├── screens/        # Page-level screens
│   │   │   ├── locales/        # i18n language files (incl. ma.json)
│   │   │   ├── context/        # KeyboardContext, AuthContext
│   │   │   └── utils/          # Offline queue, API helpers
│   │   └── package.json
│   └── backend/
│       ├── src/
│       │   ├── api/            # 7 domain routers
│       │   │   ├── admin.py
│       │   │   ├── electricity.py
│       │   │   ├── water.py
│       │   │   ├── municipal.py
│       │   │   ├── kiosk.py
│       │   │   ├── payments.py
│       │   │   └── shared.py
│       │   ├── models.py       # Pydantic v2 schemas
│       │   ├── database.py     # SQLAlchemy engine + session
│       │   └── main.py         # App factory (~21 lines)
│       ├── test_backend.py     # 102-check smoke suite
│       └── requirements.txt
├── docs/
├── UI_UX/
└── architecture.txt
```

---

## 🔒 Security

- Passwords hashed with bcrypt (never stored in plaintext)
- JWT tokens with configurable expiry + auto-logout after 30 min (kiosk mode)
- All payments processed via Razorpay — card data never touches our servers
- SQL injection prevention via SQLAlchemy ORM parameterisation
- CORS restricted to allowed origins

---

## 📊 Request Status Flow

```
DRAFT → SUBMITTED → PROCESSING → APPROVED → COMPLETED
                                           ↘ REJECTED
```

Citizens can track their request status in real time from any device.

---

## 🤝 Team Praxis

Built with care for SUVIDHA 2026 — C-DAC National Hackathon under MeitY Smart City 2.0 Initiative.

---

## 📄 License

This project was developed for the SUVIDHA 2026 Hackathon. All rights reserved by Team Praxis.

---

> *Seva Mitra — One kiosk. Every utility. Every language. Everywhere.*
