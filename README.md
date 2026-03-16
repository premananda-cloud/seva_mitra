# Seva Mitra — सेवा मित्र

**Smart & Efficient Virtual Assistant for Multilingual Integrated Transparent Resource Access**

A unified, multilingual, offline-first digital kiosk platform for citizen–government interactions.  
Built for SUVIDHA 2026 — organised by C-DAC under MeitY | Smart City 2.0 Initiative.

---

## Demo

[![Watch Demo](https://img.shields.io/badge/Watch%20Demo-YouTube-red?style=for-the-badge&logo=youtube)](https://your-demo-link-here)
[![Live Preview](https://img.shields.io/badge/Live%20Preview-Click%20Here-blue?style=for-the-badge)](https://your-live-link-here)

---

## What is Seva Mitra?

Seva Mitra is a public-facing, touch-based kiosk platform built for civic utility offices across India. It consolidates Electricity, Water, Gas, and Municipal services into a single, accessible interface — designed with every Indian citizen in mind, including those historically underserved by digital infrastructure.

Whether it is an elderly resident in a rural municipality, a Manipuri-speaking citizen in the Northeast, or someone operating in a low-connectivity environment — Seva Mitra is built to work for them.

---

## Key Features

### Multilingual First — 8 Indian Languages

- **Meitei-Mayek (Manipuri script)** — to our knowledge, the only civic kiosk platform in India with native Meitei-Mayek rendering
- Hindi · Bengali · Tamil · Telugu · Kannada · Malayalam · Odia
- Powered by `react-i18next` with full Unicode support

### Accessibility and Inclusive Design

The interface is designed with elderly and first-time users in mind. Large, high-contrast tap targets are optimised for kiosk touchscreens. Each screen presents a single action to reduce cognitive load. A `KeyboardContext`-driven virtual keyboard removes the dependency on physical input devices. Navigation is strictly linear — no hidden menus or nested flows that could disorient unfamiliar users.

### Offline-First Architecture

Service requests are queued in **IndexedDB** when internet connectivity is unavailable, and synced automatically on reconnect. No interaction is lost. The application ships with a PWA-ready manifest for permanent kiosk deployment.

### Security

- **JWT + bcrypt** authentication (cost factor 12)
- Role-based access control: citizen / admin / department
- **Razorpay** payment gateway integration — PCI-DSS compliant, with per-department API keys
- Pydantic v2 strict validation on all API inputs
- HTTPS enforced via Nginx TLS in production

### Backend Architecture

The backend is built on a modular **FastAPI** structure with 7 domain routers and 40+ endpoints, organised under `src/api/` using an app factory pattern with shared dependency injection. A **102-check smoke test suite** covers 15 API domains. Alembic handles database migrations for zero-downtime updates. Docker and docker-compose ensure reproducible deployments across environments.

---

## Departments Supported

| Department     | Services                                                       |
|----------------|----------------------------------------------------------------|
| Electricity    | Bill payment, new connection, meter change, service transfer   |
| Water Supply   | Bill payment, leak reporting, new connection                   |
| Gas            | Bill payment, new connection                                   |
| Municipal      | Waste management, civic complaints                             |

---

## Tech Stack

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

## Getting Started

### Prerequisites

- Node.js 18+
- Python 3.11+
- PostgreSQL 15+
- Docker (recommended)

### Quick Start with Docker

```bash
git clone https://github.com/premananda-cloud/KOISK_UI.git
cd KOISK_UI
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

## Running Tests

```bash
cd project/backend
python test_backend.py
```

102 checks across 15 API domains. All checks must pass before deployment.

---

## Language Configuration

Language files live in `src/locales/`. To add a new language:

1. Create `src/locales/{code}.json`
2. Register the locale entry in `i18n.js`
3. Add the language option to the language selector component

Current locales: `en`, `hi`, `bn`, `ta`, `te`, `kn`, `ml`, `or`, `ma` (Meitei-Mayek)

---

## Project Structure

```
KOISK_UI/
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
├── guidelines/
└── SUVIDHA_2026_KOISK_Technical_Proposal.docx
```

---

## Security Notes

- Passwords are hashed with bcrypt and never stored in plaintext
- JWT tokens with configurable expiry; kiosk sessions auto-expire after 30 minutes
- All payment flows are handled via Razorpay — card data never touches application servers
- SQL injection is prevented through SQLAlchemy ORM parameterisation
- CORS is restricted to permitted origins

---

## Request Status Flow

```
DRAFT → SUBMITTED → PROCESSING → APPROVED → COMPLETED
                                           ↘ REJECTED
```

Citizens can track request status in real time from any device.

---

## Team Pradix

Developed for SUVIDHA 2026 — C-DAC National Hackathon under the MeitY Smart City 2.0 Initiative.

---

## License

This project was developed for the SUVIDHA 2026 Hackathon. All rights reserved by Team Pradix.

---

*Seva Mitra — One kiosk. Every utility. Every language. Everywhere.*
