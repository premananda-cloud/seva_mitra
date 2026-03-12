
---

# 📁 **File 2: `WATER_SERVICES_README.md`**

```markdown
# 💧 SUVIDHA Water Services Module

**Version:** 1.0.0  
**Department:** Water  
**Pattern:** ServiceRequest State Machine  
**Status:** ✅ Complete (All Services + Manager + API)

---

## 📋 Table of Contents
1. [Overview](#overview)
2. [Services Summary](#services-summary)
3. [State Machine](#state-machine)
4. [Service Details](#service-details)
5. [Error Codes](#error-codes)
6. [API Reference](#api-reference)
7. [Usage Examples](#usage-examples)
8. [Integration Guide](#integration-guide)
9. [Database Schema](#database-schema)

---

## 1. Overview

The Water Services module provides a complete framework for water utility operations. It follows the canonical SUVIDHA state machine pattern and includes fully implemented service classes, manager, and KIOSK API.

### Key Features
- 💰 **Bill Payment** - Pay water bills with multiple payment methods
- 🚰 **New Connections** - Apply for new water connections
- 🔧 **Meter Changes** - Request meter replacement/upgrades
- 💦 **Leak Reports** - Report water leaks with SLA-based response
- 📊 **Self-Reading** - Submit meter readings and get auto-bills
- 📢 **Complaints** - File complaints about quality, billing, etc.

### Architecture Completeness: ✅ 100%

| Component | Status |
|-----------|--------|
| Service Classes | ✅ Complete |
| Service Manager | ✅ Complete |
| KIOSK API | ✅ Complete |
| Enums/Constants | ✅ Complete |
| Error Codes | ✅ Complete |
| Validation | ✅ Complete |
| Example Usage | ✅ Complete |

---

## 2. Services Summary

| # | Service Type | Class | Description |
|---|--------------|-------|-------------|
| 1 | `WATER_PAY_BILL` | `WaterPayBillService` | Pay water bills |
| 2 | `WATER_CONNECTION_REQUEST` | `WaterConnectionRequestService` | Apply for new water connection |
| 3 | `WATER_METER_CHANGE` | `WaterMeterChangeService` | Replace/upgrade water meter |
| 4 | `WATER_LEAK_COMPLAINT` | `WaterLeakComplaintService` | Report water leaks |
| 5 | `WATER_METER_READING_SUBMISSION` | `WaterMeterReadingService` | Submit self-readings |
| 6 | `WATER_COMPLAINT_GRIEVANCE` | `WaterComplaintService` | General complaints |

---

## 3. State Machine

All requests follow the canonical SUVIDHA state machine:
DRAFT → SUBMITTED → ACKNOWLEDGED → PENDING → APPROVED → IN_PROGRESS → DELIVERED
↓ ↓ ↓ ↓ ↓
DENIED DENIED DENIED CANCELLED FAILED (can retry)

text

### Status Ownership

| Status | Owner | Description |
|--------|-------|-------------|
| `DRAFT` | User | Being prepared |
| `SUBMITTED` | System | Sent for processing |
| `ACKNOWLEDGED` | Department | Received and assigned |
| `PENDING` | Department | Awaiting action |
| `APPROVED` | Department | Approved |
| `IN_PROGRESS` | System | Being executed |
| `DELIVERED` | System | Completed |
| `DENIED` | Department | Rejected |
| `FAILED` | System | Error occurred |
| `CANCELLED` | User/Dept | Withdrawn |

---

## 4. Service Details

### 4.1 WaterPayBillService

**Purpose:** Handle water bill payments with validation and receipt generation.

**Class:**
```python
class WaterPayBillService:
    def __init__(self, db_service=None, payment_gateway=None):
        self.db_service = db_service
        self.payment_gateway = payment_gateway
    
    def create_pay_bill_request(
        self,
        consumer_number: str,
        customer_id: str,
        billing_period: str,      # YYYY-MM
        amount: Decimal,
        payment_method: str        # UPI, CARD, NET_BANKING
    ) -> ServiceRequest
    
    def submit_payment(self, request: ServiceRequest) -> ServiceRequest
    
    def process_payment(self, request: ServiceRequest) -> ServiceRequest
    
    def generate_receipt(self, request: ServiceRequest) -> Dict[str, Any]
