"""
SUVIDHA 2026 - Water Services Database Schema
=============================================
PostgreSQL Schema for Water Services Module
Complete tables for water utility management
"""

# ============================================================================
# SERVICE REQUEST TABLES (Core/Shared - same across all utilities)
# ============================================================================

CREATE TABLE service_requests (
    service_request_id UUID PRIMARY KEY,
    service_type VARCHAR(50) NOT NULL,
    initiator_id VARCHAR(50) NOT NULL,
    beneficiary_id VARCHAR(50) NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'DRAFT',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    current_owner VARCHAR(50) NOT NULL,
    correlation_id VARCHAR(100) UNIQUE,
    error_code VARCHAR(50),
    error_message TEXT,
    payload JSONB NOT NULL DEFAULT '{}',
    created_by VARCHAR(50),
    created_ip VARCHAR(45),
    
    INDEX idx_service_request_initiator (initiator_id),
    INDEX idx_service_request_status (status),
    INDEX idx_service_request_created (created_at),
    INDEX idx_service_request_type (service_type),
    INDEX idx_service_request_correlation (correlation_id)
);

CREATE TABLE service_request_history (
    history_id UUID PRIMARY KEY,
    service_request_id UUID NOT NULL REFERENCES service_requests(service_request_id),
    old_status VARCHAR(50),
    new_status VARCHAR(50) NOT NULL,
    transition_timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    reason TEXT NOT NULL,
    metadata JSONB DEFAULT '{}',
    changed_by VARCHAR(50),
    
    FOREIGN KEY (service_request_id) REFERENCES service_requests(service_request_id)
        ON DELETE CASCADE,
    INDEX idx_history_request (service_request_id),
    INDEX idx_history_timestamp (transition_timestamp)
);


# ============================================================================
# WATER-SPECIFIC TABLES
# ============================================================================

# Water Consumer/Account Master
CREATE TABLE water_consumers (
    consumer_id VARCHAR(50) PRIMARY KEY,
    consumer_number VARCHAR(50) NOT NULL UNIQUE,  -- Service connection number
    aadhar_number VARCHAR(255) NOT NULL ENCRYPTED,  -- Encrypted for privacy
    name VARCHAR(255) NOT NULL,
    phone VARCHAR(20) NOT NULL ENCRYPTED,
    email VARCHAR(255) ENCRYPTED,
    address TEXT NOT NULL,
    property_pin_code VARCHAR(10),
    connection_type VARCHAR(50) NOT NULL,  -- DOMESTIC, COMMERCIAL, INDUSTRIAL
    customer_type VARCHAR(50),  -- INDIVIDUAL, ORGANIZATION, GOVERNMENT
    address_proof_id VARCHAR(100),
    created_date DATE NOT NULL,
    activation_date DATE,
    status VARCHAR(50) DEFAULT 'ACTIVE',  -- ACTIVE, INACTIVE, SUSPENDED, DISCONNECTED, CLOSED
    payment_status VARCHAR(50) DEFAULT 'CURRENT',  -- CURRENT, OVERDUE, DEFAULTED
    last_payment_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE (aadhar_number),
    INDEX idx_consumer_phone (phone),
    INDEX idx_consumer_name (name),
    INDEX idx_consumer_status (status),
    INDEX idx_consumer_created (created_date)
);

# Water Meter Master
CREATE TABLE water_meters (
    meter_id UUID PRIMARY KEY,
    meter_number VARCHAR(50) NOT NULL UNIQUE,
    consumer_id VARCHAR(50) NOT NULL REFERENCES water_consumers(consumer_id),
    meter_type VARCHAR(50),  -- MECHANICAL, DIGITAL, SMART
    meter_brand VARCHAR(100),
    meter_model VARCHAR(100),
    manufacture_date DATE,
    installation_date DATE NOT NULL,
    meter_status VARCHAR(50) DEFAULT 'ACTIVE',  -- ACTIVE, INACTIVE, DAMAGED, FAULTY, REPLACED
    sanctioned_load INTEGER,  -- in liters/day
    location_coordinates GEOGRAPHY,  -- For GPS mapping
    meter_reading_type VARCHAR(50),  -- MANUAL, AUTOMATIC, SMART
    last_reading_value INTEGER,
    last_reading_date DATE,
    last_meter_verification_date DATE,
    verification_status VARCHAR(50),  -- VERIFIED, PENDING, FAILED
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_meter_consumer (consumer_id),
    INDEX idx_meter_status (meter_status),
    INDEX idx_meter_number (meter_number),
    INDEX idx_meter_type (meter_type)
);

