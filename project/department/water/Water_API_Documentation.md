"""
SUVIDHA 2026 - Water Services REST API Documentation
===================================================
Complete API endpoints for Water Service KIOSK

Base URL: /api/v1/water
Authentication: Bearer JWT Token
Content-Type: application/json
"""

# ============================================================================
# 1. AUTHENTICATION ENDPOINTS
# ============================================================================

"""
POST /api/v1/auth/login
Generate OTP for customer login

Request:
{
    "phone": "+919876543210",
    "or_aadhar": "123456789012"
}

Response (200 OK):
{
    "success": true,
    "otp_id": "OTP_123456789",
    "message": "OTP sent to registered phone number",
    "expires_in": 300  # seconds
}

Error (400 Bad Request):
{
    "success": false,
    "error_code": "INVALID_DATA",
    "error_message": "Invalid phone number format"
}
"""

"""
POST /api/v1/auth/verify-otp
Verify OTP and generate JWT token

Request:
{
    "otp_id": "OTP_123456789",
    "otp_code": "123456"
}

Response (200 OK):
{
    "success": true,
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "expires_in": 900,  # 15 minutes
    "user": {
        "consumer_id": "CUST_001",
        "consumer_number": "WTR123456789",
        "name": "Raj Kumar",
        "phone": "+919876543210",
        "account_status": "ACTIVE"
    }
}

Error (401 Unauthorized):
{
    "success": false,
    "error_code": "UNAUTHORIZED",
    "error_message": "Invalid OTP"
}
"""

"""
POST /api/v1/auth/refresh-token
Refresh JWT token

Request:
{
    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}

Response (200 OK):
{
    "success": true,
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "expires_in": 900
}
"""

"""
POST /api/v1/auth/logout
Logout and invalidate token

Request:
{}

Response (200 OK):
{
    "success": true,
    "message": "Logged out successfully"
}
"""


# ============================================================================
# 2. CONSUMER ACCOUNT ENDPOINTS
# ============================================================================

"""
GET /api/v1/water/account/{consumer_id}
Get consumer account details

Request Headers:
Authorization: Bearer <JWT_TOKEN>

Response (200 OK):
{
    "success": true,
    "account": {
        "consumer_id": "CUST_001",
        "consumer_number": "WTR123456789",
        "name": "Raj Kumar",
        "phone": "+919876543210",
        "email": "raj@example.com",
        "address": "123 Main Street, Apt 4B",
        "connection_type": "DOMESTIC",
        "account_status": "ACTIVE",
        "payment_status": "CURRENT",
        "activation_date": "2025-01-15",
        "meter_number": "MTR_WTR_0001",
        "sanctioned_load": 1000,  # liters/day
        "last_payment_date": "2026-01-20",
        "total_outstanding": 0.00
    }
}
"""

"""
GET /api/v1/water/account/{consumer_id}/meters
Get all meters for a consumer

Response (200 OK):
{
    "success": true,
    "consumer_number": "WTR123456789",
    "meters": [
        {
            "meter_id": "uuid",
            "meter_number": "MTR_WTR_0001",
            "meter_type": "DIGITAL",
            "installation_date": "2025-01-15",
            "status": "ACTIVE",
            "last_reading_value": 45230,
            "last_reading_date": "2026-01-01"
        }
    ]
}
"""


# ============================================================================
# 3. BILL PAYMENT ENDPOINTS
# ============================================================================

"""
GET /api/v1/water/bills/{consumer_id}
Get all bills for consumer

Request Headers:
Authorization: Bearer <JWT_TOKEN>

Response (200 OK):
{
    "success": true,
    "consumer_number": "WTR123456789",
    "bills": [
        {
            "bill_id": "uuid",
            "bill_number": "WATER_BILL_202601_001",
            "billing_period": "2026-01",
            "consumption_units": 130,
            "rate_per_unit": "12.00",
            "fixed_charges": 50.00,
            "tax_amount": 21.60,
            "total_bill_amount": 1811.60,
            "amount_paid": 0.00,
            "outstanding_balance": 1811.60,
            "issued_date": "2026-02-01",
            "due_date": "2026-02-15",
            "payment_status": "PENDING"
        },
        {
            "bill_id": "uuid",
            "bill_number": "WATER_BILL_202512_001",
            "billing_period": "2025-12",
            "total_bill_amount": 1500.00,
            "amount_paid": 1500.00,
            "outstanding_balance": 0.00,
            "payment_status": "PAID",
            "issued_date": "2026-01-01",
            "due_date": "2026-01-15"
        }
    ]
}
"""