Validations:

Consumer account exists (CONSUMER_NOT_FOUND)

Account is active (ACCOUNT_INACTIVE)

Bill exists for period (BILL_NOT_FOUND)

Flow:

text
DRAFT → SUBMITTED → ACKNOWLEDGED → DELIVERED
              ↓                    ↑
           FAILED (retry) ─────────┘
Receipt Output:

json
{
  "receipt_number": "WATER_RECEIPT_20260115_103000",
  "consumer_number": "WTR123456",
  "amount_paid": "1200.00",
  "billing_period": "2026-01",
  "payment_method": "UPI",
  "transaction_id": "TXN_ABC123",
  "timestamp": "2026-01-15T10:30:00",
  "status": "PAID"
}
4.2 WaterConnectionRequestService
Purpose: Handle new water connection applications with inspection workflow.

Class:

python
class WaterConnectionRequestService:
    def __init__(self, db_service=None):
        self.db_service = db_service
    
    def create_connection_request(
        self,
        applicant_id: str,
        applicant_name: str,
        phone_number: str,
        email: str,
        address: str,
        connection_type: ConnectionType,  # DOMESTIC, COMMERCIAL, INDUSTRIAL
        load_requirement: int              # liters/day
    ) -> ServiceRequest
    
    def submit_connection_request(self, request: ServiceRequest) -> ServiceRequest
    
    def acknowledge_request(self, request: ServiceRequest) -> ServiceRequest
    
    def schedule_inspection(self, request: ServiceRequest) -> ServiceRequest
    
    def approve_connection(self, request: ServiceRequest, officer_id: str) -> ServiceRequest
    
    def activate_connection(self, request: ServiceRequest) -> ServiceRequest
Validations:

Address in service area (OUT_OF_SERVICE_AREA)

No existing connection (EXISTING_CONNECTION)

Flow:

text
DRAFT → SUBMITTED → ACKNOWLEDGED → PENDING → APPROVED → IN_PROGRESS → DELIVERED
                          (inspection)    (approved)   (activation)  (complete)
On Delivery, Generated:

consumer_number: "WTR9A2B1C4D"

connection_number: "WC_2026_5F3A2"

meter_number: "MTR_WTR_ABC123"

activation_date: Current timestamp

first_billing_date: 30 days later

4.3 WaterMeterChangeService
Purpose: Handle meter replacement requests for damaged or faulty meters.

Class:

python
class WaterMeterChangeService:
    def __init__(self, db_service=None):
        self.db_service = db_service
    
    def create_meter_change_request(
        self,
        consumer_number: str,
        old_meter_number: str,
        reason_code: str,           # DAMAGED, FAULTY, UPGRADE
        reason_description: str
    ) -> ServiceRequest
    
    def submit_meter_change(self, request: ServiceRequest) -> ServiceRequest
    
    def approve_meter_change(self, request: ServiceRequest) -> ServiceRequest
    
    def complete_meter_change(self, request: ServiceRequest) -> ServiceRequest
Validations:

Meter exists (METER_NOT_FOUND)

No pending disputes (METER_LOCKED)

Flow:

text
DRAFT → SUBMITTED → PENDING → IN_PROGRESS → DELIVERED
                (approved)  (install)    (complete)
4.4 WaterLeakComplaintService ⭐ (Most Sophisticated)
Purpose: Emergency leak reporting with severity-based SLA and field team dispatch.

Class:

python
class WaterLeakComplaintService:
    def __init__(self, db_service=None):
        self.db_service = db_service
    
    def create_leak_complaint(
        self,
        location_description: str,
        leak_type: LeakType,           # MINOR, MAJOR, WATER_MAIN_BURST, PIPE_SEEPAGE
        severity: LeakSeverity,        # LOW, MEDIUM, HIGH, CRITICAL
        consumer_number: str = None,   # Optional for anonymous
        affected_residents: int = 0
    ) -> ServiceRequest
    
    def submit_leak_complaint(self, request: ServiceRequest) -> ServiceRequest
    
    def dispatch_field_team(self, request: ServiceRequest, team_id: str) -> ServiceRequest
    
    def mark_repair_started(self, request: ServiceRequest) -> ServiceRequest
    
    def complete_repair(self, request: ServiceRequest, repair_description: str) -> ServiceRequest
