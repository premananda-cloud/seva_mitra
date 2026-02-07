# Gas Utilities Services Framework
## SUVIDHA 2026 - Service Transfer & Core Terms Implementation

---

## 1. Gas Service Namespace
All gas services live under:
```
department.gas
```

Each service:
- Maps to exactly one `ServiceType`
- Defines its own data schema (payload)
- Uses the common `ServiceRequest` lifecycle
- Follows canonical status transitions

---

## 2. Core Gas Utilities Services

### 2.1 GAS_PAY_BILL

**Description**
Payment of outstanding gas dues for a consumer account.

**Initiator / Beneficiary**
```
initiator_id == beneficiary_id (self-service)
```

**Required Data**
```
consumer_number       (string)  - Gas account ID / Service connection number
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
  "receipt_number": "GAS_RECEIPT_20260201_001",
  "consumer_number": "GAS123456789",
  "amount_paid": 2500.00,
  "amount_new_balance": 0.00,
  "billing_period": "2026-01",
  "payment_timestamp": "2026-02-01T10:30:00Z",
  "next_billing_date": "2026-02-28",
  "payment_method_used": "UPI",
  "transaction_id": "UPI_TXN_20260201_001"
}
```

---

### 2.2 GAS_CONNECTION_REQUEST

**Description**
Request for a new domestic or commercial gas supply connection.

**Initiator / Beneficiary**
```
initiator_id == beneficiary_id (individual/household)
initiator_id != beneficiary_id (organization requesting on behalf)
```

**Required Data**
```
applicant_id              (string)  - Aadhar or corporate ID
applicant_name            (string)  - Full name
phone_number              (string)  - Contact phone
email                     (string)  - Email address
address                   (string)  - Premises address
property_pin_code         (string)  - PIN code
connection_type           (enum)    - DOMESTIC, COMMERCIAL, INDUSTRIAL
purpose                   (string)  - Cooking/Domestic, Commercial, Industrial
connection_appliances     (array)   - List of appliances
load_requirement          (string)  - Gas requirement (kg/month estimate)
property_documents_ref    (string)  - Property proof reference
proof_of_identity_ref     (string)  - ID proof reference
proof_of_address_ref      (string)  - Address proof reference
```

**Validation Rules**
- Property must be within service area
- No existing active connection for same property
- Documents must be verified and valid
- Applicant identity must be verified
- Load requirement within sanctioned limits
- No safety hazards reported

**External Interaction**
- Department inspection team (asynchronous, 3-7 days)
- Property verification system
- Safety check system
- Online payment for connection fees

**State Flow**
```
DRAFT → SUBMITTED → ACKNOWLEDGED → PENDING (inspection) 
→ APPROVED → IN_PROGRESS (pipe installation) → DELIVERED
                OR
        → DENIED (with reason)
```

**Terminal Status**
- `DELIVERED` - Connection activated, consumer number issued
- `DENIED` - Request rejected with reason code

**Denial Reason Codes**
- `OUT_OF_SERVICE_AREA` - Property not in service area
- `EXISTING_CONNECTION` - Connection already exists
- `DOCUMENT_INVALID` - Documents rejected
- `APPLICANT_UNVERIFIED` - Identity verification failed
- `SAFETY_HAZARD` - Property safety concerns
- `CAPACITY_LIMIT` - Area capacity exceeded
- `INCOMPLETE_APPLICATION` - Missing documents

**Success Response**
```json
{
  "service_request_id": "uuid",
  "status": "DELIVERED",
  "consumer_number": "GAS987654321",
  "connection_number": "GC_2026_00001",
  "applicant_name": "Priya Sharma",
  "address": "123 Main Street, Apt 4B",
  "connection_type": "DOMESTIC",
  "meter_number": "MTR_GAS_0001",
  "activation_date": "2026-02-15",
  "first_billing_date": "2026-03-01",
  "connection_fee_paid": 1500.00,
  "monthly_rate": "₹50 per kg",
  "customer_care_number": "1800-GAS-HELP",
  "issued_at": "2026-02-01T14:00:00Z"
}
```