"""
GET /api/v1/water/bills/{consumer_id}/{bill_number}
Get detailed bill information

Response (200 OK):
{
    "success": true,
    "bill": {
        "bill_number": "WATER_BILL_202601_001",
        "bill_id": "uuid",
        "consumer_number": "WTR123456789",
        "meter_number": "MTR_WTR_0001",
        "billing_period": "2026-01",
        "billing_from": "2026-01-01",
        "billing_to": "2026-01-31",
        "opening_reading": 45100,
        "closing_reading": 45230,
        "consumption_units": 130,
        "rate_per_unit": "12.00",
        "amount_consumption": 1560.00,
        "fixed_charges": 50.00,
        "sewer_charges": 156.00,
        "water_tax": 45.60,
        "total_charges": 1811.60,
        "tax_amount": 0.00,
        "total_bill_amount": 1811.60,
        "payment_status": "PENDING",
        "due_date": "2026-02-15",
        "issued_date": "2026-02-01",
        "penalty_charges": 0.00
    }
}
"""

"""
POST /api/v1/water/pay-bill
Pay outstanding water bill

Request:
{
    "consumer_number": "WTR123456789",
    "bill_number": "WATER_BILL_202601_001",
    "billing_period": "2026-01",
    "amount": "1811.60",
    "payment_method": "UPI"
}

Response (200 OK):
{
    "success": true,
    "service_request_id": "uuid",
    "status": "DELIVERED",
    "receipt_number": "WATER_RECEIPT_20260201_001",
    "consumer_number": "WTR123456789",
    "amount_paid": 1811.60,
    "amount_previous_balance": 1811.60,
    "amount_new_balance": 0.00,
    "billing_period": "2026-01",
    "payment_timestamp": "2026-02-01T10:30:00Z",
    "next_billing_date": "2026-02-28",
    "payment_method_used": "UPI",
    "transaction_id": "UPI_TXN_20260201_001",
    "receipt": {
        "receipt_number": "WATER_RECEIPT_20260201_001",
        "consumer_number": "WTR123456789",
        "name": "Raj Kumar",
        "address": "123 Main Street, Apt 4B",
        "amount_paid": 1811.60,
        "billing_period": "2026-01",
        "payment_date": "2026-02-01",
        "transaction_id": "UPI_TXN_20260201_001"
    }
}

Error Response (400 Bad Request):
{
    "success": false,
    "error_code": "CONSUMER_NOT_FOUND",
    "error_message": "Consumer account not found in system"
}

Error Response (400 Bad Request):
{
    "success": false,
    "error_code": "ACCOUNT_INACTIVE",
    "error_message": "Account is suspended"
}

Error Response (400 Bad Request):
{
    "success": false,
    "error_code": "PAYMENT_FAILED",
    "error_message": "Payment gateway error: Insufficient funds"
}
"""

"""
POST /api/v1/water/pay-bill/partial
Make partial bill payment

Request:
{
    "consumer_number": "WTR123456789",
    "bill_number": "WATER_BILL_202601_001",
    "amount": "900.00",
    "payment_method": "NETBANKING"
}

Response (200 OK):
{
    "success": true,
    "service_request_id": "uuid",
    "status": "DELIVERED",
    "amount_paid": 900.00,
    "amount_remaining": 911.60,
    "payment_status": "PARTIAL",
    "receipt": {...}
}
"""


# ============================================================================
# 4. NEW CONNECTION REQUEST ENDPOINTS
# ============================================================================