SLA Response Times:

Severity	Response Time	Example
CRITICAL	2 hours	Main burst, flooding
HIGH	4 hours	Major leak, affecting many
MEDIUM	8 hours	Significant leak, contained
LOW	24 hours	Minor drip, no urgency
Flow:

text
DRAFT → SUBMITTED → ACKNOWLEDGED → PENDING → IN_PROGRESS → DELIVERED
         (auto)     (auto)        (team     (repair     (complete)
                                   dispatched) started)
Response Output:

json
{
  "complaint_number": "LEAK_ABCD1234",
  "estimated_arrival": "2026-01-15T14:30:00",
  "message": "Leak complaint registered. Field team dispatched."
}
4.5 WaterMeterReadingService
Purpose: Allow citizens to submit self-meter readings for auto-bill generation.

Class:

python
class WaterMeterReadingService:
    def __init__(self, db_service=None):
        self.db_service = db_service
    
    def create_reading_submission(
        self,
        consumer_number: str,
        meter_number: str,
        billing_period: str,        # YYYY-MM
        meter_reading: int
    ) -> ServiceRequest
    
    def submit_reading(self, request: ServiceRequest) -> ServiceRequest
    
    def approve_reading(self, request: ServiceRequest) -> ServiceRequest
Validations:

Reading >= previous reading (READING_BELOW_PREVIOUS)

Auto-Calculation:

Consumption = current_reading - previous_reading

Rate per unit: ₹12.00

Fixed charges: ₹50.00

Bill = (consumption × 12) + 50

Due date: 15 days from generation

Flow:

text
DRAFT → SUBMITTED → ACKNOWLEDGED → IN_PROGRESS → DELIVERED
                (validate)     (calculate)   (bill generated)
4.6 WaterComplaintService
Purpose: Handle general complaints about water quality, billing issues, service interruptions, etc.

Class:

python
class WaterComplaintService:
    def __init__(self, db_service=None):
        self.db_service = db_service
    
    def create_complaint(
        self,
        consumer_number: str,
        category: ComplaintCategory,  # WATER_QUALITY, BILLING_ISSUE, etc.
        subject: str,
        description: str,
        severity: str                  # LOW, MEDIUM, HIGH
    ) -> ServiceRequest
    
    def submit_complaint(self, request: ServiceRequest) -> ServiceRequest
    
    def assign_complaint(self, request: ServiceRequest, officer_id: str) -> ServiceRequest
    
    def start_investigation(self, request: ServiceRequest) -> ServiceRequest
    
    def resolve_complaint(self, request: ServiceRequest, resolution: str) -> ServiceRequest
Complaint Categories:

Category	Description
WATER_QUALITY	Dirty water, bad taste/smell
BILLING_ISSUE	Wrong bill amount, duplicate bill
SERVICE_INTERRUPTION	No water supply
METER_ISSUE	Meter not working
ILLING_ISSUE	Wrong bill amount, duplicate bill
SERVICE_INTERRUPTION	No water supply
METER_ISSUE	Meter not working, wrong reading
PRESSURE_LOW	Low water pressure
DISCONNECTION	Wrongful disconnection
OTHER	Anything else
Flow:

text
DRAFT → SUBMITTED → ACKNOWLEDGED → PENDING → DELIVERED
                (assigned)    (investigating) (resolved)
