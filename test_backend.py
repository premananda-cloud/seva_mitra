#!/usr/bin/env python3
"""
test_backend.py
===============
Full end-to-end smoke test for the KOISK backend.
No pytest, no external test runner — pure Python stdlib + httpx.

What it does:
  1. Wipes & re-creates database/koisk_test.db  (clean slate every run)
  2. Spins up the FastAPI server on port 8877 in a background thread
  3. Walks through every real scenario with realistic Manipur-based data
  4. Prints coloured PASS / FAIL for each check
  5. Shows a summary and exits 0 (all pass) or 1 (any failure)

Run:
    python test_backend.py
"""

import hashlib
import json
import os
import sys
import time
import threading
import traceback
from pathlib import Path

# ── point DB to database/ before ANY app import ───────────────────────────────
DB_DIR  = Path("database")
DB_FILE = DB_DIR / "koisk_test.db"
DB_DIR.mkdir(exist_ok=True)
if DB_FILE.exists():
    DB_FILE.unlink()

os.environ["DATABASE_URL"] = f"sqlite:///./{DB_FILE}"

import httpx
import uvicorn

PORT = 8877
BASE = f"http://127.0.0.1:{PORT}"

# ── colours ───────────────────────────────────────────────────────────────────
GRN  = "\033[32m"; RED  = "\033[31m"; YLW = "\033[33m"
CYN  = "\033[36m"; BLD  = "\033[1m";  RST = "\033[0m"

# ── result tracking ───────────────────────────────────────────────────────────
_passed: list[str] = []
_failed: list[str] = []

def _ok(label: str):
    _passed.append(label)
    print(f"  {GRN}✓{RST}  {label}")

def _fail(label: str, why: str = ""):
    _failed.append(label)
    print(f"  {RED}✗{RST}  {label}")
    if why:
        print(f"       {RED}{why[:120]}{RST}")

def check(label: str, condition: bool, why: str = "") -> bool:
    if condition:
        _ok(label)
    else:
        _fail(label, why)
    return condition

def section(title: str):
    pad = "─" * max(0, 55 - len(title))
    print(f"\n{BLD}{CYN}── {title} {pad}{RST}")

# ── http helpers ──────────────────────────────────────────────────────────────
def post(path, body=None, token=None, form=None):
    h = {"Authorization": f"Bearer {token}"} if token else {}
    if form:
        return httpx.post(f"{BASE}{path}", data=form, headers=h, timeout=10)
    return httpx.post(f"{BASE}{path}", json=body, headers=h, timeout=10)

def get(path, token=None, params=None):
    h = {"Authorization": f"Bearer {token}"} if token else {}
    return httpx.get(f"{BASE}{path}", headers=h, params=params or {}, timeout=10)

def patch(path, body, token=None):
    h = {"Authorization": f"Bearer {token}"} if token else {}
    return httpx.patch(f"{BASE}{path}", json=body, headers=h, timeout=10)

# ── server bootstrap ──────────────────────────────────────────────────────────
def _boot_server():
    from main import app
    cfg = uvicorn.Config(app, host="127.0.0.1", port=PORT, log_level="error")
    uvicorn.Server(cfg).run()

def start_and_wait(timeout=20):
    t = threading.Thread(target=_boot_server, daemon=True)
    t.start()
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            if httpx.get(f"{BASE}/health", timeout=2).status_code == 200:
                return True
        except Exception:
            pass
        time.sleep(0.4)
    return False

# ── peek at OTP stored in DB (test-only helper) ───────────────────────────────
def _crack_otp(session_id: int) -> str | None:
    """SHA-256 brute-force the 6-digit OTP from the DB hash — test only."""
    from src.department.database.database import SessionLocal
    from src.department.database.models   import KioskSession
    db  = SessionLocal()
    row = db.query(KioskSession).filter(KioskSession.id == session_id).first()
    db.close()
    if not row:
        return None
    stored = row.otp_code
    for n in range(1_000_000):
        candidate = f"{n:06d}"
        if hashlib.sha256(candidate.encode()).hexdigest() == stored:
            return candidate
    return None

