# Seva Mitra — सेवा मित्र

**Smart & Efficient Virtual Assistant for Multilingual Integrated Transparent Resource Access**

A unified, multilingual, offline-first digital kiosk platform for citizen–government interactions.  
Built for SUVIDHA 2026 — organised by C-DAC under MeitY | Smart City 2.0 Initiative.

---

## Demo

[![Watch Demo](https://img.shields.io/badge/Watch%20Demo-YouTube-red?style=for-the-badge&logo=youtube)](https://your-demo-link-here)
[![Live Preview](https://img.shields.io/badge/Live%20Preview-Click%20Here-blue?style=for-the-badge)](https://your-live-link-here)

---

## Test Results

[![Tests](https://img.shields.io/badge/Tests-149%20passed%2C%202%20skipped-brightgreen?style=for-the-badge)](./tests/)
[![Coverage](https://img.shields.io/badge/Coverage-Unit%20%2B%20Integration-teal?style=for-the-badge)](./tests/)
[![Runner](https://img.shields.io/badge/Runner-pytest%209.0-blue?style=for-the-badge)](./pytest.ini)

```
149 passed · 2 skipped · 0 failed   (pytest 9.0 · Python 3.12 · ~7 seconds)
```

| Suite | File | Tests |
|---|---|---|
| Authentication & Authorisation | `tests/interation/test_auth.py` | 16 |
| Kiosk Session & OTP Flow | `tests/interation/test_kiosk.py` | 20 |
| Department Endpoints | `tests/interation/test_departments.py` | 57 |
| Payments API & Admin Dashboard | `tests/interation/test_payments_and_admin.py` | 32 |
| Unit Tests — Business Logic | `tests/unit/test_business_logic.py` | 36 |

The 2 skipped tests are bcrypt-variant checks that skip automatically when the bcrypt backend is unavailable in the test environment — the underlying password security is covered by 6 additional passing tests in the same class.

A full test report is available at [`tests/KOISK_Test_Report.docx`](./tests/KOISK_Test_Report.docx).

---

## What is Seva Mitra?

Seva Mitra is a public-facing, touch-based kiosk platform built for civic utility offices across India. It consolidates Electricity, Water, Gas, and Municipal services into a single, accessible interface — designed with every Indian citizen in mind, including those historically underserved by digital infrastructure.

Whether it is an elderly resident in a rural municipality, a Manipuri-speaking citizen in the Northeast, or someone operating in a low-connectivity environment — Seva Mitra is built to work for them.

---

## Key Features

### Multilingual First — 8 Indian Languages

- **Meitei-Mayek (Manipuri script)** — to our knowledge, the only civic kiosk platform in India with native Meitei-Mayek rendering
- Hindi · Tamil · Telugu · Kannada · Odia · Marathi · English
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

The backend is built on a modular **FastAPI** structure with 7 domain routers and 40+ endpoints, organised under `src/api/` using an app factory pattern with shared dependency injection. A **149-test pytest suite** covers unit logic and full API integration across all departments.

---

## Departments Supported

| Department | Services |
|---|---|
| Electricity | Bill payment · New connection · Meter change · Service transfer |
| Water Supply | Bill payment · Leak reporting · New connection |
| Gas | Bill payment · New connection |
| Municipal | Property tax · Trade license · Birth / Death certificate · Building plan · Complaints · Grievances |

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
- SQLAlchemy 2.0 + SQLite / PostgreSQL
- bcrypt + JWT (OAuth2)
- Pydantic v2
- Razorpay SDK

**Testing**
- pytest 9.0
- FastAPI TestClient + httpx
- SQLite in-memory / file-based isolated test DB
- 149 tests across 5 test modules

**Infrastructure**
- Docker + docker-compose
- Nginx (TLS reverse proxy)
- GitHub CI

---

## Getting Started

### Prerequisites

- Node.js 18+
- Python 3.11+
- PostgreSQL 15+ (SQLite supported for development)
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
pip install -r requirements.txt
uvicorn main:app --reload
```

**Frontend**

```bash
cd UI_UX
npm install
npm run dev
```

---

## Running Tests

### Install test dependencies

```bash
pip install pytest httpx
```

### Run the full suite

```bash
python -m pytest tests/ -v
```

Expected output:

```
149 passed, 2 skipped in ~7 seconds
```

### Run only unit tests

```bash
python -m pytest tests/unit/ -v
```

### Run only integration tests

```bash
python -m pytest tests/interation/ -v
```

### Test structure

```
tests/
├── conftest.py                        # shared fixtures, isolated DB, engine redirect
├── pytest.ini                         # test discovery config
├── KOISK_Test_Report.docx             # full test report
├── unit/
│   └── test_business_logic.py         # OTP, password hashing, payment refs, catalogue
└── interation/
    ├── test_auth.py                   # login, JWT, role-based access control
    ├── test_kiosk.py                  # OTP session lifecycle, department catalogue
    ├── test_departments.py            # electricity / water / municipal endpoints
    └── test_payments_and_admin.py     # payment lifecycle, admin dashboard, kiosk config
```

### What the tests prove

| Area | What is verified |
|---|---|
| Authentication | Correct credentials issue JWT · Bad credentials return 401 · No token returns 401 |
| Role-based access | Dept admins scoped to their department · Super-admin-only endpoints return 403 |
| OTP security | 6-digit SHA-256 hashed OTPs · Wrong OTP returns 400 · Ended tokens invalidated |
| Payment lifecycle | Initiate → Complete → Receipt · Missing fields return 422 |
| Department services | Bill payment, new connections, complaints, certificates — all 3 departments |
| Admin dashboard | Request approve / deny / deliver transitions · Nonexistent IDs return 404 |
| Input validation | All required fields enforced · Malformed requests return 422, not 500 |

### Legacy smoke test

The original 102-check smoke test is also retained:

```bash
python test_backend.py
```

---

## Language Configuration

Language files live in `UI_UX/src/modules/language/locales/`. To add a new language:

1. Create `locales/{code}.json`
2. Register the locale in `i18n.js`
3. Add the option to the language selector component

Current locales: `en` · `hi` · `ma` (Meitei-Mayek) · `ta` · `te` · `kn` · `od` · `mr`

---

## Project Structure

```
seva_mitra/
├── main.py                         # FastAPI app factory
├── requirements.txt
├── test_backend.py                 # legacy 102-check smoke suite
├── pytest.ini
├── src/
│   ├── api/                        # 7 domain routers
│   │   ├── admin/
│   │   ├── electricity/
│   │   ├── water/
│   │   ├── municipal/
│   │   ├── kiosk/
│   │   ├── payments/
│   │   └── shared/
│   ├── database/
│   │   ├── models.py
│   │   └── database.py
│   └── payment/
│       ├── mock_payment_engine.py
│       └── payment_handler.py
├── UI_UX/                          # React + Vite frontend
│   ├── src/
│   │   ├── components/
│   │   ├── modules/
│   │   │   └── language/locales/   # i18n files incl. ma.json (Meitei-Mayek)
│   │   └── hooks/
│   └── package.json
├── tests/
│   ├── conftest.py
│   ├── KOISK_Test_Report.docx
│   ├── unit/
│   └── interation/
├── database/
└── docs/
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
SUBMITTED → PROCESSING → APPROVED → DELIVERED
                                   ↘ DENIED
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