"""
POST /api/v1/water/new-connection
Request new water supply connection

Request:
{
    "applicant_id": "AADHAR_123456789012",
    "applicant_name": "Priya Sharma",
    "phone_number": "9876543210",
    "email": "priya@example.com",
    "address": "123 Main Street, Apt 4B, City - 400001",
    "property_pin_code": "400001",
    "connection_type": "DOMESTIC",
    "purpose": "Domestic Use",
    "load_requirement": 1000,
    "property_documents_ref": "DOC_REF_001",
    "proof_of_identity_ref": "ID_REF_001"
}

Response (201 Created):
{
    "success": true,
    "service_request_id": "uuid",
    "status": "PENDING",
    "message": "New connection request submitted. Inspection will be scheduled soon.",
    "reference_number": "WATER_CONN_20260201_001",
    "applicant_name": "Priya Sharma",
    "address": "123 Main Street, Apt 4B, City - 400001",
    "connection_type": "DOMESTIC",
    "next_steps": [
        "Document verification (1-2 days)",
        "Site inspection scheduled (3-5 days)",
        "Approval and installation (5-7 days)"
    ],
    "estimated_activation": "2026-02-25",
    "customer_care": "1800-WATER-01"
}

Error Response (400):
{
    "success": false,
    "error_code": "OUT_OF_SERVICE_AREA",
    "error_message": "Property is outside our service area"
}

Error Response (400):
{
    "success": false,
    "error_code": "EXISTING_CONNECTION",
    "error_message": "Active connection already exists for this property"
}

Error Response (400):
{
    "success": false,
    "error_code": "DOCUMENT_INVALID",
    "error_message": "Uploaded property documents are invalid or expired"
}
"""

"""
GET /api/v1/water/new-connection/{service_request_id}/status
Get status of connection request

Response (200 OK):
{
    "success": true,
    "service_request_id": "uuid",
    "reference_number": "WATER_CONN_20260201_001",
    "status": "PENDING",
    "current_stage": "Inspection Scheduled",
    "inspection_date": "2026-02-10",
    "inspection_time_slot": "10:00 AM - 12:00 PM",
    "inspector_name": "Mr. Rajesh Kumar",
    "inspector_contact": "+91-9876543210",
    "timeline": [
        {
            "stage": "Application Received",
            "date": "2026-02-01",
            "status": "COMPLETED",
            "remarks": "Documents received and verified"
        },
        {
            "stage": "Inspection Scheduled",
            "date": "2026-02-10",
            "status": "PENDING",
            "remarks": "Awaiting site inspection"
        },
        {
            "stage": "Approval",
            "date": null,
            "status": "PENDING",
            "remarks": "Post-inspection approval pending"
        },
        {
            "stage": "Installation",
            "date": null,
            "status": "PENDING",
            "remarks": "Meter installation and connection"
        }
    ]
}
"""

"""
POST /api/v1/water/new-connection/{service_request_id}/schedule-inspection
Reschedule inspection appointment

Request:
{
    "preferred_date": "2026-02-15",
    "preferred_time_slot": "02:00 PM - 04:00 PM"
}

Response (200 OK):
{
    "success": true,
    "new_inspection_date": "2026-02-15",
    "new_inspection_time": "02:00 PM - 04:00 PM",
    "message": "Inspection rescheduled successfully"
}
"""


# ============================================================================
# 5. METER CHANGE ENDPOINTS
# ============================================================================

"""
POST /api/v1/water/meter-change
Request meter replacement or upgrade

Request:
{
    "consumer_number": "WTR123456789",
    "old_meter_number": "MTR_WTR_0001",
    "reason_code": "DAMAGED",
    "reason_description": "Meter face damaged, readings not visible",
    "proposed_installation_date": "2026-02-10"
}

Response (201 Created):
{
    "success": true,
    "service_request_id": "uuid",
    "status": "SUBMITTED",
    "message": "Meter change request submitted",
    "reference_number": "WATER_MTR_20260201_001",
    "consumer_number": "WTR123456789",
    "old_meter_number": "MTR_WTR_0001",
    "reason": "DAMAGED",
    "next_steps": [
        "Request acknowledgment and review (1 day)",
        "Department inspection of existing meter (2-3 days)",
        "Installation scheduling (1 day)",
        "Meter replacement and verification (2 hours)"
    ],
    "estimated_completion": "2026-02-10"
}

Error Response (400):
{
    "success": false,
    "error_code": "METER_NOT_FOUND",
    "error_message": "Meter not found for this consumer account"
}

Error Response (400):
{
    "success": false,
    "error_code": "METER_LOCKED",
    "error_message": "Meter has pending disputes or non-payment issues"
}
"""