5. Error Codes
User Errors
Code	Description
INVALID_DATA	Invalid input format
UNAUTHORIZED	Not authorized for this action
CONFLICT	Duplicate request
Consumer/Account Errors
Code	Description
CONSUMER_NOT_FOUND	Consumer account not found
ACCOUNT_INACTIVE	Account is suspended
BILL_NOT_FOUND	No bill for specified period
INSUFFICIENT_AMOUNT	Payment amount too low
PAYMENT_FAILED	Payment processing failed
DUPLICATE_PAYMENT	Bill already paid
Connection Errors
Code	Description
OUT_OF_SERVICE_AREA	Address outside service zone
EXISTING_CONNECTION	Active connection already exists
DOCUMENT_INVALID	Required documents invalid
APPLICANT_UNVERIFIED	Identity not verified
CAPACITY_LIMIT	No capacity in area
Meter Errors
Code	Description
METER_NOT_FOUND	Meter not found
METER_LOCKED	Meter has pending disputes
METER_MISMATCH	Meter doesn't match consumer
INSTALLATION_FAILED	Installation failed
CALIBRATION_FAILURE	Meter calibration failed
Reading Errors
Code	Description
READING_INVALID	Invalid reading value
READING_BELOW_PREVIOUS	Reading less than previous
PHOTO_UNCLEAR	Meter photo unclear
System Errors
Code	Description
DEPARTMENT_TIMEOUT	Department system timeout
INTEGRATION_FAILURE	External system error
INTERNAL_ERROR	Internal system error
6. API Reference
WaterKioskAPI Class
python
class WaterKioskAPI:
    def __init__(self, service_manager: WaterServiceManager)
6.1 Pay Bill
python
def pay_bill(
    self,
    user_id: str,
    consumer_number: str,
    billing_period: str,
    amount: str,
    payment_method: str
) -> Dict[str, Any]
Request:

json
{
  "user_id": "CUST_001",
  "consumer_number": "WTR123456",
  "billing_period": "2026-01",
  "amount": "1200.00",
  "payment_method": "UPI"
}
Success Response:

json
{
  "success": true,
  "service_request_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "DELIVERED",
  "receipt": {
    "receipt_number": "WATER_RECEIPT_20260115_103000",
    "consumer_number": "WTR123456",
    "amount_paid": "1200.00",
    "billing_period": "2026-01",
    "payment_method": "UPI",
    "transaction_id": "TXN_ABC123",
    "timestamp": "2026-01-15T10:30:00",
    "status": "PAID"
  }
}
Error Response:

json
{
  "success": false,
  "error_code": "CONSUMER_NOT_FOUND",
  "error_message": "Consumer account WTR123456 not found"
}
6.2 New Connection
python
def new_connection(
    self,
    applicant_id: str,
    applicant_name: str,
    phone: str,
    email: str,
    address: str,
    connection_type: str,
    load_requirement: int
) -> Dict[str, Any]
Request:

json
{
  "applicant_id": "APP_001",
  "applicant_name": "Priya Sharma",
  "phone": "9876543210",
  "email": "priya@example.com",
  "address": "123 Main Street, Apt 4B",
  "connection_type": "DOMESTIC",
  "load_requirement": 1000
}
Response:

json
{
  "success": true,
  "service_request_id": "550e8400-e29b-41d4-a716-446655440001",
  "status": "PENDING",
  "message": "New connection request submitted. Inspection will be scheduled soon."
}
6.3 Report Leak
python
def report_leak(
    self,
    location: str,
    leak_type: str,
    severity: str,
    consumer_number: str = None,
    affected_residents: int = 0
) -> Dict[str, Any]
Request:

json
{
  "location": "Main Street, Near Traffic Signal",
  "leak_type": "MAJOR",
  "severity": "HIGH",
  "consumer_number": "WTR123456",
  "affected_residents": 5
}
Response:

json
{
  "success": true,
  "service_request_id": "550e8400-e29b-41d4-a716-446655440002",
  "status": "PENDING",
  "complaint_number": "LEAK_ABCD1234",
  "estimated_arrival": "2026-01-15T14:30:00",
  "message": "Leak complaint registered. Field team dispatched."
}
6.4 Get Request Status
python
def get_request_status(
    self,
    service_request_id: str,
    user_id: str
) -> Dict[str, Any]
Response:

json
{
  "service_request_id": "550e8400-e29b-41d4-a716-446655440001",
  "status": "PENDING",
  "message": "Request is being processed"
}
7. Usage Examples
Example 1: Complete Bill Payment Flow
python
from department.water import WaterServiceManager, WaterKioskAPI
from decimal import Decimal

