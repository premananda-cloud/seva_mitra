# KOISK API & Services Guide
> Derived directly from `Electricity_Services.py`, `Water_Services_Complete.py`, and `koisk_api.py`
> Base URL: `http://localhost:8000`  |  Docs: `/docs`

---

## Shared Concepts

### Service Request State Machine
Every request across all departments goes through the same lifecycle:

```
DRAFT → SUBMITTED → ACKNOWLEDGED → PENDING → APPROVED → IN_PROGRESS → DELIVERED
                  ↘ DENIED (terminal)                 ↘ FAILED → IN_PROGRESS (retry)
                  ↘ CANCELLED (terminal)
```

| State | Who owns it | Meaning |
|---|---|---|
| `DRAFT` | USER | Created but not yet submitted |
| `SUBMITTED` | SYSTEM | Sent for processing |
| `ACKNOWLEDGED` | DEPARTMENT | Received and assigned |
| `PENDING` | DEPARTMENT | Waiting on inspection / approval |
| `APPROVED` | DEPARTMENT | Green-lit, execution beginning |
| `IN_PROGRESS` | SYSTEM | Actively being executed |
| `DELIVERED` | SYSTEM | Terminal — success |
| `DENIED` | DEPARTMENT | Terminal — rejected |
| `FAILED` | SYSTEM | Error — may be retried |
| `CANCELLED` | USER/DEPT | Terminal — withdrawn |

### Common Response Shape
All endpoints return either `SuccessResponse` or `ErrorResponse`:

```json
// Success
{
  "success": true,
  "service_request_id": "uuid-...",
  "status": "SUBMITTED",
  "message": "...",
  "data": {}
}

// Error
{
  "success": false,
  "error_code": "METER_NOT_FOUND",
  "error_message": "...",
  "timestamp": "2026-01-10T10:30:00"
}
```

### Status Lookup (works for all departments)
```
GET /api/v1/{dept}/requests/{request_id}
GET /api/v1/{dept}/user/{user_id}/requests
```

---

## ⚡ Electricity Department

### Services

| Service type key | Class | What it does |
|---|---|---|
| `ELECTRICITY_PAY_BILL` | `ElectricityPayBillService` | Pay outstanding dues for a meter |
| `ELECTRICITY_SERVICE_TRANSFER` | `ElectricityServiceTransferService` | Transfer connection ownership to a new customer |
| `ELECTRICITY_METER_CHANGE` | `ElectricityMeterChangeService` | Replace or correct a meter (department-initiated) |
| `ELECTRICITY_CONNECTION_REQUEST` | `ElectricityConnectionRequestService` | Apply for a brand new connection |
| `ELECTRICITY_COMPLAINT` | *(defined in enum, endpoint TBD)* | File a complaint |
| `ELECTRICITY_METER_READING_SUBMISSION` | *(defined in enum, endpoint TBD)* | Submit a meter reading |

> **Note:** `ELECTRICITY_COMPLAINT` and `ELECTRICITY_METER_READING_SUBMISSION` exist in the `ServiceType` enum but do not yet have service classes or API endpoints implemented. They are placeholders for future work.

---

### Electricity Endpoints

#### `POST /api/v1/electricity/pay-bill`
Pay an outstanding electricity bill.

**Request body:**
```json
{
  "user_id": "CUST123456",
  "meter_number": "ELEC123456",
  "billing_period": "2026-01",
  "amount": "1500.00",
  "payment_method": "UPI"
}
```

**Flow inside the service:**
1. Validates meter number format (alphanumeric, min 8 chars) and amount > 0
2. Creates request in `DRAFT`
3. Submits → `SUBMITTED`
4. Calls payment gateway → transitions through `ACKNOWLEDGED → IN_PROGRESS → DELIVERED` (or `FAILED`)
5. Returns receipt on success

**Receipt shape (on DELIVERED):**
```json
{
  "receipt_id": "REC_abc12345",
  "meter_number": "ELEC123456",
  "amount_paid": "1500.00",
  "payment_date": "2026-01-10T10:30:00",
  "payment_reference": "UPI",
  "service_request_id": "uuid-...",
  "status": "COMPLETED"
}
```