"""
GET /api/v1/water/meter-change/{service_request_id}/status
Get status of meter change request

Response (200 OK):
{
    "success": true,
    "service_request_id": "uuid",
    "reference_number": "WATER_MTR_20260201_001",
    "status": "IN_PROGRESS",
    "current_stage": "Installation Scheduled",
    "old_meter_number": "MTR_WTR_0001",
    "new_meter_number": "MTR_WTR_0002",
    "installation_date": "2026-02-10",
    "installation_time": "10:00 AM",
    "technician_name": "Amit Singh",
    "technician_contact": "+91-9123456789",
    "timeline": [
        {
            "stage": "Request Submitted",
            "date": "2026-02-01",
            "status": "COMPLETED"
        },
        {
            "stage": "Meter Inspection",
            "date": "2026-02-05",
            "status": "COMPLETED",
            "remarks": "Meter damage confirmed, replacement approved"
        },
        {
            "stage": "New Meter Procured",
            "date": "2026-02-07",
            "status": "COMPLETED"
        },
        {
            "stage": "Installation Scheduled",
            "date": "2026-02-10",
            "status": "PENDING",
            "remarks": "Awaiting installation appointment"
        }
    ]
}
"""


# ============================================================================
# 6. LEAK COMPLAINT ENDPOINTS
# ============================================================================

"""
POST /api/v1/water/report-leak
Report water leak or pipeline damage

Request:
{
    "consumer_number": "WTR123456789",
    "location_description": "Main Street, Near Traffic Signal, beside green shop",
    "landmark_reference": "Traffic signal intersection, green shop",
    "leak_type": "MAJOR",
    "severity_level": "HIGH",
    "water_loss_estimate": "10 liters per minute",
    "affected_area_residents": 5,
    "photo_refs": ["PHOTO_REF_001", "PHOTO_REF_002"],
    "location_coordinates": {
        "latitude": 19.0760,
        "longitude": 72.8777
    }
}

Response (201 Created):
{
    "success": true,
    "service_request_id": "uuid",
    "complaint_number": "LEAK_2026_00123",
    "location": "Main Street, Near Traffic Signal",
    "leak_type": "MAJOR",
    "severity": "HIGH",
    "reported_at": "2026-02-01T08:30:00Z",
    "status": "PENDING",
    "field_team_assigned": "Team_Water_001",
    "field_team_arrival_estimate": "2026-02-01T10:15:00Z",
    "message": "Leak complaint registered successfully. Emergency response team dispatched.",
    "tracking_link": "/api/v1/water/leak/{complaint_number}/track",
    "sms_notification": "Leak complaint #LEAK_2026_00123 registered. Team arriving by 10:15 AM"
}
"""

"""
GET /api/v1/water/leak/{complaint_number}/status
Get status of leak complaint

Response (200 OK):
{
    "success": true,
    "complaint_number": "LEAK_2026_00123",
    "service_request_id": "uuid",
    "location": "Main Street, Near Traffic Signal",
    "leak_type": "MAJOR",
    "severity": "HIGH",
    "reported_at": "2026-02-01T08:30:00Z",
    "status": "DELIVERED",
    "status_timeline": [
        {
            "status": "SUBMITTED",
            "timestamp": "2026-02-01T08:30:00Z",
            "message": "Complaint registered"
        },
        {
            "status": "ACKNOWLEDGED",
            "timestamp": "2026-02-01T08:35:00Z",
            "message": "Team assigned: Team_Water_001"
        },
        {
            "status": "PENDING",
            "timestamp": "2026-02-01T08:40:00Z",
            "message": "Field team en-route"
        },
        {
            "status": "IN_PROGRESS",
            "timestamp": "2026-02-01T10:20:00Z",
            "message": "Team at location, investigating"
        },
        {
            "status": "DELIVERED",
            "timestamp": "2026-02-01T14:45:00Z",
            "message": "Repair completed"
        }
    ],
    "field_team": {
        "team_id": "Team_Water_001",
        "leader_name": "Rajesh Kumar",
        "contact": "+91-9876543210",
        "arrival_time": "2026-02-01T10:15:00Z",
        "arrival_actual": "2026-02-01T10:18:00Z"
    },
    "repair_details": {
        "repair_started": "2026-02-01T10:20:00Z",
        "repair_completed": "2026-02-01T14:45:00Z",
        "repair_description": "Replaced burst main pipe section, 50 meters",
        "water_wasted_estimate": "5000 liters",
        "consumer_credit": "₹250",
        "pressure_test": "PASSED"
    },
    "map_link": "/map?lat=19.0760&lng=72.8777"
}
"""

"""
GET /api/v1/water/leak/{complaint_number}/track
Real-time tracking of leak repair team

Response (200 OK):
{
    "success": true,
    "complaint_number": "LEAK_2026_00123",
    "team": "Team_Water_001",
    "team_status": "IN_PROGRESS",
    "current_location": {
        "latitude": 19.0760,
        "longitude": 72.8777,
        "address": "Main Street, Near Traffic Signal"
    },
    "location_last_update": "2026-02-01T14:42:00Z",
    "estimated_time_to_completion": "5 minutes",
    "team_contact": "+91-9876543210"
}
"""