# Initialize
manager = WaterServiceManager()
kiosk = WaterKioskAPI(manager)

# Pay bill
result = kiosk.pay_bill(
    user_id="CUST_001",
    consumer_number="WTR123456",
    billing_period="2026-01",
    amount="1200.00",
    payment_method="UPI"
)

if result["success"]:
    print(f"Payment successful! Receipt: {result['receipt']['receipt_number']}")
    print(f"Amount paid: ₹{result['receipt']['amount_paid']}")
else:
    print(f"Payment failed: {result['error_message']}")
Example 2: Complete Leak Report Flow
python
from department.water import WaterServiceManager, WaterKioskAPI

manager = WaterServiceManager()
kiosk = WaterKioskAPI(manager)

# Report leak
result = kiosk.report_leak(
    location="Main Street, Near Traffic Signal",
    leak_type="MAJOR",
    severity="HIGH",
    consumer_number="WTR123456",
    affected_residents=5
)

print(f"Complaint #{result['complaint_number']} registered")
print(f"Team will arrive by: {result['estimated_arrival']}")

# Later, check status
status = kiosk.get_request_status(
    service_request_id=result["service_request_id"],
    user_id="CUST_001"
)
print(f"Current status: {status['status']}")
Example 3: New Connection Application
python
from department.water import WaterServiceManager, WaterKioskAPI

manager = WaterServiceManager()
kiosk = WaterKioskAPI(manager)

# Apply for connection
result = kiosk.new_connection(
    applicant_id="APP_001",
    applicant_name="Priya Sharma",
    phone="9876543210",
    email="priya@example.com",
    address="123 Main Street, Apt 4B",
    connection_type="DOMESTIC",
    load_requirement=1000
)

print(f"Application submitted: {result['service_request_id']}")
print(f"Status: {result['message']}")

# After approval and activation, you would get:
# - consumer_number
# - meter_number
# - first_billing_date
Example 4: Direct Service Usage (Without API)
python
from department.water import (
    WaterServiceManager,
    WaterMeterReadingService,
    ServiceStatus
)
from decimal import Decimal

# Use manager
manager = WaterServiceManager()

# Submit meter reading
reading_service = manager.meter_reading_service

request = reading_service.create_reading_submission(
    consumer_number="WTR123456",
    meter_number="MTR_WTR_0001",
    billing_period="2026-01",
    meter_reading=45230
)

request = reading_service.submit_reading(request)

if request.status != ServiceStatus.DENIED:
    request = reading_service.approve_reading(request)
    
    if request.status == ServiceStatus.DELIVERED:
        print(f"Bill generated: {request.payload['bill_number']}")
        print(f"Amount: ₹{request.payload['calculated_bill']}")
        print(f"Due date: {request.payload['due_date']}")
else:
    print(f"Reading rejected: {request.error_message}")
8. Integration Guide
8.1 Package Structure
text
water/
├── __init__.py                 # Package exports
├── Water_Services_Complete.py  # All implementations
└── Water_Database_Schema.sql   # Database schema
8.2 Import Patterns
python
# Import everything
from department.water import *

# Import specific items
from department.water import (
    WaterServiceManager,
    WaterKioskAPI,
    ServiceStatus,
    LeakSeverity,
    ErrorCode
)

# Import with alias
from department.water import WaterServiceManager as WaterManager
8.3 Initialization
python
# Basic initialization (mock DB and payment)
manager = WaterServiceManager()

# With database and payment gateway
manager = WaterServiceManager(
    db_service=my_postgres_connection,
    payment_gateway=my_razorpay_client
)

# Get KIOSK API
kiosk = WaterKioskAPI(manager)
8.4 Database Integration Points
The services expect the following database methods (to be implemented):

python
# For WaterPayBillService
- consumer_exists(consumer_number) -> bool
- account_active(consumer_number) -> bool
- bill_exists(consumer_number, period) -> bool

# For WaterConnectionRequestService
- address_in_service_area(address) -> bool
- existing_connection_exists(address) -> bool

