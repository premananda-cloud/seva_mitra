### README.md for Electricity Module

markdown  
\# SUVIDHA Electricity Services Module

\#\# 📋 Overview  
This module provides a complete service framework for electricity utility operations. It implements a state machine-based request lifecycle for all citizen-facing services.

\#\# 🎯 Services Provided

| Service | Description | Who Can Use |  
|---------|-------------|-------------|  
| \`ELECTRICITY\_PAY\_BILL\` | Pay electricity bills via UPI, Card, Net Banking | Citizens |  
| \`ELECTRICITY\_SERVICE\_TRANSFER\` | Transfer connection ownership to new customer | Citizens (both parties) |  
| \`ELECTRICITY\_METER\_CHANGE\` | Replace faulty/damaged meters | Department only |  
| \`ELECTRICITY\_CONNECTION\_REQUEST\` | Apply for new electricity connection | Citizens |  
| \`ELECTRICITY\_COMPLAINT\` | File complaints (billing, outage, meter issues) | Citizens |  
| \`ELECTRICITY\_METER\_READING\_SUBMISSION\` | Submit self-meter readings | Citizens |

\#\# 🔄 State Machine

All requests follow this lifecycle:

DRAFT → SUBMITTED → ACKNOWLEDGED → PENDING → APPROVED → IN\_PROGRESS → DELIVERED  
↓ ↓ ↓ ↓ ↓  
DENIED DENIED DENIED CANCELLED FAILED (can retry)  
text  
\#\#\# Status Descriptions

| Status | Owner | Description |  
|--------|-------|-------------|  
| \`DRAFT\` | User | Being prepared, not yet submitted |  
| \`SUBMITTED\` | System | Sent for processing |  
| \`ACKNOWLEDGED\` | Department | Received and assigned |  
| \`PENDING\` | Department | Awaiting action (inspection, approval) |  
| \`APPROVED\` | Department | Approved, ready for execution |  
| \`IN\_PROGRESS\` | System | Being executed |  
| \`DELIVERED\` | System | Completed successfully |  
| \`DENIED\` | Department | Rejected (terminal) |  
| \`FAILED\` | System | Error occurred, can retry |  
| \`CANCELLED\` | User/Dept | Withdrawn (terminal) |

\#\# 🏗️ Architecture

┌─────────────────────────────────────────────────────┐  
│ KIOSK API Layer │  
│ (ElectricityKioskAPI \- HTTP interface) │  
└─────────────────────┬───────────────────────────────┘  
│  
┌─────────────────────▼───────────────────────────────┐  
│ Service Manager │  
│ (ElectricityServiceManager \- routes to handlers) │  
└─────────────────────┬───────────────────────────────┘  
│  
┌─────────────┼─────────────┬─────────────┐  
▼ ▼ ▼ ▼  
┌───────────────┐ ┌───────────┐ ┌───────────┐ ┌───────────┐  
│ PayBillService│ │TransferSvc│ │Complaint │ │MeterReading│  
└───────────────┘ └───────────┘ └───────────┘ └───────────┘  
│ │ │ │  
└─────────────┼─────────────┼─────────────┘  
▼  
┌─────────────────────────────────────────────────────┐  
│ Validation Layer │  
│ (ElectricityValidationService) │  
└─────────────────────────────────────────────────────┘  
text  
\#\# 📦 Package Structure

electricity/  
├── init.py \# Package exports & helpers  
├── Electricity\_Services.py \# Main implementation  
└── Electricity\_Database\_Schema.sql \# PostgreSQL schema  
text  
\#\# 🚀 How to Use

\#\#\# 1\. Initialize the Module  
\`\`\`python  
from department.electricity import initialize\_package, create\_kiosk\_api

\# With database and payment gateway  
manager \= initialize\_package(  
    db\_service=my\_database\_connection,  
    payment\_gateway=my\_payment\_gateway  
)

\# Or get ready-to-use API layer  
kiosk\_api \= create\_kiosk\_api(db\_service, payment\_gateway)

### 2\. Process a Bill Payment

python  
result \= kiosk\_api.pay\_bill(  
    user\_id="123456789012",  
    meter\_number="ELEC123456",  
    billing\_period="2026-01",  
    amount="1500.00",  
    payment\_method="UPI"  
)

if result\["success"\]:  
    print(f"Payment successful\! Receipt: {result\['receipt'\]}")  
else:  
    print(f"Failed: {result\['error\_message'\]}")

### 3\. File a Complaint

python  
result \= kiosk\_api.file\_complaint(  
    user\_id="123456789012",  
    meter\_number="ELEC123456",  
    category="POWER\_OUTAGE",  
    priority="HIGH",  
    description="No power since 2 hours in Sector 15",  
    contact\_phone="9876543210"  
)

print(f"Complaint filed: {result\['complaint\_number'\]}")  
print(f"Expected response: {result\['expected\_response\_hours'\]} hours")

### 4\. Submit Meter Reading

python  
result \= kiosk\_api.submit\_meter\_reading(  
    user\_id="123456789012",  
    meter\_number="ELEC123456",  
    reading\_value="1250.5",  
    photo\_ref="meter\_photo\_001.jpg"  
)

if result.get("bill"):  
    print(f"Bill generated: ₹{result\['bill'\]\['amount'\]}")

## 🔍 Error Codes Reference

| Code | Description | When It Occurs |
| :---- | :---- | :---- |
| INVALID\_DATA | Invalid input format | Wrong meter format, invalid amount |
| METER\_NOT\_FOUND | Meter doesn't exist | Unknown meter number |
| METER\_INACTIVE | Meter is suspended | Account locked |
| BILL\_NOT\_FOUND | No bill for period | Wrong billing period |
| PAYMENT\_FAILED | Payment declined | Insufficient funds, gateway error |
| PENDING\_TRANSFER\_EXISTS | Transfer already in progress | Duplicate request |
| INTEGRATION\_FAILURE | External system error | Payment gateway down |

## 📊 Database Schema

The module expects these tables (see Electricity\_Database\_Schema.sql):

* service\_requests \- Core request tracking  
* service\_request\_history \- Status change audit  
* electricity\_customers \- Customer profiles  
* electricity\_meters \- Meter master data  
* electricity\_bills \- Bill records  
* electricity\_payments \- Payment transactions  
* electricity\_complaints \- Complaint records  
* electricity\_meter\_readings \- Meter reading history  
* electricity\_service\_transfers \- Transfer records  
* electricity\_connection\_requests \- New connection applications

## 🧪 Testing

Generate sample requests for testing:  
python  
from department.electricity import (  
    generate\_sample\_bill\_request,  
    generate\_sample\_transfer\_request  
)

bill\_req \= generate\_sample\_bill\_request()  
transfer\_req \= generate\_sample\_transfer\_request()

print(bill\_req.to\_dict(include\_history=True))

## 🔧 Extending the Module

To add a new service type:

1. Add to ServiceType enum  
2. Create new service class (extend pattern)  
3. Add to ElectricityServiceManager  
4. Add method to ElectricityKioskAPI  
5. Update get\_service\_handler\_map() in \_\_init\_\_.py

## 📈 Version History

* 1.0.0 \- Initial release with core services (pay bill, transfer, meter change, connection)  
* 1.1.0 \- Added Complaint and Meter Reading services

## 👥 Authors

SUVIDHA 2026 Team

## 📄 License

MIT  
text  
\---

\#\# 🎯 \*\*Summary of Changes\*\*

| What | Status | Description |  
|------|--------|-------------|  
| \`ElectricityComplaintService\` | ✅ NEW | File and track complaints with priority/SLA |  
| \`ElectricityMeterReadingSubmissionService\` | ✅ NEW | Submit self-readings, auto-calculate bills |  
| Updated Service Manager | ✅ MODIFIED | Added both services to registry |  
| Updated KIOSK API | ✅ MODIFIED | Added API methods for both services |  
| Documentation | ✅ NEW | Complete README with examples |  
| Error Codes | ✅ COMPLETE | All error cases covered |

The module now provides \*\*complete coverage\*\* of all electricity services citizens would need:  
\- 💰 Pay bills  
\- 📝 File complaints    
\- 📊 Submit readings  
\- 🔄 Transfer connections  
\- 🏠 New connections  
\- 🔧 Meter changes (department)

Each service follows the same state machine pattern, making the system consistent and easy to understand.  