# Water Bills/Invoices
CREATE TABLE water_bills (
    bill_id UUID PRIMARY KEY,
    bill_number VARCHAR(100) NOT NULL UNIQUE,
    meter_id UUID NOT NULL REFERENCES water_meters(meter_id),
    consumer_id VARCHAR(50) NOT NULL REFERENCES water_consumers(consumer_id),
    billing_period VARCHAR(10) NOT NULL,  -- YYYY-MM format
    billing_month_start_date DATE NOT NULL,
    billing_month_end_date DATE NOT NULL,
    opening_reading INTEGER,  -- Previous month closing
    closing_reading INTEGER,  -- Current month closing
    consumption_units INTEGER NOT NULL,  -- units consumed
    rate_per_unit DECIMAL(10, 4) NOT NULL,  -- in INR per unit
    fixed_charges DECIMAL(10, 2),
    sewer_charges DECIMAL(10, 2),
    water_tax DECIMAL(10, 2),
    variable_charges DECIMAL(10, 2),
    tax_amount DECIMAL(10, 2),
    total_bill_amount DECIMAL(12, 2) NOT NULL,
    amount_paid DECIMAL(12, 2) DEFAULT 0,
    outstanding_balance DECIMAL(12, 2),
    due_date DATE NOT NULL,
    payment_status VARCHAR(50) DEFAULT 'PENDING',  -- PENDING, PARTIAL, PAID, OVERDUE, DISPUTE
    issued_date DATE NOT NULL,
    penalty_charges DECIMAL(10, 2) DEFAULT 0,  -- Late payment penalties
    is_provisional BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_bill_consumer (consumer_id),
    INDEX idx_bill_meter (meter_id),
    INDEX idx_bill_period (billing_period),
    INDEX idx_bill_status (payment_status),
    INDEX idx_bill_due_date (due_date),
    INDEX idx_bill_created (issued_date)
);

# Water Bill Payments
CREATE TABLE water_bill_payments (
    payment_id UUID PRIMARY KEY,
    bill_id UUID NOT NULL REFERENCES water_bills(bill_id),
    consumer_id VARCHAR(50) NOT NULL REFERENCES water_consumers(consumer_id),
    payment_amount DECIMAL(12, 2) NOT NULL,
    payment_date DATE NOT NULL,
    payment_time TIME,
    payment_method VARCHAR(50) NOT NULL,  -- UPI, NETBANKING, CARD, CASH, CHEQUE, DD
    transaction_reference VARCHAR(100) UNIQUE,  -- Gateway transaction ID
    payment_gateway VARCHAR(50),  -- CCAVENUE, PAYTM, RAZORPAY, etc.
    receipt_number VARCHAR(100) UNIQUE,
    payment_status VARCHAR(50) DEFAULT 'SUCCESS',  -- SUCCESS, FAILED, PENDING, REVERSAL
    reversal_amount DECIMAL(12, 2),
    reversal_date DATE,
    reversal_reason VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_payment_bill (bill_id),
    INDEX idx_payment_consumer (consumer_id),
    INDEX idx_payment_date (payment_date),
    INDEX idx_payment_method (payment_method),
    INDEX idx_payment_transaction (transaction_reference)
);

# Water Meter Readings
CREATE TABLE water_meter_readings (
    reading_id UUID PRIMARY KEY,
    meter_id UUID NOT NULL REFERENCES water_meters(meter_id),
    consumer_id VARCHAR(50) NOT NULL REFERENCES water_consumers(consumer_id),
    reading_value INTEGER NOT NULL,  -- Meter dial reading
    reading_date DATE NOT NULL,
    reading_time TIME,
    reading_submitted_by VARCHAR(50),  -- 'CONSUMER', 'METER_READER', 'SMART_METER'
    reading_source VARCHAR(50),  -- MANUAL, AUTOMATIC, MOBILE_APP, KIOSK, SMS
    reading_photo_ref VARCHAR(255),  -- Reference to uploaded photo
    reading_photo_url VARCHAR(500),
    verification_status VARCHAR(50) DEFAULT 'PENDING',  -- PENDING, VERIFIED, REJECTED
    remarks TEXT,
    billed BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_reading_meter (meter_id),
    INDEX idx_reading_consumer (consumer_id),
    INDEX idx_reading_date (reading_date),
    INDEX idx_reading_verification (verification_status),
    INDEX idx_reading_billed (billed)
);

