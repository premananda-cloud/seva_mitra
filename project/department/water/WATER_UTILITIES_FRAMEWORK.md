# Water Utilities Services Framework
## SUVIDHA 2026 - Service Transfer & Core Terms Implementation

---

## 1. Water Service Namespace
All water services live under:
```
department.water
```

Each service:
- Maps to exactly one `ServiceType`
- Defines its own data schema (payload)
- Uses the common `ServiceRequest` lifecycle
- Follows canonical status transitions

---

## 2. Core Water Utilities Services

### 2.1 WATER_PAY_BILL

**Description**
Payment of outstanding water dues for a consumer account.

**Initiator / Beneficiary**
```
initiator_id == beneficiary_id (self-service)
```

**Required Data**
```
consumer_number       (string)  - Water account ID / Service connection number
billing_period        (string)  - YYYY-MM format
amount                (decimal) - Payment amount in INR
payment_method        (string)  - UPI, NETBANKING, CARD, CASH
payment_reference     (string)  - Unique payment transaction ID
```

**Validation Rules**
- Consumer account must exist and be ACTIVE
- Outstanding bill must exist for given billing_period
- Amount must match or exceed minimum due amount
- Amount must not exceed total outstanding balance

**External Interaction**
- Payment gateway (synchronous, real-time)
- Department billing system (acknowledgement, asynchronous)

**Terminal Status**
- `DELIVERED` - Payment successful, bill marked paid
- `FAILED` - Payment error (gateway timeout, insufficient funds, duplicate)

**Error Codes**
- `CONSUMER_NOT_FOUND` - Account doesn't exist in system
- `ACCOUNT_INACTIVE` - Account suspended/closed/disconnected
- `BILL_NOT_FOUND` - No outstanding bill for given period
- `INSUFFICIENT_AMOUNT` - Payment below minimum due
- `PAYMENT_FAILED` - Payment gateway error
- `INVALID_PAYMENT_METHOD` - Unsupported payment method
- `DUPLICATE_PAYMENT` - Duplicate payment detected

**Success Response**
```json
{
  "service_request_id": "uuid",
  "status": "DELIVERED",
  "receipt_number": "WATER_RECEIPT_20260201_001",
  "consumer_number": "WTR123456789",
  "amount_paid": 1200.00,
  "amount_previous_balance": 1200.00,
  "amount_new_balance": 0.00,
  "billing_period": "2026-01",
  "payment_timestamp": "2026-02-01T10:30:00Z",
  "next_billing_date": "2026-02-28",
  "payment_method_used": "UPI",
  "transaction_id": "UPI_TXN_20260201_001"
}
```

---

### 2.2 WATER_CONNECTION_REQUEST

**Description**
Request for a new domestic, commercial, or industrial water supply connection.

**Initiator / Beneficiary**
```
initiator_id == beneficiary_id (individual/household)
initiator_id != beneficiary_id (organization requesting on behalf)
```

**Required Data**
```
applicant_id              (string)  - Aadhar number or corporate registration ID
applicant_name            (string)  - Full name
phone_number              (string)  - Contact phone (10 digits)
email                     (string)  - Email address
address                   (string)  - Premises address (full)
property_pin_code         (string)  - PIN code
connection_type           (enum)    - DOMESTIC, COMMERCIAL, INDUSTRIAL
purpose                   (string)  - Drinking/Domestic, Commercial, Industrial, etc.
load_requirement          (integer) - Water requirement in liters/day
property_documents_ref    (string)  - Reference to uploaded property proof (deed/lease)
proof_of_identity_ref     (string)  - Reference to ID proof (Aadhar/PAN)
```

**Validation Rules**
- Property address must be within service area
- No existing active connection for same property
- Documents must be verified and valid
- Applicant identity must be verified
- Load requirement must be within sanctioned limits for area

**External Interaction**
- Department inspection team (asynchronous, may take 3-7 days)
- Property verification system (async)
- Online payment for connection fees (sync)

**State Flow**
```
DRAFT → SUBMITTED → ACKNOWLEDGED → PENDING (inspection) 
→ APPROVED → IN_PROGRESS (meter installation) → DELIVERED
                OR
        → DENIED (with reason: documents invalid, area not covered, etc.)
```

**Terminal Status**
- `DELIVERED` - Connection activated, consumer number issued
- `DENIED` - Request rejected with reason code

**Denial Reason Codes**
- `OUT_OF_SERVICE_AREA` - Property not in municipal boundary
- `EXISTING_CONNECTION` - Active connection already exists
- `DOCUMENT_INVALID` - Uploaded documents rejected
- `APPLICANT_UNVERIFIED` - Identity verification failed
- `CAPACITY_LIMIT` - Area water capacity exceeded
- `INCOMPLETE_APPLICATION` - Missing required documents

