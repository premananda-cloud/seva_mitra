"""
SUVIDHA 2026 - Electricity Services REST API Documentation
===========================================================
Complete API endpoints for Electricity Service KIOSK

Base URL: /api/v1/electricity
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
        "customer_id": "123456789012",
        "name": "Raj Kumar",
        "phone": "+919876543210"
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
# 2. BILL PAYMENT ENDPOINTS
# ============================================================================

"""
POST /api/v1/electricity/pay-bill
Create and submit a bill payment request

Request:
{
    "meter_number": "ELEC123456",
    "billing_period": "2026-01",
    "amount": "1500.00",
    "payment_method": "UPI"  # CARD, UPI, NET_BANKING
}

Headers:
Authorization: Bearer {jwt_token}

Response (200 OK):
{
    "success": true,
    "service_request_id": "550e8400-e29b-41d4-a716-446655440000",
    "status": "DELIVERED",
    "receipt": {
        "receipt_id": "REC_550e8400",
        "meter_number": "ELEC123456",
        "amount_paid": "1500.00",
        "payment_date": "2026-03-01T10:30:00Z",
        "payment_reference": "RZP_PAY_123456789",
        "status": "COMPLETED"
    }
}

Error (400 Bad Request):
{
    "success": false,
    "service_request_id": "550e8400-e29b-41d4-a716-446655440000",
    "error_code": "PAYMENT_FAILED",
    "error_message": "Payment declined by gateway",
    "status": "FAILED"
}

Error (404 Not Found):
{
    "success": false,
    "error_code": "BILL_NOT_FOUND",
    "error_message": "No outstanding bill found for the specified period"
}
"""

"""
GET /api/v1/electricity/meters/{meter_number}/bill-summary
Get outstanding bills for a meter

Response (200 OK):
{
    "success": true,
    "meter_number": "ELEC123456",
    "customer_id": "123456789012",
    "bills": [
        {
            "bill_id": "BL_550e8400",
            "bill_number": "ELEC123456/2026-01",
            "billing_period": "2026-01",
            "bill_amount": 1500.00,
            "amount_paid": 0.00,
            "outstanding_amount": 1500.00,
            "bill_date": "2026-01-05",
            "due_date": "2026-01-20",
            "status": "OVERDUE",
            "days_overdue": 40
        },
        {
            "bill_id": "BL_660e8401",
            "bill_number": "ELEC123456/2026-02",
            "billing_period": "2026-02",
            "bill_amount": 1750.00,
            "amount_paid": 0.00,
            "outstanding_amount": 1750.00,
            "bill_date": "2026-02-05",
            "due_date": "2026-02-20",
            "status": "PENDING",
            "days_overdue": 0
        }
    ],
    "total_outstanding": 3250.00
}
"""

"""
GET /api/v1/electricity/meters/{meter_number}/payment-history
Get payment history for a meter

Query Parameters:
- limit: 10 (default)
- offset: 0 (default)
- from_date: 2026-01-01 (optional)
- to_date: 2026-03-01 (optional)

Response (200 OK):
{
    "success": true,
    "meter_number": "ELEC123456",
    "total_payments": 12,
    "total_amount_paid": 18000.00,
    "payments": [
        {
            "payment_id": "PAY_550e8400",
            "bill_number": "ELEC123456/2026-02",
            "amount_paid": 1750.00,
            "payment_date": "2026-02-15T14:30:00Z",
            "payment_method": "UPI",
            "payment_status": "SUCCESS",
            "gateway_name": "RazorPay",
            "gateway_reference": "RZP_PAY_123456789"
        }
    ]
}
"""

"""
GET /api/v1/electricity/requests/{service_request_id}/status
Get payment request status

Response (200 OK):
{
    "success": true,
    "service_request_id": "550e8400-e29b-41d4-a716-446655440000",
    "service_type": "ELECTRICITY_PAY_BILL",
    "status": "DELIVERED",
    "created_at": "2026-03-01T10:15:00Z",
    "updated_at": "2026-03-01T10:30:00Z",
    "status_history": [
        {
            "status": "DRAFT",
            "timestamp": "2026-03-01T10:15:00Z",
            "reason": "Service request created"
        },
        {
            "status": "SUBMITTED",
            "timestamp": "2026-03-01T10:20:00Z",
            "reason": "Payment request submitted by user"
        },
        {
            "status": "IN_PROGRESS",
            "timestamp": "2026-03-01T10:25:00Z",
            "reason": "Processing payment with gateway"
        },
        {
            "status": "DELIVERED",
            "timestamp": "2026-03-01T10:30:00Z",
            "reason": "Payment processed successfully"
        }
    ]
}
"""


# ============================================================================
# 3. SERVICE TRANSFER ENDPOINTS
# ============================================================================

"""
POST /api/v1/electricity/transfer-service
Create a service transfer request