# Water Leak Complaints
CREATE TABLE water_leak_complaints (
    complaint_id UUID PRIMARY KEY,
    complaint_number VARCHAR(100) NOT NULL UNIQUE,
    service_request_id UUID REFERENCES service_requests(service_request_id),
    consumer_id VARCHAR(50) REFERENCES water_consumers(consumer_id),  -- Nullable if anonymous report
    location_description TEXT NOT NULL,
    landmark_reference VARCHAR(255),
    location_latitude DECIMAL(10, 8),
    location_longitude DECIMAL(11, 8),
    leak_type VARCHAR(50) NOT NULL,  -- MINOR, MAJOR, WATER_MAIN_BURST, PIPE_SEEPAGE
    severity_level VARCHAR(50) NOT NULL,  -- LOW, MEDIUM, HIGH, CRITICAL
    water_loss_estimate_liters_per_hour INTEGER,
    affected_area_residents INTEGER DEFAULT 0,
    photos_count INTEGER DEFAULT 0,
    first_photo_ref VARCHAR(255),
    report_timestamp TIMESTAMP NOT NULL,
    report_source VARCHAR(50),  -- KIOSK, PHONE, MOBILE_APP, WALK_IN
    field_team_assigned_id VARCHAR(50),
    dispatch_timestamp TIMESTAMP,
    team_arrival_timestamp TIMESTAMP,
    team_arrival_actual TIMESTAMP,
    repair_start_timestamp TIMESTAMP,
    repair_completion_timestamp TIMESTAMP,
    repair_description TEXT,
    estimated_water_wasted_liters INTEGER,
    water_loss_credit_amount DECIMAL(10, 2),
    status VARCHAR(50) DEFAULT 'OPEN',  -- OPEN, ASSIGNED, IN_PROGRESS, RESOLVED, CLOSED
    resolution_date DATE,
    resolution_type VARCHAR(50),  -- REPAIRED, ESCALATED, DUPLICATE, INVALID
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_leak_complaint_number (complaint_number),
    INDEX idx_leak_service_request (service_request_id),
    INDEX idx_leak_consumer (consumer_id),
    INDEX idx_leak_severity (severity_level),
    INDEX idx_leak_status (status),
    INDEX idx_leak_report_date (report_timestamp),
    INDEX idx_leak_location (location_latitude, location_longitude)
);

# Water Connection Requests
CREATE TABLE water_connection_requests (
    request_id UUID PRIMARY KEY,
    service_request_id UUID REFERENCES service_requests(service_request_id),
    applicant_id VARCHAR(50) NOT NULL,
    applicant_name VARCHAR(255) NOT NULL,
    phone_number VARCHAR(20) NOT NULL,
    email VARCHAR(255),
    address TEXT NOT NULL,
    property_pin_code VARCHAR(10),
    connection_type VARCHAR(50) NOT NULL,  -- DOMESTIC, COMMERCIAL, INDUSTRIAL
    purpose VARCHAR(100),  -- Drinking/Domestic, Commercial, Industrial, etc.
    load_requirement INTEGER,  -- liters/day
    property_documents_ref VARCHAR(255),
    proof_of_identity_ref VARCHAR(255),
    inspection_date DATE,
    inspection_officer_id VARCHAR(50),
    inspection_status VARCHAR(50),  -- PENDING, COMPLETED, PASSED, FAILED
    inspection_findings TEXT,
    connection_fee_amount DECIMAL(10, 2),
    connection_fee_paid BOOLEAN DEFAULT FALSE,
    approval_date DATE,
    approved_by VARCHAR(50),
    installation_start_date DATE,
    installation_completion_date DATE,
    meter_number VARCHAR(50),
    consumer_number VARCHAR(50),
    activation_date DATE,
    first_billing_date DATE,
    status VARCHAR(50) DEFAULT 'PENDING',  -- PENDING, APPROVED, ACTIVATED, REJECTED, CANCELLED
    rejection_reason VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_conn_request_service (service_request_id),
    INDEX idx_conn_request_applicant (applicant_id),
    INDEX idx_conn_request_status (status),
    INDEX idx_conn_request_type (connection_type),
    INDEX idx_conn_request_created (created_at)
);