**Success Response**
```json
{
  "service_request_id": "uuid",
  "status": "DELIVERED",
  "consumer_number": "WTR987654321",
  "connection_number": "WC_2026_00001",
  "applicant_name": "Priya Sharma",
  "address": "123 Main Street, Apt 4B",
  "connection_type": "DOMESTIC",
  "meter_number": "MTR_WTR_0001",
  "activation_date": "2026-02-15",
  "first_billing_date": "2026-03-01",
  "connection_fee_paid": 500.00,
  "monthly_rate": "30 per 1000 liters",
  "customer_care_number": "1800-WATER-01",
  "issued_at": "2026-02-01T14:00:00Z"
}
```

---

### 2.3 WATER_METER_CHANGE

**Description**
Replacement, upgrade, or correction of water meter (installation or serial number change).

**Initiator / Beneficiary**
```
initiator_id = customer requesting replacement
beneficiary_id = customer receiving replacement
```

**Required Data**
```
consumer_number           (string) - Water account ID
old_meter_number          (string) - Current/old meter ID
new_meter_number          (string) - New meter ID
reason_code               (enum)   - DAMAGED, FAULTY, UPGRADE, CORRECTION, REPAIR
reason_description        (string) - Detailed reason
inspection_report_ref     (string) - Reference to inspection report
department_order_ref      (string) - Department authorization reference
proposed_installation_date (date)  - Requested installation date
```

**Validation Rules**
- Consumer must exist and have active account
- Old meter must be currently active for this consumer
- New meter must be valid and not assigned to another consumer
- Department inspection report must be attached
- Consumer cannot request meter change more than once per year (unless repair)

**External Interaction**
- Department inspection team (on-site verification)
- Meter installation team (scheduled installation)
- Billing system update (old readings → new meter baseline)

**State Flow**
```
DRAFT → SUBMITTED → ACKNOWLEDGED → PENDING (inspection scheduling)
→ APPROVED (inspection completed) → IN_PROGRESS (installation)
→ DELIVERED (new meter active, old readings transferred)
```

**Terminal Status**
- `DELIVERED` - Meter replacement completed, new meter reading recorded
- `FAILED` - Technical issue during installation

**Failure Codes**
- `METER_NOT_FOUND` - Meter doesn't exist in system
- `METER_LOCKED` - Meter has pending disputes/non-payment
- `INSTALLATION_FAILED` - Technical failure during change
- `CALIBRATION_FAILURE` - New meter failed calibration

**Success Response**
```json
{
  "service_request_id": "uuid",
  "status": "DELIVERED",
  "consumer_number": "WTR123456789",
  "old_meter_number": "MTR_WTR_0001",
  "new_meter_number": "MTR_WTR_0002",
  "reason": "DAMAGED",
  "installation_date": "2026-02-10",
  "final_reading_old_meter": 45230,
  "opening_reading_new_meter": 00000,
  "meter_condition_certificate": "PASSED_CALIBRATION",
  "warranty_period": "5 years",
  "changed_at": "2026-02-10T09:00:00Z"
}
```

---

### 2.4 WATER_LEAK_COMPLAINT

**Description**
Report a water leak, pipe burst, or pipeline damage issue requiring urgent department action.

**Initiator / Beneficiary**
```
initiator_id = reporting consumer (or public if no account)
beneficiary_id = same as initiator (self-service)
```

**Required Data**
```
consumer_number          (string, optional) - If known/registered consumer
location_description     (string) - Detailed location of leak
landmark_reference       (string) - Nearby landmark for identification
leak_type                (enum)   - MINOR, MAJOR, WATER_MAIN_BURST, PIPE_SEEPAGE
severity_level           (enum)   - LOW, MEDIUM, HIGH, CRITICAL
water_loss_estimate      (string) - Estimated water loss (liters/hour if known)
affected_area_residents  (integer)- Number of people affected
photo_ref_array          (array)  - Array of photo references (max 5 photos)
location_coordinates     (object) - GPS coordinates {latitude, longitude}
```

**Validation Rules**
- Location must be within municipal area
- At least one photo must be provided (unless reported via phone)
- Leak type must be one of predefined options
- Location coordinates must be valid (if provided)
- Severity should match leak type (MAJOR typically CRITICAL)

**External Interaction**
- Field team dispatch (urgent for CRITICAL/HIGH)
- Real-time location tracking
- WhatsApp/SMS status updates to consumer

**State Flow**
```
DRAFT → SUBMITTED → ACKNOWLEDGED (assignment to field team)
→ PENDING (field team en-route) → IN_PROGRESS (team at location, investigation)
→ APPROVED (repair plan identified) → IN_PROGRESS (repair work)
→ DELIVERED (leak fixed, pressure tested, area cleaned)
OR
→ FAILED (unable to repair immediately, needs escalation)
```