---

### 2.3 GAS_METER_CHANGE

**Description**
Replacement, upgrade, or correction of gas meter.

**Initiator / Beneficiary**
```
initiator_id = customer requesting replacement
beneficiary_id = customer receiving replacement
```

**Required Data**
```
consumer_number           (string) - Gas account ID
old_meter_number          (string) - Current meter ID
new_meter_number          (string) - New meter ID
reason_code               (enum)   - DAMAGED, FAULTY, UPGRADE, CORRECTION, EXPIRY
reason_description        (string) - Detailed reason
inspection_report_ref     (string) - Inspection report reference
department_order_ref      (string) - Department authorization
proposed_installation_date (date)  - Requested installation date
```

**Validation Rules**
- Consumer must exist with active account
- Old meter must be currently active
- New meter must be valid and not assigned
- Inspection report must be attached
- Cannot request more than once per year (except expiry/safety)
- Meter not locked due to non-payment

**External Interaction**
- Department inspection team (on-site verification)
- Meter installation team
- Billing system update
- Safety certification

**State Flow**
```
DRAFT → SUBMITTED → ACKNOWLEDGED → PENDING (inspection scheduling)
→ APPROVED (inspection complete) → IN_PROGRESS (installation)
→ DELIVERED (meter active)
```

**Terminal Status**
- `DELIVERED` - Meter replacement completed
- `FAILED` - Technical issue during installation

**Failure Codes**
- `METER_NOT_FOUND` - Meter doesn't exist
- `METER_LOCKED` - Meter locked due to issues
- `INSTALLATION_FAILED` - Technical failure
- `CERTIFICATION_FAILURE` - Safety certification failed
- `SAFETY_HAZARD_DETECTED` - Safety issue found

**Success Response**
```json
{
  "service_request_id": "uuid",
  "status": "DELIVERED",
  "consumer_number": "GAS123456789",
  "old_meter_number": "MTR_GAS_0001",
  "new_meter_number": "MTR_GAS_0002",
  "reason": "DAMAGED",
  "installation_date": "2026-02-10",
  "final_reading_old_meter": 1250,
  "opening_reading_new_meter": 0,
  "meter_condition_certificate": "PASSED_CERTIFICATION",
  "warranty_period": "5 years",
  "safety_inspection": "PASSED",
  "changed_at": "2026-02-10T09:00:00Z"
}
```

---

### 2.4 GAS_SAFETY_INSPECTION

**Description**
Periodic safety inspection of gas installation, pipes, and fittings. Mandatory every 2 years or on-demand.

**Initiator / Beneficiary**
```
initiator_id = customer requesting OR department (automated)
beneficiary_id = customer receiving inspection
```

**Required Data**
```
consumer_number              (string) - Gas account ID
inspection_type              (enum)   - PERIODIC, ON_DEMAND, PRE_ACTIVATION
inspection_requested_date    (date)   - When inspection was requested
preferred_inspection_dates   (array)  - Array of 3 preferred dates/times
reason_for_inspection        (string) - Issues reported or periodic
inspection_urgency           (enum)   - ROUTINE, URGENT, CRITICAL
```

**Validation Rules**
- Consumer account must exist
- Last inspection must be older than 24 months (for periodic)
- No pending disputes on account
- URGENT/CRITICAL processed within 48 hours

**External Interaction**
- Department safety inspection team
- Gas leak detection equipment
- National safety database (for certification)

**State Flow**
```
DRAFT → SUBMITTED → ACKNOWLEDGED → PENDING (scheduling)
→ APPROVED (scheduled) → IN_PROGRESS (inspection)
→ DELIVERED (inspection passed, certificate issued)
OR
→ FAILED (safety issues found)
```