**Error codes:** `INVALID_DATA`, `PAYMENT_FAILED`, `INTEGRATION_FAILURE`

---

#### `POST /api/v1/electricity/transfer-service`
Transfer electricity service from one customer to another.

**Request body:**
```json
{
  "old_customer_id": "123456789012",
  "new_customer_id": "987654321098",
  "meter_number": "ELEC123456",
  "identity_proof": "ID_REF_001",
  "ownership_proof": "OWN_REF_001",
  "consent_doc": "CONS_REF_001",
  "effective_date": "2026-03-01"
}
```

**Important validations:**
- Both `old_customer_id` and `new_customer_id` must be 12-digit Aadhaar numbers
- `effective_date` must be in the future

**Flow:** `DRAFT → SUBMITTED` (manual department steps: ACKNOWLEDGED → APPROVED → DELIVERED happen offline)

**Admin steps required** (done via admin API, not triggered automatically):
- Department officer calls acknowledge → approve → complete_transfer

**Error codes:** `INVALID_DATA`, `PENDING_TRANSFER_EXISTS`, `TRANSFER_AUTHORIZATION_FAILED`

---

#### `POST /api/v1/electricity/meter-change`
Request a meter replacement or correction.

**Request body:**
```json
{
  "user_id": "CUST123456",
  "meter_number": "ELEC123456",
  "reason": "Meter malfunction",
  "new_meter_number": null
}
```

**Flow:** Initiated as `DRAFT`, then `SUBMITTED → IN_PROGRESS → DELIVERED` after physical inspection. This is primarily department-initiated — the service class sets `initiator_id = "DEPARTMENT"`.

---

#### `POST /api/v1/electricity/new-connection`
Apply for a new electricity connection at a property.

**Request body:**
```json
{
  "customer_name": "John Doe",
  "customer_id": "CUST123456",
  "address": "123 Main Street, City",
  "load_requirement": "5",
  "identity_proof": "AADHAR_12345",
  "address_proof": "RENT_AGREEMENT_001"
}
```

**Flow:** `SUBMITTED → ACKNOWLEDGED → (inspection) → APPROVED → IN_PROGRESS → DELIVERED`  
On delivery, a `meter_number` and `activation_date` are returned in the response metadata.

---

#### `GET /api/v1/electricity/requests/{request_id}`
Get current status of any electricity service request.

**Response:**
```json
{
  "service_request_id": "uuid-...",
  "status": "PENDING",
  "created_at": "2026-01-10T10:00:00",
  "updated_at": "2026-01-10T10:05:00",
  "error_code": null,
  "error_message": null
}
```

---

#### `GET /api/v1/electricity/user/{user_id}/requests`
List all electricity requests filed by a user.

```json
{
  "user_id": "CUST123456",
  "request_count": 3,
  "requests": [...]
}
```

---

## 💧 Water Department

### Services

| Service type key | Class | What it does |
|---|---|---|
| `WATER_PAY_BILL` | `WaterPayBillService` | Pay outstanding water dues |
| `WATER_CONNECTION_REQUEST` | `WaterConnectionRequestService` | Apply for a new water connection |
| `WATER_METER_CHANGE` | `WaterMeterChangeService` | Replace or upgrade a water meter |
| `WATER_LEAK_COMPLAINT` | `WaterLeakComplaintService` | Report a leak — triggers field dispatch |
| `WATER_METER_READING_SUBMISSION` | `WaterMeterReadingService` | Submit a self-read meter reading |
| `WATER_COMPLAINT_GRIEVANCE` | `WaterComplaintService` | Billing disputes, quality issues, service complaints |

> Water has **6 fully implemented service classes** — more complete than Electricity which has 4.

---

### Water Endpoints

#### `POST /api/v1/water/pay-bill`
Pay an outstanding water bill.

**Request body:**
```json
{
  "user_id": "CONS123456",
  "consumer_number": "WATER123456",
  "billing_period": "2026-01",
  "amount": "800.00",
  "payment_method": "UPI"
}
```