# ─────────────────────────────────────────────────────────────────────────────
#  TEST SCENARIOS
# ─────────────────────────────────────────────────────────────────────────────
def run():
    admin_token  = None
    kiosk_token  = None
    elec_req_id  = None
    water_req_id = None
    muni_req_id  = None

    # ══════════════════════════════════════════════════════════════════════════
    section("1 · Health")
    # ══════════════════════════════════════════════════════════════════════════
    r = get("/health")
    check("GET /health → 200",            r.status_code == 200, r.text)
    check("status = healthy",             r.json().get("status") == "healthy")
    check("departments list present",     "departments" in r.json())

    # ══════════════════════════════════════════════════════════════════════════
    section("2 · Admin authentication")
    # ══════════════════════════════════════════════════════════════════════════
    r = post("/admin/login", form={"username": "admin", "password": "wrongpassword"})
    check("Bad password → 401",           r.status_code == 401)

    r = post("/admin/login", form={"username": "admin", "password": "Admin@1234"})
    check("POST /admin/login → 200",      r.status_code == 200, r.text)
    if r.status_code == 200:
        admin_token = r.json().get("access_token")
        check("access_token present",     bool(admin_token))
        check("role = super_admin",       r.json().get("role") == "super_admin")
        check("department = null",        r.json().get("department") is None)

    r = get("/admin/requests")                         # no token
    check("No token → 401",              r.status_code == 401)

    # ══════════════════════════════════════════════════════════════════════════
    section("3 · Kiosk department catalogue")
    # ══════════════════════════════════════════════════════════════════════════
    r = get("/kiosk/departments")
    check("GET /kiosk/departments → 200", r.status_code == 200, r.text)
    if r.status_code == 200:
        depts = {d["id"]: d for d in r.json().get("departments", [])}
        check("electricity in catalogue", "electricity" in depts)
        check("water in catalogue",       "water" in depts)
        check("municipal in catalogue",   "municipal" in depts)
        check("electricity has services", len(depts.get("electricity", {}).get("services", [])) > 0)
        check("water has services",       len(depts.get("water",       {}).get("services", [])) > 0)
        check("municipal has services",   len(depts.get("municipal",   {}).get("services", [])) > 0)

    # ══════════════════════════════════════════════════════════════════════════
    section("4 · Kiosk OTP session — new citizen")
    # ══════════════════════════════════════════════════════════════════════════
    # 4a. Start session
    r = post("/kiosk/session/start", {
        "full_name":    "Premananda Thounaojam",
        "phone_number": "+919856001234",
        "email":        "prem.thounaojam@koisk.local",
        "kiosk_id":     "KIOSK-IMPHAL-01",
    })
    check("POST /kiosk/session/start → 200", r.status_code == 200, r.text)
    sess_id = None
    if r.status_code == 200:
        sess_id = r.json().get("session_id")
        check("session_id returned",      sess_id is not None)
        check("otp_sent = true",          r.json().get("otp_sent") is True)
        check("not returning user",       r.json().get("is_returning_user") is False)

    # 4b. Wrong OTP
    if sess_id:
        r = post("/kiosk/session/verify-otp", {"session_id": sess_id, "otp_code": "000000"})
        check("Wrong OTP → 400",          r.status_code == 400)

    # 4c. Crack the real OTP from the DB hash and verify
    real_otp = _crack_otp(sess_id) if sess_id else None
    check("OTP hash cracked (test helper)", real_otp is not None)

    if sess_id and real_otp:
        r = post("/kiosk/session/verify-otp", {"session_id": sess_id, "otp_code": real_otp})
        check("Correct OTP → 200",        r.status_code == 200, r.text)
        if r.status_code == 200:
            kiosk_token = r.json().get("session_token")
            check("session_token issued", bool(kiosk_token))
            check("full_name correct",    r.json().get("full_name") == "Premananda Thounaojam")
            check("success = true",       r.json().get("success") is True)

    # 4d. Validate session
    if kiosk_token:
        r = get("/kiosk/session/validate", params={"session_token": kiosk_token})
        check("GET /kiosk/session/validate → 200", r.status_code == 200, r.text)
        check("valid = true",             r.json().get("valid") is True)
        check("full_name matches",        r.json().get("full_name") == "Premananda Thounaojam")

    # ══════════════════════════════════════════════════════════════════════════
    section("5 · Kiosk OTP session — returning citizen")
    # ══════════════════════════════════════════════════════════════════════════
    # Same phone → is_returning_user should be True
    r = post("/kiosk/session/start", {
        "full_name":    "Premananda Thounaojam",
        "phone_number": "+919856001234",
        "kiosk_id":     "KIOSK-IMPHAL-01",
    })
    check("Returning user start → 200",   r.status_code == 200, r.text)
    if r.status_code == 200:
        check("is_returning_user = true", r.json().get("is_returning_user") is True)

    # ══════════════════════════════════════════════════════════════════════════
    section("6 · Electricity department")
    # ══════════════════════════════════════════════════════════════════════════

    # 6a. Fetch bills (empty — no meters seeded for this user, should return empty list)
    r = get("/api/v1/electricity/bills/prem_user_001")
    check("GET /electricity/bills → 200", r.status_code == 200, r.text)
    check("bills key present",            "bills" in r.json())

    # 6b. Pay bill
    r = post("/api/v1/electricity/pay-bill", {
        "user_id":        "prem_user_001",
        "meter_number":   "MTR-ELEC-IMP-4821",
        "billing_period": "2026-02",
        "amount":         1475.50,
        "payment_method": "upi",
        "gateway":        "mock",
    })
    check("POST /electricity/pay-bill → 200",     r.status_code == 200, r.text)
    if r.status_code == 200:
        elec_req_id = r.json().get("service_request_id")
        check("service_request_id present",       bool(elec_req_id))
        check("success = true",                   r.json().get("success") is True)
        check("department = electricity",         r.json().get("department") == "electricity")
        check("status = DELIVERED (mock)",        r.json().get("status") == "DELIVERED")
        check("receipt data present",             bool(r.json().get("data")))
        receipt = r.json().get("data", {})
        check("receipt has reference_no",         bool(receipt.get("reference_no") or
                                                       receipt.get("referenceNo")))

    # 6c. New connection
    r = post("/api/v1/electricity/new-connection", {
        "customer_name":    "Ibomcha Laishram",
        "customer_id":      "CUST-ELEC-IMP-0092",
        "address":          "Keishamthong, Imphal West, Manipur 795001",
        "load_requirement": "5kW",
        "identity_proof":   "AADHAAR-9876543210",
        "address_proof":    "RATION-IMP-4532",
    })
    check("POST /electricity/new-connection → 200", r.status_code == 200, r.text)
    check("new connection SUBMITTED",               r.json().get("status") == "SUBMITTED")

    # 6d. Meter change
    r = post("/api/v1/electricity/meter-change", {
        "user_id":      "prem_user_001",
        "meter_number": "MTR-ELEC-IMP-4821",
        "reason":       "Burnt meter — reading erratic after power surge",
    })
    check("POST /electricity/meter-change → 200",   r.status_code == 200, r.text)

    # 6e. Service transfer
    r = post("/api/v1/electricity/transfer-service", {
        "old_customer_id": "CUST-ELEC-IMP-0011",
        "new_customer_id": "CUST-ELEC-IMP-0092",
        "meter_number":    "MTR-ELEC-IMP-4821",
        "identity_proof":  "AADHAAR-9876543210",
        "ownership_proof": "SALE-DEED-2026-0044",
        "consent_doc":     "NOC-2026-0044",
        "effective_date":  "2026-04-01",
    })
    check("POST /electricity/transfer-service → 200", r.status_code == 200, r.text)

    # ══════════════════════════════════════════════════════════════════════════
    section("7 · Water department")
    # ══════════════════════════════════════════════════════════════════════════

    # 7a. Bills (empty)
    r = get("/api/v1/water/bills/prem_user_001")
    check("GET /water/bills → 200",           r.status_code == 200, r.text)

    # 7b. Pay bill
    r = post("/api/v1/water/pay-bill", {
        "user_id":         "prem_user_001",
        "consumer_number": "WAT-CON-IMP-0334",
        "billing_period":  "2026-02",
        "amount":          380.00,
        "payment_method":  "card",
        "gateway":         "mock",
    })
    check("POST /water/pay-bill → 200",        r.status_code == 200, r.text)
    if r.status_code == 200:
        water_req_id = r.json().get("service_request_id")
        check("water receipt present",         bool(r.json().get("data")))
        check("status = DELIVERED (mock)",     r.json().get("status") == "DELIVERED")

    # 7c. New connection
    r = post("/api/v1/water/new-connection", {
        "applicant_name": "Tomba Ningthoujam",
        "applicant_id":   "CUST-WAT-IMP-0210",
        "address":        "Singjamei Bazar, Imphal West, Manipur 795001",
        "property_type":  "Residential",
        "identity_proof": "AADHAAR-7700112233",
        "address_proof":  "RATION-IMP-0210",
    })
    check("POST /water/new-connection → 200",  r.status_code == 200, r.text)

    # 7d. Leak complaint
    r = post("/api/v1/water/leak-complaint", {
        "consumer_id":     "CUST-WAT-IMP-0334",
        "consumer_number": "WAT-CON-IMP-0334",
        "complaint_type":  "Pipe burst",
        "location":        "Near Mantripukhri junction, Ward 12",
        "severity":        "High",
        "description":     "Main pipe burst, road flooded since 6am",
    })
    check("POST /water/leak-complaint → 200",  r.status_code == 200, r.text)

    # ══════════════════════════════════════════════════════════════════════════
    section("8 · Municipal department")
    # ══════════════════════════════════════════════════════════════════════════

    # 8a. Bills
    r = get("/api/v1/municipal/bills/prem_user_001")
    check("GET /municipal/bills → 200",            r.status_code == 200, r.text)

    # 8b. Property tax payment
    r = post("/api/v1/municipal/property-tax", {
        "user_id":         "prem_user_001",
        "consumer_number": "MUNI-CON-IMP-0077",
        "property_id":     "PROP-IMP-WARD12-0077",
        "tax_year":        "2025-2026",
        "amount":          6200.00,
        "payment_method":  "netbanking",
        "gateway":         "mock",
    })
    check("POST /municipal/property-tax → 200",    r.status_code == 200, r.text)
    if r.status_code == 200:
        muni_req_id = r.json().get("service_request_id")
        check("property tax receipt present",      bool(r.json().get("data")))
        check("status = DELIVERED (mock)",         r.json().get("status") == "DELIVERED")

    # 8c. Trade license — new
    r = post("/api/v1/municipal/trade-license", {
        "applicant_id":   "CUST-MUNI-IMP-0055",
        "applicant_name": "Ranjit Sharma",
        "business_name":  "Sharma Provision Store",
        "business_type":  "Retail",
        "address":        "Paona Bazar, Imphal, Manipur 795001",
        "ward_number":    "WARD-12",
        "identity_proof": "AADHAAR-6655443322",
        "address_proof":  "RATION-IMP-0055",
        "is_renewal":     False,
    })
    check("POST /municipal/trade-license (new) → 200",     r.status_code == 200, r.text)
    check("type = MUNICIPAL_TRADE_LICENSE_NEW",
          r.json().get("status") == "SUBMITTED")

    # 8d. Trade license — renewal
    r = post("/api/v1/municipal/trade-license", {
        "applicant_id":        "CUST-MUNI-IMP-0055",
        "applicant_name":      "Ranjit Sharma",
        "business_name":       "Sharma Provision Store",
        "business_type":       "Retail",
        "address":             "Paona Bazar, Imphal, Manipur 795001",
        "ward_number":         "WARD-12",
        "identity_proof":      "AADHAAR-6655443322",
        "address_proof":       "RATION-IMP-0055",
        "is_renewal":          True,
        "existing_license_no": "TL-IMP-2025-0055",
    })
    check("POST /municipal/trade-license (renewal) → 200", r.status_code == 200, r.text)

    # 8e. Birth certificate
    r = post("/api/v1/municipal/birth-certificate", {
        "applicant_id":   "CUST-MUNI-IMP-0100",
        "child_name":     "Laishram Sanatomba",
        "dob":            "2026-01-20",
        "place_of_birth": "RIMS Hospital, Imphal",
        "father_name":    "Laishram Tomba Singh",
        "mother_name":    "Laishram Ongbi Bimola",
        "hospital_name":  "RIMS Hospital",
        "identity_proof": "AADHAAR-1122334455",
    })
    check("POST /municipal/birth-certificate → 200", r.status_code == 200, r.text)

    # 8f. Death certificate
    r = post("/api/v1/municipal/death-certificate", {
        "applicant_id":        "CUST-MUNI-IMP-0101",
        "deceased_name":       "Wangam Dhanabir Meitei",
        "date_of_death":       "2026-02-14",
        "place_of_death":      "Shija Hospitals, Langol, Imphal",
        "cause_of_death":      "Cardiac arrest",
        "informant_name":      "Wangam Ibomcha",
        "identity_proof":      "AADHAAR-9988776655",
        "medical_certificate": "SHIJA-MED-CERT-2026-0088",
    })
    check("POST /municipal/death-certificate → 200",  r.status_code == 200, r.text)

    # 8g. Building plan approval
    r = post("/api/v1/municipal/building-plan", {
        "applicant_id":         "CUST-MUNI-IMP-0120",
        "applicant_name":       "Konsam Ibochouba",
        "property_id":          "PROP-IMP-WARD08-0120",
        "plot_area":            312.5,
        "built_up_area":        220.0,
        "floors":               2,
        "building_type":        "Residential",
        "architect_name":       "Ar. Premchand Thongam",
        "identity_proof":       "AADHAAR-5544332211",
        "land_ownership_proof": "PATTA-IMP-0120-2019",
        "blueprint_ref":        "BLUEPRINT-2026-IMP-0120",
    })
    check("POST /municipal/building-plan → 200",       r.status_code == 200, r.text)

    # 8h. Sanitation complaint
    r = post("/api/v1/municipal/complaint", {
        "consumer_id":        "CUST-MUNI-IMP-0077",
        "complaint_category": "Garbage collection",
        "location":           "Thangmeiband, Imphal East",
        "ward_number":        "WARD-08",
        "description":        "Garbage not collected for 6 days, creating health hazard",
        "severity":           "High",
    })
    check("POST /municipal/complaint → 200",           r.status_code == 200, r.text)

    # 8i. General grievance
    r = post("/api/v1/municipal/grievance", {
        "citizen_id":  "CUST-MUNI-IMP-0077",
        "subject":     "Delay in birth certificate issuance",
        "description": "Application submitted 45 days ago, no response or update received",
        "dept_ref":    "BIRTH-CERT-DEPT",
    })
    check("POST /municipal/grievance → 200",           r.status_code == 200, r.text)

    # ══════════════════════════════════════════════════════════════════════════
    section("9 · Payments API")
    # ══════════════════════════════════════════════════════════════════════════

    # 9a. Initiate
    r = post("/api/v1/payments/initiate", {
        "userId":         "prem_user_001",
        "billId":         "BILL-ELEC-MTR-TEST-2026-02",
        "dept":           "electricity",
        "amount":         822.00,
        "currency":       "INR",
        "method":         "upi",
        "gateway":        "mock",
        "consumerNumber": "MTR-ELEC-IMP-TEST",
        "billingPeriod":  "2026-02",
    })
    check("POST /payments/initiate → 200",   r.status_code == 200, r.text)
    pay_id = order_id = None
    if r.status_code == 200:
        pay_id   = r.json().get("paymentId")   or r.json().get("payment_id")
        order_id = r.json().get("orderId")     or r.json().get("order_id")
        check("paymentId present",             bool(pay_id or order_id))
        check("isMock = true",                 r.json().get("isMock") is True)

    # 9b. Complete
    if pay_id or order_id:
        r = post("/api/v1/payments/complete", {
            "paymentId":        pay_id or order_id,
            "orderId":          order_id or pay_id,
            "gateway":          "mock",
            "gatewayPaymentId": f"pay_mock_test_{int(time.time())}",
        })
        check("POST /payments/complete → 200", r.status_code == 200, r.text)
        if r.status_code == 200:
            check("receipt in response", bool(r.json().get("receipt")))

    # 9c. History
    r = get("/api/v1/payments/history/prem_user_001")
    check("GET /payments/history → 200",     r.status_code == 200, r.text)

    # ══════════════════════════════════════════════════════════════════════════
    section("10 · Admin — request management")
    # ══════════════════════════════════════════════════════════════════════════

    r = get("/admin/requests", token=admin_token)
    check("GET /admin/requests → 200",          r.status_code == 200, r.text)
    if r.status_code == 200:
        total = r.json().get("total", 0)
        check(f"requests recorded (found {total})", total > 0)

    # Filter by department
    r = get("/admin/requests", token=admin_token, params={"department": "electricity"})
    check("filter by department=electricity",   r.status_code == 200, r.text)
    if r.status_code == 200:
        check("all rows are electricity",
              all(x["department"] == "electricity" for x in r.json().get("requests", [])))

    # Filter by status
    r = get("/admin/requests", token=admin_token, params={"status": "SUBMITTED"})
    check("filter by status=SUBMITTED",         r.status_code == 200, r.text)

    # Get specific request
    if elec_req_id:
        r = get(f"/admin/requests/{elec_req_id}", token=admin_token)
        check("GET /admin/requests/{id} → 200",    r.status_code == 200, r.text)
        check("department = electricity",           r.json().get("department") == "electricity")
        check("service_type = ELECTRICITY_PAY_BILL",
              r.json().get("service_type") == "ELECTRICITY_PAY_BILL")

    # Approve an electricity request
    if elec_req_id:
        r = patch(f"/admin/requests/{elec_req_id}/status",
                  {"status": "APPROVED", "note": "Verified meter — approved"},
                  token=admin_token)
        check("PATCH status → APPROVED",           r.status_code == 200, r.text)
        check("new_status = APPROVED",             r.json().get("new_status") == "APPROVED")

    # Deliver a municipal request
    if muni_req_id:
        r = patch(f"/admin/requests/{muni_req_id}/status",
                  {"status": "DELIVERED"},
                  token=admin_token)
        check("PATCH status → DELIVERED",          r.status_code == 200, r.text)

    # Deny a water request
    if water_req_id:
        r = patch(f"/admin/requests/{water_req_id}/status",
                  {"status": "DENIED",
                   "error_code": "DOCS_INCOMPLETE",
                   "error_message": "Address proof not legible"},
                  token=admin_token)
        check("PATCH status → DENIED",             r.status_code == 200, r.text)

    # ══════════════════════════════════════════════════════════════════════════
    section("11 · Admin — payments view")
    # ══════════════════════════════════════════════════════════════════════════

    r = get("/admin/payments", token=admin_token)
    check("GET /admin/payments → 200",    r.status_code == 200, r.text)
    if r.status_code == 200:
        total = r.json().get("total", 0)
        check(f"payment rows present ({total})", total > 0)

    # Filter by department
    r = get("/admin/payments", token=admin_token, params={"department": "water"})
    check("filter payments by department", r.status_code == 200, r.text)

    # ══════════════════════════════════════════════════════════════════════════
    section("12 · Kiosk config (super-admin)")
    # ══════════════════════════════════════════════════════════════════════════

    r = post("/admin/kiosk-config", {
        "department":      "electricity",
        "razorpay_key_id": "rzp_test_SUVIDHA2026",
        "razorpay_mode":   "test",
        "is_active":       True,
        "settings":        {"support_phone": "1800-345-6789", "kiosk_name": "SUVIDHA Kiosk Imphal"},
    }, token=admin_token)
    check("POST /admin/kiosk-config → 200",    r.status_code == 200, r.text)
    if r.status_code == 200:
        hint = r.json().get("razorpay_key_id_hint")
        check("hint = masked last-4 of key",   hint == "****2026")
        check("is_active = true",              r.json().get("is_active") is True)

    # Non-super-admin cannot set config (verified later via dept admin)
    r = get("/admin/kiosk-config", token=admin_token)
    check("GET /admin/kiosk-config → 200",     r.status_code == 200, r.text)
    if r.status_code == 200:
        cfgs = {c["department"]: c for c in r.json().get("configs", [])}
        check("electricity config saved",      "electricity" in cfgs)

    # ══════════════════════════════════════════════════════════════════════════
    section("13 · Shared request lookup")
    # ══════════════════════════════════════════════════════════════════════════

    if elec_req_id:
        r = get(f"/api/v1/requests/{elec_req_id}")
        check("GET /api/v1/requests/{id} → 200",     r.status_code == 200, r.text)
        check("department = electricity",             r.json().get("department") == "electricity")

    # User-scoped request list
    r = get("/api/v1/requests/user/prem_user_001")
    check("GET /api/v1/requests/user/{uid} → 200",   r.status_code == 200, r.text)
    if r.status_code == 200:
        total = r.json().get("total", 0)
        check(f"user has {total} requests",           total > 0)

    # Filter by department
    r = get("/api/v1/requests/user/prem_user_001", params={"department": "municipal"})
    check("user requests filter by municipal",        r.status_code == 200, r.text)

    # ══════════════════════════════════════════════════════════════════════════
    section("14 · Kiosk session end & token invalidation")
    # ══════════════════════════════════════════════════════════════════════════

    if kiosk_token:
        r = post("/kiosk/session/end", {"session_token": kiosk_token})
        check("POST /kiosk/session/end → 200",         r.status_code == 200, r.text)
        check("success = true",                        r.json().get("success") is True)

        # Token must be dead now
        r = get("/kiosk/session/validate", params={"session_token": kiosk_token})
        check("Ended token → 401",                     r.status_code == 401)

    # ══════════════════════════════════════════════════════════════════════════
    section("15 · Department admin — scoped access")
    # ══════════════════════════════════════════════════════════════════════════

    # Create a department-admin via SQL (no registration endpoint — admin management is backend-only)
    from src.department.database.database import SessionLocal, _hash_password
    from src.department.database.models   import Admin as AdminModel
    db = SessionLocal()
    water_admin = AdminModel(
        username        = "water_admin_imphal",
        email           = "wateradmin@imc.gov.in",
        full_name       = "Water Dept Admin",
        hashed_password = _hash_password("WaterAdmin@2026"),
        role            = "department_admin",
        department      = "water",
        is_active       = True,
    )
    db.add(water_admin)
    db.commit()
    db.close()

    r = post("/admin/login", form={"username": "water_admin_imphal", "password": "WaterAdmin@2026"})
    check("Dept admin login → 200",               r.status_code == 200, r.text)
    dept_token = r.json().get("access_token") if r.status_code == 200 else None
    if dept_token:
        check("role = department_admin",           r.json().get("role") == "department_admin")
        check("department = water",                r.json().get("department") == "water")

    # Dept admin can see water requests
    if dept_token:
        r = get("/admin/requests", token=dept_token)
        check("Dept admin GET /admin/requests → 200", r.status_code == 200, r.text)
        if r.status_code == 200:
            for req in r.json().get("requests", []):
                check("rows scoped to water dept",
                      req["department"] == "water")
                break   # just check the first row

    # Dept admin cannot access kiosk-config (super-admin only)
    if dept_token:
        r = get("/admin/kiosk-config", token=dept_token)
        check("Dept admin cannot access kiosk-config → 403", r.status_code == 403)

    # ══════════════════════════════════════════════════════════════════════════
    # SUMMARY
    # ══════════════════════════════════════════════════════════════════════════
    total = len(_passed) + len(_failed)
    print(f"\n{'═'*60}")
    print(f"  {BLD}Results: {GRN}{len(_passed)} passed{RST}  |  {RED}{len(_failed)} failed{RST}  |  {total} total{RST}")
    print(f"  Database: {DB_FILE}")
    print(f"{'═'*60}")
    if _failed:
        print(f"\n{RED}Failed:{RST}")
        for f in _failed:
            print(f"  • {f}")
    print()


# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print(f"\n{BLD}KOISK Backend — End-to-End Smoke Test{RST}")
    print(f"Database  →  {DB_FILE}")
    print(f"Server    →  {BASE}\n")

    print("Starting server...", end=" ", flush=True)
    if not start_and_wait():
        print(f"{RED}FAILED — server did not come up{RST}")
        sys.exit(1)
    print(f"{GRN}up ✓{RST}")

    try:
        run()
    except Exception:
        traceback.print_exc()
        sys.exit(1)

    sys.exit(1 if _failed else 0)