**Terminal Status**
- `DELIVERED` - Inspection passed, certificate valid 24 months
- `FAILED` - Safety issues found, action required
- `DENIED` - Cannot schedule (account issues)

**Inspection Result Codes**
- `SAFE_PASS` - All systems safe, certificate valid 24 months
- `SAFE_WITH_RECOMMENDATIONS` - Safe but minor improvements recommended
- `UNSAFE_REPAIRS_REQUIRED` - Issues found, repairs mandatory
- `UNSAFE_DISCONNECTION_REQUIRED` - Critical hazard, connection suspended

**Success Response**
```json
{
  "service_request_id": "uuid",
  "status": "DELIVERED",
  "consumer_number": "GAS123456789",
  "inspection_number": "GASINSP_2026_00123",
  "inspection_date": "2026-02-10",
  "inspector_name": "Rajesh Kumar",
  "inspector_contact": "+91-9876543210",
  "inspection_findings": "All gas lines, connections, and appliances are safe",
  "safety_certificate_number": "GSC_2026_12345",
  "certificate_valid_until": "2028-02-10",
  "issues_found": [],
  "recommendations": ["Annual appliance maintenance advised"],
  "next_inspection_due": "2028-02-10",
  "inspection_fee_charged": 500.00,
  "status_updates": [
    "Inspection scheduled - 2026-02-05",
    "Inspector arrived - 2026-02-10 10:00",
    "Inspection completed - 2026-02-10 10:45",
    "Certificate issued - 2026-02-10 11:00"
  ]
}
```

---

### 2.5 GAS_EMERGENCY_COMPLAINT

**Description**
Report gas emergency - smell, leak, pressure issues, or safety hazards requiring immediate response.

**Initiator / Beneficiary**
```
initiator_id = reporting consumer or public
beneficiary_id = consumer whose connection affected
```

**Required Data**
```
consumer_number          (string, optional) - If known
location_description     (string) - Location of issue
issue_type               (enum)   - GAS_SMELL, PIPE_LEAK, PRESSURE_DROP, 
                                    NO_GAS_FLOW, HISSING_SOUND, SAFETY_HAZARD
severity_level           (enum)   - LOW, HIGH, CRITICAL
any_people_affected      (boolean)- Anyone in affected area
appliance_affected       (string) - Which appliance/area (if known)
location_coordinates     (object) - GPS {latitude, longitude}
```

**Validation Rules**
- Issue type must be predefined
- CRITICAL processed immediately (SLA: 30 minutes)
- Contact information valid
- Location within service area

**External Interaction**
- Emergency response team (immediate dispatch)
- Fire department coordination (if needed)
- Real-time location tracking
- SMS/WhatsApp alerts

**State Flow**
```
DRAFT → SUBMITTED → ACKNOWLEDGED (immediate)
→ PENDING (team en-route) → IN_PROGRESS (team at location)
→ APPROVED (issue identified) → IN_PROGRESS (emergency action)
→ DELIVERED (issue resolved, safety verified)
OR
→ FAILED (escalated to authorities)
```

**Terminal Status**
- `DELIVERED` - Emergency resolved, system safe
- `IN_PROGRESS` - Active response (max 4 hours)
- `FAILED` - Escalated to authorities

**SLA**
- CRITICAL: Response 15 min, resolution 2 hours
- HIGH: Response 30 min, resolution 4 hours
- LOW: Response 2 hours, resolution 24 hours