# For WaterMeterChangeService
- meter_exists(meter_number) -> bool
- meter_has_pending_disputes(meter_number) -> bool

# For WaterMeterReadingService
- get_previous_reading(consumer_number) -> int
8.5 Payment Gateway Integration
python
# The payment gateway should implement:
class PaymentGateway:
    def process_payment(self, amount: Decimal, method: str) -> Dict:
        return {
            "success": bool,
            "transaction_id": str,
            "error": str  # if failed
        }
9. Database Schema
The module expects the following tables (see Water_Database_Schema.sql):

Core Tables (Shared)
service_requests - Core request tracking

service_request_history - Status change audit

Water-Specific Tables
water_consumers - Consumer profiles

water_meters - Meter master data

water_bills - Bill records

water_bill_payments - Payment transactions

water_meter_readings - Reading history

water_leak_complaints - Leak reports

water_connection_requests - New connection applications

water_meter_changes - Meter replacement records

water_complaints - General complaints

water_field_teams - Field team management

water_service_audit_log - Audit trail

10. Quick Reference
Enums
python
# Service Status
ServiceStatus.DRAFT
ServiceStatus.SUBMITTED
ServiceStatus.ACKNOWLEDGED
ServiceStatus.PENDING
ServiceStatus.APPROVED
ServiceStatus.IN_PROGRESS
ServiceStatus.DELIVERED
ServiceStatus.DENIED
ServiceStatus.FAILED
ServiceStatus.CANCELLED

# Service Types
ServiceType.WATER_PAY_BILL
ServiceType.WATER_CONNECTION_REQUEST
ServiceType.WATER_METER_CHANGE
ServiceType.WATER_LEAK_COMPLAINT
ServiceType.WATER_METER_READING_SUBMISSION
ServiceType.WATER_COMPLAINT_GRIEVANCE

# Leak Severity
LeakSeverity.LOW
LeakSeverity.MEDIUM
LeakSeverity.HIGH
LeakSeverity.CRITICAL

# Leak Type
LeakType.MINOR
LeakType.MAJOR
LeakType.WATER_MAIN_BURST
LeakType.PIPE_SEEPAGE

# Connection Type
ConnectionType.DOMESTIC
ConnectionType.COMMERCIAL
ConnectionType.INDUSTRIAL

# Complaint Category
ComplaintCategory.WATER_QUALITY
ComplaintCategory.BILLING_ISSUE
ComplaintCategory.SERVICE_INTERRUPTION
ComplaintCategory.METER_ISSUE
ComplaintCategory.PRESSURE_LOW
ComplaintCategory.DISCONNECTION
ComplaintCategory.OTHER
Error Handling Template
python
def safe_api_call():
    try:
        result = kiosk.pay_bill(...)
        if not result["success"]:
            # Handle specific error codes
            if result["error_code"] == "CONSUMER_NOT_FOUND":
                # Show "Please register" message
            elif result["error_code"] == "PAYMENT_FAILED":
                # Retry with different method
            else:
                # Show generic error
        return result
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return {"success": False, "error_message": "System error"}
📝 Version History
Version	Date	Changes
1.0.0	2026-01-15	Initial release with all 6 services, manager, and API
👥 Authors
SUVIDHA 2026 Team

📄 License
MIT

text

---

## 📋 **Summary**

| Module | Services | Manager | API | Database Schema | Documentation |
|--------|----------|---------|-----|-----------------|---------------|
| **Electricity** | 6 services | ✅ | ✅ | ✅ | Need to create |
| **Water** | 6 services | ✅ | ✅ | ✅ | ✅ Complete |
| **Municipal** | 8 services | ❌ | ❌ | ❌ | ✅ Complete |

### Next Steps:

1. **Create Electricity README** (similar to Water format)
2. **Implement missing Municipal components**:
   - `MunicipalServiceManager`
   - `MunicipalKioskAPI`
   - `__init__.py`
   - Database schema
3. **Create unified database schema** for all departments (as discussed earlier)

Would you like me to create the **Electricity README** next, or help implement the missing Municipal components?