**Validations before submission:**
- Consumer account must exist → error: `CONSUMER_NOT_FOUND`
- Account must be active → error: `ACCOUNT_INACTIVE`
- Bill must exist for that period → error: `BILL_NOT_FOUND`

**Flow:** `DRAFT → SUBMITTED → ACKNOWLEDGED → DELIVERED` (or `FAILED`)

On success, `payment_reference` and `payment_timestamp` are stored in the request payload.

**Receipt shape:**
```json
{
  "receipt_number": "WATER_RECEIPT_20260110_103000",
  "consumer_number": "WATER123456",
  "amount_paid": "800.00",
  "billing_period": "2026-01",
  "payment_method": "UPI",
  "transaction_id": "TXN_ABC123DEF456",
  "timestamp": "2026-01-10T10:30:00",
  "status": "PAID"
}
```

**Error codes:** `CONSUMER_NOT_FOUND`, `ACCOUNT_INACTIVE`, `BILL_NOT_FOUND`, `PAYMENT_FAILED`, `DUPLICATE_PAYMENT`, `INTEGRATION_FAILURE`

---

#### `POST /api/v1/water/new-connection`
Request a new water connection.

**Request body:**
```json
{
  "applicant_name": "Jane Smith",
  "applicant_id": "APPL123456",
  "address": "456 Oak Avenue, City",
  "property_type": "Residential",
  "identity_proof": "AADHAR_67890",
  "address_proof": "OWNERSHIP_PROOF_002"
}
```

**Full connection type options (from enum):** `DOMESTIC`, `COMMERCIAL`, `INDUSTRIAL`

**Validations before submission:**
- Address must be within service area → error: `OUT_OF_SERVICE_AREA`
- No existing active connection at the property → error: `EXISTING_CONNECTION`

**Full flow:**
```
SUBMITTED → ACKNOWLEDGED → PENDING (inspection scheduled, +3 days) → APPROVED → IN_PROGRESS → DELIVERED
```

On delivery, these are generated and returned:
```json
{
  "consumer_number": "WTRxxxxxxxxxxxx",
  "connection_number": "WC_2026_xxxxx",
  "meter_number": "MTR_WTR_xxxxxx",
  "activation_date": "...",
  "first_billing_date": "... (+30 days)"
}
```

**Error codes:** `OUT_OF_SERVICE_AREA`, `EXISTING_CONNECTION`, `DOCUMENT_INVALID`, `APPLICANT_UNVERIFIED`, `CAPACITY_LIMIT`

---

#### `POST /api/v1/water/leak-complaint`
Report a water leak or pipe break.

**Request body:**
```json
{
  "consumer_id": "CONS123456",
  "consumer_number": "WATER123456",
  "complaint_type": "MAJOR",
  "location": "Main Street, Near Traffic Signal",
  "severity": "HIGH",
  "description": "Water leaking from main pipeline"
}
```

**Severity options (from `LeakSeverity` enum):** `LOW`, `MEDIUM`, `HIGH`, `CRITICAL`

**Leak type options (from `LeakType` enum):** `MINOR`, `MAJOR`, `WATER_MAIN_BURST`, `PIPE_SEEPAGE`

**SLA response times by severity:**
| Severity | Field team ETA |
|---|---|
| CRITICAL | 2 hours |
| HIGH | 4 hours |
| MEDIUM | 8 hours |
| LOW | 24 hours |

**Flow:** `SUBMITTED → ACKNOWLEDGED` (auto, immediate) `→ PENDING` (field team dispatched)

**Response includes:**
```json
{
  "complaint_number": "LEAK_ABCD1234",
  "estimated_arrival": "2026-01-10T14:30:00",
  "message": "Leak complaint registered. Field team dispatched."
}
```

---

#### `GET /api/v1/water/requests/{request_id}`
Get status of any water service request. Same shape as electricity version.

---

### Water-only services (classes exist, API endpoints not yet wired up)