**Success Response**
```json
{
  "service_request_id": "uuid",
  "status": "DELIVERED",
  "complaint_number": "GAS_EMERG_2026_00456",
  "issue_type": "GAS_SMELL",
  "severity": "CRITICAL",
  "reported_at": "2026-02-01T08:30:00Z",
  "field_team_assigned": "Team_GAS_Emergency_001",
  "team_leader": "Amit Singh",
  "team_leader_contact": "+91-9987654321",
  "dispatch_time": "2026-02-01T08:35:00Z",
  "team_arrival": "2026-02-01T08:47:00Z",
  "issue_investigation": "Gas leak found in main connection pipe",
  "emergency_action_taken": "Main valve shut off, area cleared",
  "resolution_description": "Leak sealed using repair tape, pressure tested",
  "pressure_test_result": "PASSED",
  "safety_verification": "SAFE_TO_USE",
  "resolved_at": "2026-02-01T10:15:00Z",
  "follow_up_action": "Permanent pipe replacement within 7 days",
  "no_charge_for_emergency_call": true,
  "permanent_repair_scheduled": "2026-02-05"
}
```

---

### 2.6 GAS_METER_READING_SUBMISSION

**Description**
Consumer submits gas meter reading for billing period.

**Initiator / Beneficiary**
```
initiator_id == beneficiary_id (self-service)
```

**Required Data**
```
consumer_number       (string)  - Gas account ID
meter_number          (string)  - Meter being read
billing_period        (string)  - YYYY-MM format
meter_reading         (integer) - Meter dial reading (units)
reading_date          (date)    - Date reading taken
reading_time          (time)    - Time reading taken
photo_ref             (string)  - Photo of meter dial (optional)
```

**Validation Rules**
- Consumer account must be active
- Meter must match consumer's account
- Reading must be >= previous month's reading
- Must be submitted within 5-7 days of period end
- Photo (if provided) must clearly show meter dial
- Reading must not exceed reasonable limits

**External Interaction**
- Billing system (updates reading)
- No other external dependencies

**State Flow**
```
DRAFT → SUBMITTED → ACKNOWLEDGED → APPROVED (validated)
→ IN_PROGRESS (bill calculation) → DELIVERED (bill generated)
OR
→ DENIED (reading invalid)
```

**Terminal Status**
- `DELIVERED` - Reading accepted, bill generated
- `DENIED` - Reading rejected

**Success Response**
```json
{
  "service_request_id": "uuid",
  "status": "DELIVERED",
  "consumer_number": "GAS123456789",
  "meter_number": "MTR_GAS_0001",
  "billing_period": "2026-01",
  "meter_reading_submitted": 1250,
  "previous_reading": 1100,
  "consumption_units": 150,
  "unit_type": "kg",
  "rate_per_unit": "75.00",
  "fixed_charges": 100.00,
  "calculated_bill": "11350.00",
  "bill_number": "GAS_BILL_2026_00001",
  "bill_generated_date": "2026-02-01",
  "due_date": "2026-02-15",
  "message": "Reading accepted. Bill generated successfully."
}
```

---

### 2.7 GAS_COMPLAINT_GRIEVANCE

**Description**
Submit complaint or grievance regarding gas billing, service, or quality issues.

**Initiator / Beneficiary**
```
initiator_id == beneficiary_id (self-service)
```

**Required Data**
```
consumer_number          (string) - Gas account ID (optional)
complaint_category       (enum)   - BILLING_ISSUE, SERVICE_INTERRUPTION,
                                    METER_ISSUE, PRESSURE_ISSUE, QUALITY_ISSUE,
                                    WRONG_CHARGES, DISCONNECTION, OTHER
complaint_subject        (string) - Brief subject line
complaint_description    (text)   - Detailed description
severity_level           (enum)   - LOW, MEDIUM, HIGH, CRITICAL
evidence_refs            (array)  - Photos, documents, bills
preferred_contact        (string) - Phone, Email, WhatsApp, SMS
preferred_language       (enum)   - EN, HI, MR, TA, TE
```

**Validation Rules**
- Complaint description minimum 20 characters
- Category must be predefined
- If consumer_number provided, account must exist
- Recommended to include evidence

**External Interaction**
- Complaint management system (routing, escalation)
- WhatsApp/Email notifications
- Department officer assignment