# ============================================================================
# 7. METER READING SUBMISSION ENDPOINTS
# ============================================================================

"""
POST /api/v1/water/meter-reading/submit
Submit water meter reading

Request:
{
    "consumer_number": "WTR123456789",
    "meter_number": "MTR_WTR_0001",
    "billing_period": "2026-02",
    "meter_reading": 45360,
    "reading_date": "2026-02-01",
    "reading_time": "09:30",
    "photo_ref": "PHOTO_REF_001"
}

Response (201 Created):
{
    "success": true,
    "service_request_id": "uuid",
    "status": "DELIVERED",
    "consumer_number": "WTR123456789",
    "meter_number": "MTR_WTR_0001",
    "billing_period": "2026-01",
    "meter_reading_submitted": 45360,
    "previous_reading": 45230,
    "consumption_units": 130,
    "rate_per_unit": "12.00",
    "fixed_charges": 50.00,
    "calculated_bill": 1810.00,
    "bill_number": "WATER_BILL_2026_00001",
    "bill_generated_date": "2026-02-01",
    "due_date": "2026-02-15",
    "message": "Reading accepted. Bill generated successfully."
}

Error Response (400):
{
    "success": false,
    "error_code": "READING_BELOW_PREVIOUS",
    "error_message": "Submitted reading (45000) is below previous reading (45230)"
}

Error Response (400):
{
    "success": false,
    "error_code": "PHOTO_UNCLEAR",
    "error_message": "Meter photo is not clear. Please submit clear photo of meter dial"
}
"""

"""
GET /api/v1/water/meter-reading/history/{consumer_id}
Get meter reading history

Response (200 OK):
{
    "success": true,
    "consumer_number": "WTR123456789",
    "meter_number": "MTR_WTR_0001",
    "readings": [
        {
            "reading_id": "uuid",
            "meter_reading": 45360,
            "reading_date": "2026-02-01",
            "reading_submitted_by": "CONSUMER",
            "billing_period": "2026-02",
            "consumption_units": 130,
            "status": "VERIFIED"
        },
        {
            "reading_id": "uuid",
            "meter_reading": 45230,
            "reading_date": "2026-01-01",
            "reading_submitted_by": "CONSUMER",
            "billing_period": "2026-01",
            "consumption_units": 120,
            "status": "VERIFIED"
        }
    ]
}
"""


# ============================================================================
# 8. COMPLAINT & GRIEVANCE ENDPOINTS
# ============================================================================

"""
POST /api/v1/water/complaint
Submit water complaint or grievance

Request:
{
    "consumer_number": "WTR123456789",
    "complaint_category": "WATER_QUALITY",
    "complaint_subject": "Brown/dirty water from tap",
    "complaint_description": "Water coming from tap is brown colored and has sediment",
    "severity_level": "HIGH",
    "evidence_refs": ["PHOTO_REF_001", "PHOTO_REF_002"],
    "preferred_contact": "WhatsApp",
    "preferred_language": "EN"
}

Response (201 Created):
{
    "success": true,
    "service_request_id": "uuid",
    "complaint_number": "COMP_2026_00456",
    "consumer_number": "WTR123456789",
    "complaint_category": "WATER_QUALITY",
    "complaint_subject": "Brown/dirty water from tap",
    "registered_at": "2026-02-01T09:00:00Z",
    "status": "ACKNOWLEDGED",
    "message": "Complaint registered successfully",
    "assigned_officer": "Priya Sharma",
    "officer_contact": "+91-9123456789",
    "expected_resolution_date": "2026-02-05",
    "tracking_link": "/api/v1/water/complaint/{complaint_number}/status"
}
"""