These two service classes are fully implemented in `Water_Services_Complete.py` but have no `@app.post` route in `koisk_api.py` yet. They need to be added.

#### `WaterMeterReadingService` → needs `POST /api/v1/water/submit-reading`

**What it does:** Citizen submits their own meter reading. The service validates it isn't below the previous reading, calculates consumption, generates a bill automatically.

**Expected request:**
```json
{
  "consumer_number": "WATER123456",
  "meter_number": "MTR_WTR_000001",
  "billing_period": "2026-01",
  "meter_reading": 45230
}
```

**Validation:** Reading must be ≥ previous reading → error: `READING_BELOW_PREVIOUS`

**On approval, auto-calculates:**
- `consumption_units = current_reading - previous_reading`
- `bill_amount = (consumption × ₹12.00) + ₹50.00 fixed charge`
- Generates `bill_number` with due date (+15 days)

---

#### `WaterComplaintService` → needs `POST /api/v1/water/complaint`

**What it does:** General complaint or grievance — quality, billing dispute, pressure issues, disconnection, meter fault.

**Complaint categories (from `ComplaintCategory` enum):**
`WATER_QUALITY`, `BILLING_ISSUE`, `SERVICE_INTERRUPTION`, `METER_ISSUE`, `PRESSURE_LOW`, `DISCONNECTION`, `OTHER`

**Expected request:**
```json
{
  "consumer_number": "WATER123456",
  "complaint_category": "BILLING_ISSUE",
  "subject": "Wrong billing amount for January",
  "description": "Bill shows 450 units but actual reading was 180 units",
  "severity": "MEDIUM"
}
```

**Flow:** `SUBMITTED → ACKNOWLEDGED` (officer assigned) `→ PENDING` (investigation) `→ DELIVERED` (resolved)

---

## 🏛️ Municipal Department

Municipal is a **new department** — no existing service file. Services defined based on the structure established by Electricity and Water.

### Planned Services

| Service type key | Category | Notes |
|---|---|---|
| `MUNICIPAL_PROPERTY_TAX_PAYMENT` | Payment | Annual tax — uses `billing_period` as tax year e.g. `"2025-2026"` |
| `MUNICIPAL_TRADE_LICENSE_NEW` | Application | New business license |
| `MUNICIPAL_TRADE_LICENSE_RENEWAL` | Application | Annual renewal |
| `MUNICIPAL_BIRTH_CERTIFICATE` | Certificate | Requires hospital/medical proof |
| `MUNICIPAL_DEATH_CERTIFICATE` | Certificate | Requires medical certificate |
| `MUNICIPAL_BUILDING_PLAN_APPROVAL` | Approval | Needs site inspection step |
| `MUNICIPAL_SANITATION_COMPLAINT` | Complaint | Garbage, drains, street lights, roads |
| `MUNICIPAL_GENERAL_GRIEVANCE` | Grievance | Catch-all for citizen complaints |
| `MUNICIPAL_NEW_CONNECTION_REQUEST` | Application | Property registration / new service area connection |

### Municipal Endpoints (to be built)

```
POST /api/v1/municipal/property-tax
POST /api/v1/municipal/trade-license
POST /api/v1/municipal/birth-certificate
POST /api/v1/municipal/death-certificate
POST /api/v1/municipal/building-plan
POST /api/v1/municipal/complaint
POST /api/v1/municipal/grievance
GET  /api/v1/municipal/bills/{user_id}
GET  /api/v1/municipal/requests/{request_id}
```

### Municipal consumer number format
Following the pattern from Electricity (`ELEC-MH-XXXXX`) and Water (`WAT-MH-XXXXX`):
`MUNI-MH-XXXXX` — includes `ward_number` and `zone` as extra fields not present in other departments.

---

## Admin / Department Officer API

### Auth
```
POST /admin/login   →  JWT token (scoped to role + department)
```

Token roles:
- `super_admin` — sees all departments
- `department_admin` — scoped to one department
- `merchant` — department_admin who has completed payment setup