**Terminal Status**
- `DELIVERED` - Leak repaired, water pressure normalized
- `IN_PROGRESS` - Active repair work happening (can stay here for 48 hours max)
- `FAILED` - Escalated to engineering team for major work

**SLA**
- CRITICAL: Field team arrival in 2 hours, repair completion in 6 hours
- HIGH: Field team arrival in 4 hours, repair completion in 24 hours
- MEDIUM: Field team arrival in 8 hours, repair completion in 48 hours
- LOW: Field team arrival in 24 hours, repair completion in 5 days

**Success Response**
```json
{
  "service_request_id": "uuid",
  "status": "DELIVERED",
  "complaint_number": "LEAK_2026_00123",
  "location": "Main Street, Near Traffic Signal",
  "leak_type": "MAJOR",
  "severity": "HIGH",
  "reported_at": "2026-02-01T08:30:00Z",
  "field_team_assigned": "Team_Water_001",
  "field_team_arrival": "2026-02-01T10:15:00Z",
  "repair_started": "2026-02-01T10:20:00Z",
  "repair_completed": "2026-02-01T14:45:00Z",
  "repair_description": "Replaced burst main pipe section, 50 meters",
  "water_wasted_estimate": "5000 liters",
  "consumer_credit": "₹250 (compensation for water loss)",
  "status_updates": [
    "Complaint registered - 08:30",
    "Field team dispatched - 09:00",
    "Field team arrived - 10:15",
    "Repair completed - 14:45",
    "Pressure tested and confirmed - 15:00"
  ],
  "field_engineer_name": "Rajesh Kumar",
  "contact_number": "+91-9876543210"
}
```

---

### 2.5 WATER_METER_READING_SUBMISSION

**Description**
Consumer submits water meter reading for billing period (self-reading by customer).

**Initiator / Beneficiary**
```
initiator_id == beneficiary_id (self-service, customer submits own reading)
```

**Required Data**
```
consumer_number       (string)  - Water account ID
meter_number          (string)  - Meter being read
billing_period        (string)  - YYYY-MM (current month)
meter_reading         (integer) - Meter dial reading (digits)
reading_date          (date)    - Date reading taken
reading_time          (time)    - Time reading taken (HH:MM)
photo_ref             (string)  - Photo of meter dial (optional but encouraged)
```

**Validation Rules**
- Consumer account must be active
- Meter must match consumer's account
- Reading must be greater than previous month's reading (or equal if no usage)
- Reading must be submitted within 3-5 days of billing period end
- Photo (if provided) must clearly show meter dial

**External Interaction**
- Billing system (updates meter reading)
- No external dependencies (synchronous validation only)

**State Flow**
```
DRAFT → SUBMITTED → ACKNOWLEDGED → APPROVED (meter reading validated)
→ IN_PROGRESS (bill calculation) → DELIVERED (bill generated)
OR
→ DENIED (reading invalid - less than previous, photo unclear, etc.)
```

**Terminal Status**
- `DELIVERED` - Reading accepted, bill generated with this reading
- `DENIED` - Reading rejected (below previous month, illegible, etc.)

**Success Response**
```json
{
  "service_request_id": "uuid",
  "status": "DELIVERED",
  "consumer_number": "WTR123456789",
  "meter_number": "MTR_WTR_0001",
  "billing_period": "2026-01",
  "meter_reading_submitted": 45230,
  "previous_reading": 45100,
  "consumption_units": 130,
  "rate_per_unit": "12.00",
  "fixed_charges": 50.00,
  "calculated_bill": "1810.00",
  "bill_number": "WATER_BILL_2026_00001",
  "bill_generated_date": "2026-02-01",
  "due_date": "2026-02-15",
  "message": "Reading accepted. Bill generated successfully."
}
```

---

### 2.6 WATER_COMPLAINT_GRIEVANCE

**Description**
Submit complaint or grievance regarding water quality, billing issues, service interruptions, or other issues.

**Initiator / Beneficiary**
```
initiator_id == beneficiary_id (self-service)
```

**Required Data**
```
consumer_number          (string) - Water account ID (optional if general complaint)
complaint_category       (enum)   - WATER_QUALITY, BILLING_ISSUE, SERVICE_INTERRUPTION,
                                    METER_ISSUE, PRESSURE_LOW, DISCONNECTION, OTHER
complaint_subject        (string) - Brief subject line
complaint_description    (text)   - Detailed description of issue
severity_level           (enum)   - LOW, MEDIUM, HIGH, CRITICAL
evidence_refs            (array)  - Photos, documents, bills, etc.
preferred_contact        (string) - Phone, Email, WhatsApp, SMS
preferred_language       (enum)   - EN, HI, MR, TA, TE, etc.
```