"""
GET /api/v1/water/complaint/{complaint_number}/status
Get complaint status

Response (200 OK):
{
    "success": true,
    "complaint_number": "COMP_2026_00456",
    "consumer_number": "WTR123456789",
    "complaint_category": "WATER_QUALITY",
    "complaint_subject": "Brown/dirty water from tap",
    "complaint_description": "Water coming from tap is brown colored and has sediment",
    "registered_at": "2026-02-01T09:00:00Z",
    "status": "DELIVERED",
    "assigned_officer": "Priya Sharma",
    "officer_contact": "+91-9123456789",
    "investigation_started": "2026-02-01T10:00:00Z",
    "investigation_findings": "Main pipeline cleaning required in sector 5",
    "resolution_action": "Pipeline flushing scheduled for 2026-02-05",
    "expected_resolution_date": "2026-02-05",
    "actual_resolution_date": "2026-02-05T16:30:00Z",
    "resolution_description": "Pipeline cleaned, water quality tested - PASSED",
    "resolution_rating": {
        "rating_requested": true,
        "rating": 5,
        "feedback": "Issue resolved quickly and professionally"
    },
    "timeline": [
        {
            "date": "2026-02-01 09:00",
            "status": "REGISTERED",
            "message": "Complaint received and registered"
        },
        {
            "date": "2026-02-01 10:00",
            "status": "ASSIGNED",
            "message": "Assigned to officer Priya Sharma"
        },
        {
            "date": "2026-02-03 14:00",
            "status": "INVESTIGATION",
            "message": "Investigation completed, findings submitted"
        },
        {
            "date": "2026-02-05 16:30",
            "status": "RESOLVED",
            "message": "Pipeline cleaning completed, quality verified"
        }
    ]
}
"""


# ============================================================================
# 9. SERVICE REQUEST STATUS ENDPOINTS
# ============================================================================

"""
GET /api/v1/water/requests/{service_request_id}
Get generic service request details

Response (200 OK):
{
    "success": true,
    "service_request_id": "uuid",
    "service_type": "WATER_PAY_BILL",
    "initiator_id": "CUST_001",
    "beneficiary_id": "CUST_001",
    "status": "DELIVERED",
    "created_at": "2026-02-01T10:00:00Z",
    "updated_at": "2026-02-01T10:30:00Z",
    "current_owner": "SYSTEM",
    "correlation_id": "WATER_PAY_BILL_abc123",
    "error_code": null,
    "error_message": null
}
"""

"""
GET /api/v1/water/requests
List all service requests for logged-in user

Response (200 OK):
{
    "success": true,
    "total_requests": 5,
    "requests": [
        {
            "service_request_id": "uuid",
            "service_type": "WATER_PAY_BILL",
            "status": "DELIVERED",
            "created_at": "2026-02-01T10:00:00Z",
            "description": "Bill payment for Jan 2026"
        },
        {
            "service_request_id": "uuid",
            "service_type": "WATER_CONNECTION_REQUEST",
            "status": "PENDING",
            "created_at": "2026-01-20T14:00:00Z",
            "description": "New connection request at Main Street"
        }
    ]
}
"""


# ============================================================================
# 10. ERROR RESPONSES
# ============================================================================

"""
Standard Error Response Format:

Error (400 Bad Request):
{
    "success": false,
    "error_code": "INVALID_DATA",
    "error_message": "Validation failed: Phone number format invalid"
}

Error (401 Unauthorized):
{
    "success": false,
    "error_code": "UNAUTHORIZED",
    "error_message": "Authentication required or token expired"
}

Error (404 Not Found):
{
    "success": false,
    "error_code": "NOT_FOUND",
    "error_message": "Service request not found"
}

Error (500 Internal Server Error):
{
    "success": false,
    "error_code": "INTERNAL_ERROR",
    "error_message": "An unexpected error occurred. Please try again later."
}
"""


# ============================================================================
# 11. COMMON ERROR CODES
# ============================================================================

"""
INVALID_DATA - Request validation failed
UNAUTHORIZED - User not authenticated or invalid token
ACCOUNT_INACTIVE - Consumer account is suspended/closed
BILL_NOT_FOUND - No bill found for given period
PAYMENT_FAILED - Payment gateway returned error
CONSUMER_NOT_FOUND - Consumer account doesn't exist
OUT_OF_SERVICE_AREA - Location not in service area
EXISTING_CONNECTION - Connection already exists
DOCUMENT_INVALID - Uploaded documents are invalid
METER_NOT_FOUND - Meter doesn't exist in system
METER_LOCKED - Meter has pending disputes
READING_INVALID - Meter reading validation failed
READING_BELOW_PREVIOUS - Reading less than previous month
INSUFFICIENT_AMOUNT - Payment below minimum
DUPLICATE_PAYMENT - Duplicate payment detected
DEPARTMENT_TIMEOUT - Department system not responding
INTEGRATION_FAILURE - External system error
INTERNAL_ERROR - Server-side error
"""