**State Flow**
```
DRAFT → SUBMITTED → ACKNOWLEDGED (assigned to officer)
→ PENDING (investigation) → APPROVED (resolution plan)
→ IN_PROGRESS (action taken) → DELIVERED (resolved)
OR
→ DENIED (invalid/duplicate)
```

**Terminal Status**
- `DELIVERED` - Complaint resolved
- `DENIED` - Complaint rejected/duplicate

**Success Response**
```json
{
  "service_request_id": "uuid",
  "status": "DELIVERED",
  "complaint_number": "COMP_GAS_2026_00456",
  "consumer_number": "GAS123456789",
  "complaint_category": "BILLING_ISSUE",
  "complaint_subject": "Excessive charges in January bill",
  "registered_at": "2026-02-01T09:00:00Z",
  "assigned_officer": "Priya Sharma",
  "officer_contact": "+91-9123456789",
  "investigation_started": "2026-02-01T10:00:00Z",
  "investigation_findings": "Meter malfunction detected",
  "resolution_action": "Meter reading corrected, refund processed",
  "complaint_resolved_date": "2026-02-05T16:30:00Z",
  "resolution_description": "Billing error corrected, refund issued",
  "refund_amount": 500.00,
  "refund_date": "2026-02-06",
  "resolution_rating_requested": true,
  "reference_documents": ["METER_TEST_REPORT_001", "BILLING_CORRECTION_001"]
}
```

---

## 3. Data Ownership Rules (Gas)

```
Consumer data (name, address, contact)     → Department-owned
Meter data (readings, specifications)       → Department-owned
Billing data (bills, amounts, due dates)    → Department-owned
Payment confirmations                        → System-owned (payment gateway)
Complaints & grievances                     → Department-owned
Safety inspections                          → Department-owned
Emergency reports                           → Department-owned
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

### Gas-Specific Errors
```
METER_NOT_FOUND             - Meter doesn't exist in system
METER_LOCKED                - Meter locked due to issues
SAFETY_HAZARD_DETECTED      - Safety concern found
READING_INVALID             - Meter reading validation failed
INSPECTION_OVERDUE          - Safety inspection overdue
```

---

## 5. Key Design Rules

1. **Gas services NEVER bypass ServiceRequest** - All actions flow through state machine
2. **Safety is paramount** - Emergency responses prioritized, 15-minute SLA for critical
3. **Inspection mandatory** - Every 2 years or before activation
4. **Payment is synchronous, approval is asynchronous** - Payment immediate; connections take days
5. **Audit trail is immutable** - All changes recorded, never deleted
6. **Status visibility enforced** - Different views for different actors

---

## 6. Mapping to Code Structure

```
Gas_Services.py
├── class GasPayBillService
├── class GasConnectionRequestService
├── class GasMeterChangeService
├── class GasSafetyInspectionService
├── class GasEmergencyComplaintService
├── class GasMeterReadingService
├── class GasComplaintService
└── class GasServiceManager

Gas_Database_Schema.sql
├── service_requests (core, shared)
├── service_request_history (audit)
├── gas_consumers (customer data)
├── gas_meters (meter specifications)
├── gas_bills (billing records)
├── gas_emergency_complaints (emergency logs)
├── gas_connections (connection records)
├── gas_safety_inspections (inspection records)
└── gas_service_audit_log (audit trail)

Gas_API_Documentation.md
├── Authentication endpoints
├── Service endpoints (POST, GET, PUT)
├── Status tracking endpoints
└── Error handling & response codes

Gas_KIOSK_API.py
├── class GasKioskAPI
└── HTTP request/response handlers
```

---

## 7. Next Logical Extensions

- SLA tracking per service
- Automated bill generation & overdue notices
- Smart meter integration & real-time readings
- Pressure regulation & supply scheduling
- Gas conservation incentives
- Municipal payment portal integration
- Real-time emergency dispatch tracking
- Citizen feedback & satisfaction surveys
- Escalation workflows for priority handling
- Fire/safety department integration