**Validation Rules**
- Complaint must have meaningful description (min 20 characters)
- Category must be from predefined list
- If consumer_number provided, account must exist
- At least one evidence reference recommended for non-service issues

**External Interaction**
- Complaint management system (routing, escalation)
- WhatsApp/Email notifications
- Department officer assignment

**State Flow**
```
DRAFT → SUBMITTED → ACKNOWLEDGED (assigned to officer)
→ PENDING (investigation) → APPROVED (resolution plan made)
→ IN_PROGRESS (resolution action taken)
→ DELIVERED (resolved, feedback requested)
OR
→ DENIED (complaint invalid/duplicate)
```

**Terminal Status**
- `DELIVERED` - Complaint resolved
- `DENIED` - Complaint rejected/duplicate/invalid

**Success Response**
```json
{
  "service_request_id": "uuid",
  "status": "DELIVERED",
  "complaint_number": "COMP_2026_00456",
  "consumer_number": "WTR123456789",
  "complaint_category": "WATER_QUALITY",
  "complaint_subject": "Brown/dirty water from tap",
  "registered_at": "2026-02-01T09:00:00Z",
  "assigned_officer": "Priya Sharma",
  "officer_contact": "+91-9123456789",
  "investigation_started": "2026-02-01T10:00:00Z",
  "investigation_findings": "Main pipeline cleaning required in sector 5",
  "resolution_action": "Pipeline flushing scheduled for 2026-02-05",
  "expected_resolution_date": "2026-02-05",
  "complaint_resolved_date": "2026-02-05T16:30:00Z",
  "resolution_description": "Pipeline cleaned, water quality tested - PASSED",
  "resolution_rating_requested": true,
  "reference_documents": ["PIPELINE_TEST_REPORT_001", "PHOTO_EVIDENCE_001"]
}
```

---

## 3. Data Ownership Rules (Water)

```
Consumer data (name, address, contact)     → Department-owned
Meter data (readings, specifications)       → Department-owned
Billing data (bills, amounts, due dates)    → Department-owned
Payment confirmations                        → System-owned (payment gateway)
Complaints & grievances                     → Department-owned
Leak reports & repairs                      → Department-owned
Service request history                     → System-owned
```

---

## 4. Error Codes & Exceptions

### User-Level Errors
```
INVALID_DATA                 - Request data validation failed
UNAUTHORIZED                 - User not authenticated
ACCOUNT_NOT_FOUND           - Consumer account doesn't exist
ACCOUNT_INACTIVE            - Account suspended/closed
INSUFFICIENT_AMOUNT         - Payment below minimum
DUPLICATE_REQUEST           - Duplicate service request
OUT_OF_SERVICE_AREA         - Location not in service area
```

### System-Level Errors
```
DEPARTMENT_TIMEOUT          - Department system not responding
INTEGRATION_FAILURE         - External system error
PAYMENT_GATEWAY_ERROR       - Payment processing failure
DATABASE_ERROR              - Internal database issue
AUTHENTICATION_FAILED       - OTP/token validation failed
```

---

## 5. Key Design Rules

1. **Water services NEVER bypass ServiceRequest** - All actions flow through state machine
2. **Payment is synchronous, approval is asynchronous** - Bill payment resolves immediately; new connection takes days
3. **Audit trail is immutable** - All status changes recorded, never deleted
4. **Status visibility enforced** - Users see subset of statuses; department sees all

---

## 6. Mapping to Code Structure

Recommended Python layout:
```
Water_Services.py
├── class WaterPayBillService
├── class WaterConnectionRequestService
├── class WaterMeterChangeService
├── class WaterLeakComplaintService
├── class WaterMeterReadingService
├── class WaterComplaintService
└── class WaterServiceManager

Water_Database_Schema.sql
├── service_requests (core, shared)
├── service_request_history (audit)
├── water_consumers (customer data)
├── water_meters (meter specifications)
├── water_bills (billing records)
├── water_leak_complaints (complaints)
└── water_connections (connection records)

Water_API_Documentation.md
├── Authentication endpoints
├── Service endpoints (POST, GET, PUT)
├── Status tracking endpoints
└── Error handling & response codes

Water_KIOSK_API.py
├── class WaterKioskAPI
└── HTTP request/response handlers
```

---

## 7. Next Logical Extensions

- SLA tracking per service (response time, resolution time)
- Automated bill generation & overdue notices
- Pressure management & supply scheduling
- Water conservation incentives
- Integration with municipal payment portals
- Real-time meter data streaming (smart meters)
- Citizen feedback & satisfaction surveys
- Escalation workflows for priority handling