Request:
{
    "meter_number": "ELEC123456",
    "new_customer_id": "987654321098",
    "new_customer_name": "Priya Singh",
    "identity_proof": "ID_DOC_REF_001",
    "ownership_proof": "OWN_DOC_REF_001",
    "consent_document": "CONS_DOC_REF_001",
    "effective_date": "2026-04-01"
}

Headers:
Authorization: Bearer {jwt_token}

Response (201 Created):
{
    "success": true,
    "service_request_id": "660e8401-f39c-42e5-b827-557766551111",
    "status": "SUBMITTED",
    "message": "Transfer request submitted. Awaiting department approval.",
    "reference_number": "TRF_660e8401",
    "expected_processing_time": "5-7 business days"
}

Error (409 Conflict):
{
    "success": false,
    "error_code": "PENDING_TRANSFER_EXISTS",
    "error_message": "A transfer request already exists for this meter"
}
"""

"""
GET /api/v1/electricity/transfers/{service_request_id}
Get transfer request details and status

Response (200 OK):
{
    "success": true,
    "transfer": {
        "service_request_id": "660e8401-f39c-42e5-b827-557766551111",
        "meter_number": "ELEC123456",
        "old_customer": {
            "customer_id": "123456789012",
            "name": "Raj Kumar"
        },
        "new_customer": {
            "customer_id": "987654321098",
            "name": "Priya Singh"
        },
        "status": "PENDING",
        "effective_date": "2026-04-01",
        "created_at": "2026-03-01T10:00:00Z",
        "status_history": [
            {
                "status": "SUBMITTED",
                "timestamp": "2026-03-01T10:00:00Z",
                "reason": "Transfer request submitted"
            },
            {
                "status": "ACKNOWLEDGED",
                "timestamp": "2026-03-01T11:30:00Z",
                "reason": "Transfer request acknowledged by department"
            }
        ]
    }
}
"""

"""
POST /api/v1/electricity/transfers/{service_request_id}/cancel
Cancel a transfer request (only if not yet approved)

Request:
{
    "reason": "Changed my mind"
}

Response (200 OK):
{
    "success": true,
    "service_request_id": "660e8401-f39c-42e5-b827-557766551111",
    "status": "CANCELLED",
    "message": "Transfer request cancelled"
}

Error (409 Conflict):
{
    "success": false,
    "error_code": "CONFLICT",
    "error_message": "Cannot cancel request in APPROVED status"
}
"""


# ============================================================================
# 4. COMPLAINT ENDPOINTS
# ============================================================================

"""
POST /api/v1/electricity/complaints
Register a new complaint

Request:
{
    "meter_number": "ELEC123456",
    "complaint_category": "BILLING",  # BILLING, SERVICE, METER, CONNECTION, OTHER
    "complaint_description": "Bill amount seems incorrect",
    "complaint_priority": "NORMAL",  # LOW, NORMAL, HIGH, URGENT
    "attachments": ["photo_ref_001", "document_ref_001"]
}

Headers:
Authorization: Bearer {jwt_token}

Response (201 Created):
{
    "success": true,
    "service_request_id": "770e8402-g49d-53f6-c938-668877662222",
    "complaint_id": "COMP_770e8402",
    "status": "OPEN",
    "message": "Complaint registered successfully",
    "tracking_number": "COMP_770e8402",
    "expected_resolution_time": "5 business days"
}
"""

"""
GET /api/v1/electricity/complaints/{complaint_id}
Get complaint details and status

Response (200 OK):
{
    "success": true,
    "complaint": {
        "complaint_id": "COMP_770e8402",
        "service_request_id": "770e8402-g49d-53f6-c938-668877662222",
        "meter_number": "ELEC123456",
        "category": "BILLING",
        "description": "Bill amount seems incorrect",
        "priority": "NORMAL",
        "status": "IN_PROGRESS",
        "assigned_to": "Officer_001",
        "created_at": "2026-03-01T10:00:00Z",
        "updated_at": "2026-03-02T09:00:00Z",
        "resolution_notes": "Under investigation. Bill will be verified.",
        "customer_satisfaction_rating": null
    }
}
"""

"""
GET /api/v1/electricity/complaints?status=OPEN&limit=10
List all complaints for current user

Query Parameters:
- status: OPEN, ACKNOWLEDGED, IN_PROGRESS, RESOLVED, CLOSED
- priority: LOW, NORMAL, HIGH, URGENT
- limit: 10
- offset: 0