# Water Meter Changes/Replacements
CREATE TABLE water_meter_changes (
    change_id UUID PRIMARY KEY,
    service_request_id UUID REFERENCES service_requests(service_request_id),
    consumer_id VARCHAR(50) NOT NULL REFERENCES water_consumers(consumer_id),
    old_meter_number VARCHAR(50) NOT NULL,
    old_meter_id UUID REFERENCES water_meters(meter_id),
    new_meter_number VARCHAR(50) NOT NULL,
    new_meter_id UUID REFERENCES water_meters(meter_id),
    reason_code VARCHAR(50) NOT NULL,  -- DAMAGED, FAULTY, UPGRADE, CORRECTION, REPAIR
    reason_description TEXT,
    old_meter_final_reading INTEGER,
    new_meter_opening_reading INTEGER,
    inspection_report_ref VARCHAR(255),
    department_order_ref VARCHAR(255),
    requested_date DATE,
    requested_by VARCHAR(50),
    inspection_date DATE,
    inspection_result VARCHAR(50),
    installation_date DATE,
    installation_completed_date DATE,
    meter_condition_certificate VARCHAR(50),  -- PASSED_CALIBRATION, FAILED, PENDING
    warranty_period_months INTEGER,
    status VARCHAR(50) DEFAULT 'PENDING',  -- PENDING, APPROVED, SCHEDULED, COMPLETED, FAILED
    failure_reason VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_meter_change_service_request (service_request_id),
    INDEX idx_meter_change_consumer (consumer_id),
    INDEX idx_meter_change_status (status),
    INDEX idx_meter_change_date (requested_date)
);

# Water Complaints & Grievances
CREATE TABLE water_complaints (
    complaint_id UUID PRIMARY KEY,
    complaint_number VARCHAR(100) NOT NULL UNIQUE,
    service_request_id UUID REFERENCES service_requests(service_request_id),
    consumer_id VARCHAR(50) REFERENCES water_consumers(consumer_id),
    complaint_category VARCHAR(50) NOT NULL,  -- WATER_QUALITY, BILLING_ISSUE, SERVICE_INTERRUPTION, METER_ISSUE, etc.
    complaint_subject VARCHAR(255) NOT NULL,
    complaint_description TEXT NOT NULL,
    severity_level VARCHAR(50),  -- LOW, MEDIUM, HIGH, CRITICAL
    evidence_doc_refs VARCHAR(1000),  -- JSON array of document references
    preferred_contact_method VARCHAR(50),  -- PHONE, EMAIL, WHATSAPP, SMS
    preferred_language VARCHAR(20) DEFAULT 'EN',  -- EN, HI, MR, TA, TE, KN, ML
    assigned_officer_id VARCHAR(50),
    assigned_date DATE,
    investigation_start_date DATE,
    investigation_findings TEXT,
    resolution_action_taken TEXT,
    expected_resolution_date DATE,
    actual_resolution_date DATE,
    resolution_description TEXT,
    consumer_satisfaction_rating INTEGER,  -- 1-5 scale
    status VARCHAR(50) DEFAULT 'OPEN',  -- OPEN, ACKNOWLEDGED, INVESTIGATING, RESOLVED, CLOSED
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_complaint_number (complaint_number),
    INDEX idx_complaint_service_request (service_request_id),
    INDEX idx_complaint_consumer (consumer_id),
    INDEX idx_complaint_category (complaint_category),
    INDEX idx_complaint_status (status),
    INDEX idx_complaint_created (created_at)
);

# Water Department Field Teams
CREATE TABLE water_field_teams (
    team_id VARCHAR(50) PRIMARY KEY,
    team_name VARCHAR(100) NOT NULL,
    team_type VARCHAR(50) NOT NULL,  -- LEAK_REPAIR, METER_READING, INSPECTION, MAINTENANCE
    team_leader_id VARCHAR(50),
    team_leader_name VARCHAR(100),
    team_leader_phone VARCHAR(20),
    team_members_count INTEGER,
    service_area VARCHAR(255),  -- Geographic area served
    equipment_available TEXT,  -- JSON array of equipment
    current_status VARCHAR(50) DEFAULT 'AVAILABLE',  -- AVAILABLE, BUSY, ON_LEAVE, OFFLINE
    current_location_lat DECIMAL(10, 8),
    current_location_lng DECIMAL(11, 8),
    last_location_update TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_team_type (team_type),
    INDEX idx_team_status (current_status)
);

