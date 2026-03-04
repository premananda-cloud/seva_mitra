# 🏛️ SUVIDHA Municipal Services Module

**Version:** 1.0.0  
**Department:** Municipal  
**Pattern:** ServiceRequest State Machine  
**Status:** ✅ Complete (Services Implemented)

---

## 📋 Table of Contents
1. [Overview](#overview)
2. [Services Summary](#services-summary)
3. [State Machine](#state-machine)
4. [Service Details](#service-details)
5. [Error Codes](#error-codes)
6. [Usage Examples](#usage-examples)
7. [Integration Guide](#integration-guide)
8. [Database Schema](#database-schema)
9. [Missing Pieces](#missing-pieces)

---

## 1. Overview

The Municipal Services module provides a comprehensive service framework for urban local body operations. It follows the same state machine pattern as Electricity and Water departments, ensuring consistency across all citizen services.

### Key Features
- 🏠 **Property Tax Management** - Pay annual/arrear property taxes
- 📜 **Trade License** - New applications and renewals
- 👶 **Birth Certificates** - Register births and request certificates
- ⚰️ **Death Certificates** - Register deaths and request certificates
- 🏗️ **Building Plan Approval** - Approve construction plans
- 🗑️ **Sanitation Complaints** - Report garbage, drain, and cleanliness issues
- 📢 **General Grievances** - Any other citizen complaints

---

## 2. Services Summary

| # | Service Type | Class | Description |
|---|--------------|-------|-------------|
| 1 | `MUNICIPAL_PROPERTY_TAX_PAYMENT` | `PropertyTaxPaymentService` | Pay property tax for residential/commercial properties |
| 2 | `MUNICIPAL_TRADE_LICENSE_NEW` | `TradeLicenseService` | Apply for new trade/business license |
| 3 | `MUNICIPAL_TRADE_LICENSE_RENEWAL` | `TradeLicenseService` | Renew existing trade license |
| 4 | `MUNICIPAL_BIRTH_CERTIFICATE` | `BirthCertificateService` | Request birth certificate |
| 5 | `MUNICIPAL_DEATH_CERTIFICATE` | `DeathCertificateService` | Request death certificate |
| 6 | `MUNICIPAL_BUILDING_PLAN_APPROVAL` | `BuildingPlanApprovalService` | Submit building plans for approval |
| 7 | `MUNICIPAL_SANITATION_COMPLAINT` | `SanitationComplaintService` | Report garbage/drain/cleanliness issues |
| 8 | `MUNICIPAL_GENERAL_GRIEVANCE` | `GeneralGrievanceService` | Any other citizen complaint |

---

## 3. State Machine

All requests follow the canonical SUVIDHA state machine:
┌─────────┐
┌───▶│CANCELLED│◀───┐
│ └─────────┘ │
┌────┴────┐ ┌────┴────┐
┌───▶│ DRAFT │───┐ │ DENIED │◀───┐
│ └─────────┘ │ └─────────┘ │
│ ▼ │
│ ┌─────────────┐ │
│ │ SUBMITTED │──┐ │
│ └─────────────┘ │ │
│ │ ▼ │
│ ▼ ┌─────────────┐ │
│ ┌─────────────┐ │ FAILED │──┐
│ │ACKNOWLEDGED │ └─────────────┘ │
│ └─────────────┘ ▲ │
│ │ │ │
│ ▼ │ │
│ ┌─────────────┐ │ │
│ │ PENDING │──────────┘ │
│ └─────────────┘ │
│ │ │
│ ▼ │
│ ┌─────────────┐ │
│ │ APPROVED │──┐ │
│ └─────────────┘ │ │
│ │ ▼ │
│ ▼ ┌─────────────┐ │
│ ┌─────────────┐ │ IN_PROGRESS│ │
│ │IN_PROGRESS │ └─────────────┘ │
│ └─────────────┘ │
│ │ │
│ ▼ │
│ ┌─────────────┐ │
└───────────▶│ DELIVERED │◀─────────────────┘
└─────────────┘

text

### Status Descriptions

| Status | Owner | Description |
|--------|-------|-------------|
| `DRAFT` | User | Being prepared, not yet submitted |
| `SUBMITTED` | System | Sent for processing |
| `ACKNOWLEDGED` | Department | Received and assigned |
| `PENDING` | Department | Awaiting action (inspection, verification) |
| `APPROVED` | Department | Approved, ready for execution |
| `IN_PROGRESS` | System | Being executed (certificate generation, etc.) |
| `DELIVERED` | System | Completed successfully |
| `DENIED` | Department | Rejected (terminal) |
| `FAILED` | System | Error occurred, can retry |
| `CANCELLED` | User/Dept | Withdrawn (terminal) |

---

## 4. Service Details

### 4.1 PropertyTaxPaymentService

**Purpose:** Handle property tax payments for residential, commercial, and industrial properties.

**Class:**
```python
class PropertyTaxPaymentService:
    def create_request(
        self,
        consumer_number: str,    # Property tax account number
        property_id: str,        # Unique property identifier
        user_id: str,            # Citizen ID/Aadhar
        tax_year: str,           # e.g., "2025-2026"
        amount: Decimal,         # Payment amount
        payment_method: str      # UPI, CARD, NET_BANKING
    ) -> ServiceRequest
Flow:

text
create_request() → [DRAFT] 
                 → SUBMITTED (auto)
                 → process_payment() → ACKNOWLEDGED → DELIVERED
                 → FAILED (if payment fails)
Receipt Output:

json
{
  "receipt_type": "Property Tax Receipt",
  "property_id": "PROP_001",
  "consumer_number": "PTAX123456",
  "tax_year": "2025-2026",
  "amount_paid": "5000.00",
  "payment_method": "UPI",
  "payment_id": "PAY_123",
  "generated_at": "2026-01-15T10:30:00"
}
4.2 TradeLicenseService
Purpose: Handle both new trade license applications and annual renewals.

Class:

python
class TradeLicenseService:
    def create_request(
        self,
        applicant_id: str,
        applicant_name: str,
        business_name: str,
        business_type: str,           # Retail, Food, Manufacturing, Services
        address: str,
        ward_number: str,
        identity_proof: str,          # Document reference
        address_proof: str,           # Document reference
        is_renewal: bool = False,
        existing_license_no: Optional[str] = None
    ) -> ServiceRequest
    
    def acknowledge(self, req: ServiceRequest) -> ServiceRequest
    def approve(self, req: ServiceRequest, officer_id: str, license_no: str) -> ServiceRequest
    def deny(self, req: ServiceRequest, reason: str) -> ServiceRequest
    def deliver(self, req: ServiceRequest) -> ServiceRequest
Flow:

text
New License:
DRAFT → SUBMITTED → ACKNOWLEDGED → APPROVED → DELIVERED
                            ↓
                         DENIED

Renewal:
DRAFT → SUBMITTED → ACKNOWLEDGED → APPROVED → DELIVERED
Business Types:

Retail - Shops, stores

Food - Restaurants, cafes, food stalls

Manufacturing - Factories, production units

Services - Salons, repair shops, consultants

4.3 BirthCertificateService
Purpose: Register births and issue birth certificates.

Class:

python
class BirthCertificateService:
    def create_request(
        self,
        applicant_id: str,
        child_name: str,
        dob: str,                    # YYYY-MM-DD
        place_of_birth: str,
        father_name: str,
        mother_name: str,
        hospital_name: Optional[str],
        identity_proof: str
    ) -> ServiceRequest
    
    def process(
        self, 
        req: ServiceRequest, 
        officer_id: str, 
        cert_number: str
    ) -> ServiceRequest
Flow:

text
DRAFT → SUBMITTED → ACKNOWLEDGED → DELIVERED
                (records verified) (certificate issued)
4.4 DeathCertificateService
Purpose: Register deaths and issue death certificates.

Class:

python
class DeathCertificateService:
    def create_request(
        self,
        applicant_id: str,
        deceased_name: str,
        date_of_death: str,          # YYYY-MM-DD
        place_of_death: str,
        cause_of_death: str,
        informant_name: str,
        identity_proof: str,
        medical_certificate: str      # Medical certificate reference
    ) -> ServiceRequest
    
    def process(
        self, 
        req: ServiceRequest, 
        officer_id: str, 
        cert_number: str
    ) -> ServiceRequest
Required Documents:

Medical certificate from doctor/hospital

Identity proof of informant

Death proof (if applicable)

4.5 BuildingPlanApprovalService
Purpose: Review and approve building construction plans.

Class:

python
class BuildingPlanApprovalService:
    def create_request(
        self,
        applicant_id: str,
        applicant_name: str,
        property_id: str,
        plot_area: float,            # in sq meters
        built_up_area: float,        # in sq meters
        floors: int,
        building_type: str,          # Residential, Commercial, Industrial
        architect_name: str,
        identity_proof: str,
        land_ownership_proof: str,
        blueprint_ref: str
    ) -> ServiceRequest
    
    def schedule_inspection(
        self, 
        req: ServiceRequest, 
        inspection_date: str
    ) -> ServiceRequest
    
    def approve(
        self, 
        req: ServiceRequest, 
        officer_id: str, 
        approval_no: str
    ) -> ServiceRequest
    
    def deny(
        self, 
        req: ServiceRequest, 
        reason: str
    ) -> ServiceRequest
Flow:

text
DRAFT → SUBMITTED → PENDING → APPROVED → DELIVERED
                (inspection)      ↓
                               DENIED
4.6 SanitationComplaintService
Purpose: Handle complaints about garbage, drains, and sanitation.

Class:

python
class SanitationComplaintService:
    def create_request(
        self,
        consumer_id: str,
        complaint_category: str,     # From ComplaintCategory enum
        location: str,
        ward_number: str,
        description: str,
        severity: str = "Medium",    # Low, Medium, High, Critical
        photo_ref: Optional[str] = None
    ) -> ServiceRequest
    
    def assign(
        self, 
        req: ServiceRequest, 
        field_officer_id: str
    ) -> ServiceRequest
    
    def resolve(
        self, 
        req: ServiceRequest, 
        resolution_notes: str
    ) -> ServiceRequest
Complaint Categories:

Category	Description
GARBAGE_NOT_COLLECTED	Waste not picked up
DRAIN_BLOCKED	Blocked drainage/sewage
STREET_LIGHT_FAULT	Street light not working
ROAD_DAMAGE	Potholes, damaged roads
ILLEGAL_CONSTRUCTION	Unauthorized construction
NOISE_POLLUTION	Excessive noise
OTHER	Any other sanitation issue
Flow:

text
DRAFT → SUBMITTED → IN_PROGRESS → DELIVERED
                (assigned)    (resolved)
4.7 GeneralGrievanceService
Purpose: Catch-all service for any citizen complaint not covered by specific categories.

Class:

python
class GeneralGrievanceService:
    def create_request(
        self,
        citizen_id: str,
        subject: str,
        description: str,
        dept_ref: Optional[str] = None,   # Sub-department reference
        attachment: Optional[str] = None
    ) -> ServiceRequest
    
    def acknowledge(
        self, 
        req: ServiceRequest, 
        ticket_no: str
    ) -> ServiceRequest
    
    def resolve(
        self, 
        req: ServiceRequest, 
        response: str, 
        officer_id: str
    ) -> ServiceRequest
Flow:

text
DRAFT → SUBMITTED → ACKNOWLEDGED → DELIVERED
                (ticket issued) (resolved)
5. Error Codes
Code	Description	When It Occurs
INVALID_DATA	Invalid input format	Missing required fields, wrong format
CONSUMER_NOT_FOUND	Consumer account doesn't exist	Invalid property tax number
ACCOUNT_INACTIVE	Account is suspended	Property tax account locked
DUPLICATE_REQUEST	Duplicate submission	Same request already exists
DOCUMENT_INVALID	Invalid documents	Identity/address proof rejected
APPLICANT_UNVERIFIED	Applicant not verified	Identity check failed
PAYMENT_FAILED	Payment processing failed	Gateway error, insufficient funds
PROPERTY_NOT_FOUND	Property not in database	Invalid property ID
TAX_ALREADY_PAID	Tax already paid for year	Duplicate payment attempt
LICENSE_NOT_FOUND	License doesn't exist	Invalid license number for renewal
ZONE_RESTRICTED	Business not allowed in zone	Zoning violation
INTERNAL_ERROR	System error	Unexpected server error
6. Usage Examples
Example 1: Property Tax Payment
python
from municipal.municipal_services import PropertyTaxPaymentService
from decimal import Decimal

# Initialize service
tax_service = PropertyTaxPaymentService()

# Create payment request
request = tax_service.create_request(
    consumer_number="PTAX123456",
    property_id="PROP_001",
    user_id="CUST_001",
    tax_year="2025-2026",
    amount=Decimal("5000.00"),
    payment_method="UPI"
)

# After payment gateway success
request = tax_service.process_payment(request, payment_id="PAY_123")

# Generate receipt
receipt = tax_service.generate_receipt(request)
print(receipt)
Example 2: Trade License Application
python
from municipal.municipal_services import TradeLicenseService

license_service = TradeLicenseService()

# New license application
request = license_service.create_request(
    applicant_id="APP_001",
    applicant_name="John Store",
    business_name="John's Grocery",
    business_type="Retail",
    address="123 Main St, Sector 15",
    ward_number="Ward-5",
    identity_proof="AADHAR_123",
    address_proof="RENT_001",
    is_renewal=False
)

# Department officer actions
request = license_service.acknowledge(request)
request = license_service.approve(
    request, 
    officer_id="OFF_001", 
    license_no="LIC_2026_001"
)
request = license_service.deliver(request)

print(f"License issued: {request.payload['issued_license_no']}")
Example 3: Sanitation Complaint
python
from municipal.municipal_services import SanitationComplaintService

complaint_service = SanitationComplaintService()

# File complaint
request = complaint_service.create_request(
    consumer_id="CONS_001",
    complaint_category="GARBAGE_NOT_COLLECTED",
    location="123 Main St, Sector 15",
    ward_number="Ward-5",
    description="Garbage not collected for 5 days, foul smell",
    severity="High",
    photo_ref="garbage_photo_001.jpg"
)

# Assign to field officer
request = complaint_service.assign(request, field_officer_id="FIELD_001")

# Resolve after cleanup
request = complaint_service.resolve(
    request, 
    "Garbage collected, area sanitized"
)

print(f"Complaint {request.service_request_id} resolved")
Example 4: Building Plan Approval
python
from municipal.municipal_services import BuildingPlanApprovalService

plan_service = BuildingPlanApprovalService()

# Submit plans
request = plan_service.create_request(
    applicant_id="APP_001",
    applicant_name="ABC Constructions",
    property_id="PROP_001",
    plot_area=500.0,
    built_up_area=350.0,
    floors=2,
    building_type="Residential",
    architect_name="Arch Firm",
    identity_proof="AADHAR_123",
    land_ownership_proof="DEED_001",
    blueprint_ref="BLUEPRINT_001"
)

# Schedule inspection
request = plan_service.schedule_inspection(request, "2026-02-01")

# After inspection, approve
request = plan_service.approve(
    request, 
    officer_id="OFF_001", 
    approval_no="APPR_2026_001"
)

print(f"Plan approved: {request.payload['approval_number']}")
7. Integration Guide
7.1 Required Components (Not Yet Implemented)
To fully integrate the Municipal module, you need to create:

1. MunicipalServiceManager (Missing)
python
class MunicipalServiceManager:
    """Central manager for all municipal services"""
    
    def __init__(self, db_service=None, payment_gateway=None):
        self.db_service = db_service
        self.payment_gateway = payment_gateway
        
        # Initialize all services
        self.tax_service = PropertyTaxPaymentService(db_service, payment_gateway)
        self.license_service = TradeLicenseService(db_service)
        self.birth_service = BirthCertificateService(db_service)
        self.death_service = DeathCertificateService(db_service)
        self.building_service = BuildingPlanApprovalService(db_service)
        self.sanitation_service = SanitationComplaintService(db_service)
        self.grievance_service = GeneralGrievanceService(db_service)
        
        # Service registry
        self.service_handlers = {
            MunicipalServiceType.PROPERTY_TAX_PAYMENT: self.tax_service,
            MunicipalServiceType.TRADE_LICENSE_NEW: self.license_service,
            MunicipalServiceType.TRADE_LICENSE_RENEWAL: self.license_service,
            MunicipalServiceType.BIRTH_CERTIFICATE: self.birth_service,
            MunicipalServiceType.DEATH_CERTIFICATE: self.death_service,
            MunicipalServiceType.BUILDING_PLAN_APPROVAL: self.building_service,
            MunicipalServiceType.SANITATION_COMPLAINT: self.sanitation_service,
            MunicipalServiceType.GENERAL_GRIEVANCE: self.grievance_service,
        }
2. MunicipalKioskAPI (Missing)
python
class MunicipalKioskAPI:
    """KIOSK API Layer for Municipal Services"""
    
    def __init__(self, service_manager: MunicipalServiceManager):
        self.service_manager = service_manager
    
    def pay_property_tax(self, user_id, property_id, tax_year, amount, payment_method):
        # Implementation...
        pass
    
    def apply_license(self, applicant_id, business_name, ...):
        # Implementation...
        pass
    
    def request_birth_certificate(self, applicant_id, child_name, ...):
        # Implementation...
        pass
    
    # ... other API methods
3. __init__.py (Missing)
python
"""
SUVIDHA Municipal Services Package
==================================
Municipal service implementations for urban local body operations.
"""

__version__ = "1.0.0"

from .municipal_services import (
    # Enums
    ServiceStatus,
    MunicipalServiceType,
    PropertyType,
    ComplaintCategory,
    ErrorCode,
    
    # Core Model
    ServiceRequest,
    
    # Services
    PropertyTaxPaymentService,
    TradeLicenseService,
    BirthCertificateService,
    DeathCertificateService,
    BuildingPlanApprovalService,
    SanitationComplaintService,
    GeneralGrievanceService,
)

__all__ = [
    "ServiceStatus",
    "MunicipalServiceType",
    "PropertyType",
    "ComplaintCategory",
    "ErrorCode",
    "ServiceRequest",
    "PropertyTaxPaymentService",
    "TradeLicenseService",
    "BirthCertificateService",
    "DeathCertificateService",
    "BuildingPlanApprovalService",
    "SanitationComplaintService",
    "GeneralGrievanceService",
]
7.2 Database Schema (To Be Created)
Create Municipal_Database_Schema.sql with tables for:

property_tax_records

trade_licenses

birth_certificates

death_certificates

building_plans

sanitation_complaints

grievances

8. Missing Pieces Checklist
Component	Status	Priority
MunicipalServiceManager	❌ Missing	HIGH
MunicipalKioskAPI	❌ Missing	HIGH
__init__.py	❌ Missing	HIGH
Database Schema	❌ Missing	MEDIUM
Unit Tests	❌ Missing	MEDIUM
Example Usage	✅ Complete	-
Documentation	✅ Complete	-
9. Quick Reference
Import Pattern
python
# Once __init__.py is created
from department.municipal import (
    PropertyTaxPaymentService,
    TradeLicenseService,
    BirthCertificateService,
    ServiceStatus
)

# Or direct import (currently)
from department.municipal.municipal_services import (
    PropertyTaxPaymentService,
    ServiceStatus
)
Service Status Constants
python
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
Error Handling Pattern
python
try:
    request = service.create_request(...)
except ValueError as e:
    # Handle validation errors
    print(f"Validation failed: {e}")

# Check error codes in response
if request.error_code:
    print(f"Error: {request.error_code} - {request.error_message}")
📝 Version History
Version	Date	Changes
1.0.0	2026-01-15	Initial re