Response (200 OK):
{
    "success": true,
    "total_complaints": 3,
    "complaints": [
        {
            "complaint_id": "COMP_770e8402",
            "category": "BILLING",
            "description": "Bill amount seems incorrect",
            "status": "IN_PROGRESS",
            "created_at": "2026-03-01T10:00:00Z",
            "updated_at": "2026-03-02T09:00:00Z"
        }
    ]
}
"""

"""
POST /api/v1/electricity/complaints/{complaint_id}/resolution-rating
Rate complaint resolution

Request:
{
    "satisfaction_rating": 5,  # 1-5
    "feedback": "Issue was resolved satisfactorily"
}

Response (200 OK):
{
    "success": true,
    "message": "Thank you for your feedback"
}
"""


# ============================================================================
# 5. METER READING SUBMISSION
# ============================================================================

"""
POST /api/v1/electricity/meter-readings
Submit meter reading

Request:
{
    "meter_number": "ELEC123456",
    "reading_value": 45678.50,
    "reading_date": "2026-03-01",
    "reading_type": "MANUAL",  # MANUAL, AUTOMATIC, ESTIMATED
    "photo_proof": "PHOTO_REF_001"
}

Headers:
Authorization: Bearer {jwt_token}

Response (201 Created):
{
    "success": true,
    "service_request_id": "880e8403-h59e-64g7-d049-779988773333",
    "reading_id": "READ_880e8403",
    "status": "SUBMITTED",
    "message": "Meter reading submitted successfully"
}
"""

"""
GET /api/v1/electricity/meters/{meter_number}/reading-history
Get meter reading history

Query Parameters:
- limit: 12 (default)
- offset: 0

Response (200 OK):
{
    "success": true,
    "meter_number": "ELEC123456",
    "readings": [
        {
            "reading_id": "READ_880e8403",
            "reading_value": 45678.50,
            "reading_date": "2026-03-01",
            "reading_type": "MANUAL",
            "consumption_units": 125.50,
            "submitted_at": "2026-03-01T14:30:00Z"
        }
    ]
}
"""


# ============================================================================
# 6. NEW CONNECTION REQUEST
# ============================================================================

"""
POST /api/v1/electricity/connection-request
Request new electricity connection

Request:
{
    "address": "789 New Street, City",
    "load_requirement": 5.0,  # in kW
    "connection_type": "RESIDENTIAL",
    "property_documents": ["PROP_DOC_001", "PROOF_OF_RESIDENCE_001"]
}

Headers:
Authorization: Bearer {jwt_token}

Response (201 Created):
{
    "success": true,
    "service_request_id": "990e8404-i69f-75h8-e150-880099884444",
    "application_number": "CON_990e8404",
    "status": "SUBMITTED",
    "message": "Connection request submitted",
    "expected_processing_time": "10-15 days"
}
"""

"""
GET /api/v1/electricity/connection-requests/{application_number}
Get connection request status

Response (200 OK):
{
    "success": true,
    "application": {
        "application_number": "CON_990e8404",
        "service_request_id": "990e8404-i69f-75h8-e150-880099884444",
        "address": "789 New Street, City",
        "load_requirement": 5.0,
        "status": "PENDING",
        "submitted_at": "2026-03-01T10:00:00Z",
        "approved_at": null,
        "activation_date": null,
        "assigned_meter_number": null,
        "message": "Application under review. Site inspection scheduled."
    }
}
"""


# ============================================================================
# 7. ACCOUNT INFORMATION
# ============================================================================

"""
GET /api/v1/electricity/account
Get customer account information

Response (200 OK):
{
    "success": true,
    "customer": {
        "customer_id": "123456789012",
        "name": "Raj Kumar",
        "phone": "+919876543210",
        "email": "raj@example.com",
        "address": "123 Main St",
        "customer_type": "RESIDENTIAL",
        "account_status": "ACTIVE",
        "account_age_days": 1825
    },
    "meters": [
        {
            "meter_id": "MTR_550e8400",
            "meter_number": "ELEC123456",
            "meter_type": "SINGLE_PHASE",
            "sanctioned_load": 5.00,
            "status": "ACTIVE",
            "installation_date": "2022-01-15"
        }
    ]
}
"""

"""
PUT /api/v1/electricity/account
Update account information

Request:
{
    "phone": "+919876543211",
    "email": "newemail@example.com",
    "address": "123 New Street"
}

Response (200 OK):
{
    "success": true,
    "message": "Account information updated successfully"
}
"""


# ============================================================================
# 8. ADMIN ENDPOINTS
# ============================================================================

"""
GET /api/v1/electricity/admin/dashboard
Get admin dashboard metrics

Headers:
Authorization: Bearer {admin_jwt_token}