# Water Service Request Audit Log
CREATE TABLE water_service_audit_log (
    audit_id UUID PRIMARY KEY,
    service_request_id UUID REFERENCES service_requests(service_request_id),
    action_type VARCHAR(50),  -- CREATE, UPDATE, TRANSITION, APPROVE, DENY, DELIVER
    action_description TEXT,
    action_by VARCHAR(50),
    action_timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    before_data JSONB,
    after_data JSONB,
    ip_address VARCHAR(45),
    user_agent VARCHAR(500),
    
    INDEX idx_audit_request (service_request_id),
    INDEX idx_audit_timestamp (action_timestamp),
    INDEX idx_audit_action (action_type)
);

# ============================================================================
# INDEXES FOR PERFORMANCE
# ============================================================================

CREATE INDEX idx_water_consumer_status_active ON water_consumers(status) 
    WHERE status = 'ACTIVE';

CREATE INDEX idx_water_bill_overdue ON water_bills(outstanding_balance) 
    WHERE payment_status = 'OVERDUE' AND outstanding_balance > 0;

CREATE INDEX idx_water_meter_active ON water_meters(meter_status) 
    WHERE meter_status = 'ACTIVE';

CREATE INDEX idx_water_leak_open ON water_leak_complaints(status, created_at DESC) 
    WHERE status IN ('OPEN', 'ASSIGNED', 'IN_PROGRESS');

CREATE INDEX idx_water_payment_success ON water_bill_payments(consumer_id, payment_date DESC)
    WHERE payment_status = 'SUCCESS';

# ============================================================================
# VIEWS FOR REPORTING
# ============================================================================

CREATE VIEW water_consumer_outstanding_bills AS
SELECT 
    c.consumer_id,
    c.consumer_number,
    c.name,
    COUNT(b.bill_id) as pending_bills_count,
    SUM(b.outstanding_balance) as total_outstanding,
    MAX(b.due_date) as oldest_due_date
FROM water_consumers c
LEFT JOIN water_bills b ON c.consumer_id = b.consumer_id 
    AND b.payment_status IN ('PENDING', 'OVERDUE', 'PARTIAL')
WHERE c.status = 'ACTIVE'
GROUP BY c.consumer_id, c.consumer_number, c.name;

CREATE VIEW water_leak_complaints_open AS
SELECT 
    complaint_number,
    location_description,
    severity_level,
    leak_type,
    report_timestamp,
    field_team_assigned_id,
    CURRENT_TIMESTAMP - report_timestamp as hours_open
FROM water_leak_complaints
WHERE status NOT IN ('RESOLVED', 'CLOSED')
ORDER BY severity_level DESC, report_timestamp ASC;

CREATE VIEW water_monthly_billing_summary AS
SELECT 
    billing_period,
    COUNT(DISTINCT consumer_id) as customers,
    COUNT(bill_id) as bills_issued,
    SUM(total_bill_amount) as total_billed,
    SUM(amount_paid) as amount_collected,
    SUM(outstanding_balance) as outstanding_amount
FROM water_bills
GROUP BY billing_period
ORDER BY billing_period DESC;

# ============================================================================
# STORED PROCEDURES
# ============================================================================

CREATE PROCEDURE mark_bill_overdue()
LANGUAGE plpgsql
AS $$
BEGIN
    UPDATE water_bills 
    SET payment_status = 'OVERDUE',
        penalty_charges = total_bill_amount * 0.10,  -- 10% penalty
        updated_at = CURRENT_TIMESTAMP
    WHERE payment_status IN ('PENDING', 'PARTIAL')
        AND due_date < CURRENT_DATE;
END;
$$;

CREATE PROCEDURE auto_generate_monthly_bills()
LANGUAGE plpgsql
AS $$
BEGIN
    -- This would generate bills for all active consumers
    -- Based on meter readings and billing rates
    -- Complex procedure - would involve reading latest meter values
    -- and calculating charges based on consumption
END;
$$;