### Request Management
```
GET   /admin/requests                        — list all (auto-scoped by dept)
GET   /admin/requests/{request_id}           — single request
PATCH /admin/requests/{request_id}/status    — approve / deny / deliver
GET   /admin/payments                        — all payments (auto-scoped)
```

### Merchant Payment Setup
```
POST /admin/merchant/setup   — store gateway config (PortOne / Razorpay)
GET  /admin/merchant/config  — view stored config (keys obfuscated)
```

**Setup body:**
```json
{
  "gateway": "portone",
  "merchant_id": "store_xxx",
  "channel_key": "channel_key_xxx",
  "api_key": "sk_live_xxx"
}
```

---

## Error Code Reference

### Shared across all departments
| Code | Meaning |
|---|---|
| `INVALID_DATA` | Validation failed on input fields |
| `UNAUTHORIZED` | Not permitted to perform this action |
| `CONFLICT` | Duplicate or conflicting request exists |
| `DEPARTMENT_TIMEOUT` | Department system did not respond |
| `INTEGRATION_FAILURE` | Payment gateway or external system error |
| `INTERNAL_ERROR` | Unhandled server-side error |

### Electricity-specific
| Code | Meaning |
|---|---|
| `METER_NOT_FOUND` | No meter matching that number |
| `METER_INACTIVE` | Meter is suspended or deactivated |
| `METER_NOT_OWNED_BY_USER` | Meter belongs to a different customer |
| `BILL_NOT_FOUND` | No bill for that meter + period |
| `INSUFFICIENT_AMOUNT` | Amount is below minimum due |
| `PAYMENT_FAILED` | Gateway declined payment |
| `PENDING_TRANSFER_EXISTS` | Another transfer is already in progress |
| `TRANSFER_AUTHORIZATION_FAILED` | Transfer was denied by department |

### Water-specific
| Code | Meaning |
|---|---|
| `CONSUMER_NOT_FOUND` | No consumer account with that number |
| `ACCOUNT_INACTIVE` | Account is suspended |
| `BILL_NOT_FOUND` | No bill for that consumer + period |
| `DUPLICATE_PAYMENT` | Bill for that period already paid |
| `OUT_OF_SERVICE_AREA` | Property address not in service zone |
| `EXISTING_CONNECTION` | Active connection already exists at address |
| `DOCUMENT_INVALID` | Submitted proof document failed verification |
| `APPLICANT_UNVERIFIED` | Identity could not be confirmed |
| `CAPACITY_LIMIT` | No capacity to add new connection in that area |
| `METER_NOT_FOUND` | Meter number not in system |
| `METER_LOCKED` | Meter has pending disputes or unpaid dues |
| `METER_MISMATCH` | Meter number does not match consumer record |
| `INSTALLATION_FAILED` | Physical installation could not be completed |
| `CALIBRATION_FAILURE` | New meter failed calibration |
| `READING_INVALID` | Reading value is not a valid number |
| `READING_BELOW_PREVIOUS` | Reading is less than last recorded reading |
| `PHOTO_UNCLEAR` | Meter photo submitted was unreadable |

---

## Payment Methods
Accepted value strings for `payment_method` across all departments:

| Value | Description |
|---|---|
| `UPI` | UPI (Google Pay, PhonePe, Paytm, etc.) |
| `CARD` | Debit or credit card |
| `NET_BANKING` | Internet banking |

Gateway used is determined server-side based on `MOCK_PAYMENT` env var. With `MOCK_PAYMENT=true` (default), all payments auto-complete with a simulated reference number — no real keys needed.

---

## What's Missing / Gaps to Fill

| Item | Department | Priority |
|---|---|---|
| `ELECTRICITY_COMPLAINT` endpoint | Electricity | Medium |
| `ELECTRICITY_METER_READING_SUBMISSION` endpoint | Electricity | Medium |
| `POST /api/v1/water/submit-reading` | Water | High — class fully built |
| `POST /api/v1/water/complaint` | Water | High — class fully built |
| All Municipal endpoints | Municipal | High — new department |
| Bills list endpoint per department | All | High — frontend depends on it |
| Meter reading submission photo upload | Water | Low |