Query Parameters:
- from_date: 2026-01-01
- to_date: 2026-03-01
- meter_number: ELEC123456 (optional)

Response (200 OK):
{
    "success": true,
    "period": {
        "from_date": "2026-01-01",
        "to_date": "2026-03-01"
    },
    "metrics": {
        "total_bills_generated": 1500,
        "total_payments_received": 1450000.00,
        "successful_payments": 1420,
        "failed_payments": 30,
        "average_payment_value": 1020.50,
        "total_complaints": 45,
        "complaints_resolved": 38,
        "complaints_pending": 7,
        "service_transfers_requested": 8,
        "service_transfers_completed": 6,
        "new_connections": 12,
        "system_uptime": 99.8
    }
}
"""

"""
GET /api/v1/electricity/admin/service-requests
List pending service requests (admin view)

Query Parameters:
- status: SUBMITTED, PENDING, ACKNOWLEDGED, IN_PROGRESS
- service_type: ELECTRICITY_PAY_BILL, ELECTRICITY_SERVICE_TRANSFER, etc.
- limit: 20
- offset: 0

Response (200 OK):
{
    "success": true,
    "total": 25,
    "requests": [
        {
            "service_request_id": "660e8401-f39c-42e5-b827-557766551111",
            "service_type": "ELECTRICITY_SERVICE_TRANSFER",
            "initiator_id": "123456789012",
            "beneficiary_id": "987654321098",
            "status": "ACKNOWLEDGED",
            "created_at": "2026-03-01T10:00:00Z",
            "updated_at": "2026-03-01T11:30:00Z",
            "correlation_id": "TRF_660e8401"
        }
    ]
}
"""

"""
POST /api/v1/electricity/admin/service-requests/{service_request_id}/approve
Approve a service request

Request:
{
    "approved_by": "Officer_001",
    "comments": "All documents verified and approved"
}

Response (200 OK):
{
    "success": true,
    "service_request_id": "660e8401-f39c-42e5-b827-557766551111",
    "status": "APPROVED",
    "message": "Request approved successfully"
}
"""

"""
POST /api/v1/electricity/admin/service-requests/{service_request_id}/deny
Deny a service request

Request:
{
    "reason": "Incomplete documentation provided",
    "suggested_action": "Please resubmit with complete property documents"
}

Response (200 OK):
{
    "success": true,
    "service_request_id": "660e8401-f39c-42e5-b827-557766551111",
    "status": "DENIED",
    "message": "Request denied"
}
"""


# ============================================================================
# 9. ERROR CODES REFERENCE
# ============================================================================

"""
ERROR CODES:

USER ERRORS (4xx):
- INVALID_DATA: 400 - Invalid input data
- UNAUTHORIZED: 401 - User not authenticated
- CONFLICT: 409 - Request conflicts with existing data

METER ERRORS:
- METER_NOT_FOUND: 404 - Meter does not exist
- METER_INACTIVE: 400 - Meter is not active
- METER_NOT_OWNED_BY_USER: 403 - User does not own this meter

BILL ERRORS:
- BILL_NOT_FOUND: 404 - Bill not found
- INSUFFICIENT_AMOUNT: 400 - Payment amount is less than due
- PAYMENT_FAILED: 400 - Payment gateway declined transaction

TRANSFER ERRORS:
- PENDING_TRANSFER_EXISTS: 409 - Transfer already pending
- TRANSFER_AUTHORIZATION_FAILED: 400 - Authorization failed

SYSTEM ERRORS (5xx):
- DEPARTMENT_TIMEOUT: 504 - Department system timeout
- INTEGRATION_FAILURE: 502 - External integration failed
- INTERNAL_ERROR: 500 - Internal server error
"""


# ============================================================================
# 10. RESPONSE FORMAT STANDARDS
# ============================================================================

"""
SUCCESS RESPONSE:
{
    "success": true,
    "service_request_id": "550e8400-e29b-41d4-a716-446655440000",
    "data": { ... },
    "message": "Operation successful",
    "timestamp": "2026-03-01T10:30:00Z"
}

ERROR RESPONSE:
{
    "success": false,
    "error_code": "INVALID_DATA",
    "error_message": "Detailed error description",
    "service_request_id": "550e8400-e29b-41d4-a716-446655440000",
    "details": { ... },
    "timestamp": "2026-03-01T10:30:00Z"
}

PAGINATED RESPONSE:
{
    "success": true,
    "data": [ ... ],
    "pagination": {
        "total": 100,
        "limit": 10,
        "offset": 0,
        "has_next": true,
        "has_previous": false
    },
    "timestamp": "2026-03-01T10:30:00Z"
}
"""

