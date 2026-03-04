"""
SUVIDHA 2026 - Electricity Services Database Schema
===================================================
PostgreSQL Schema for Electricity Services Module
"""

# ============================================================================
# SERVICE REQUEST TABLES (Core/Shared)
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
# ELECTRICITY-SPECIFIC TABLES
# ============================================================================

CREATE TABLE electricity_customers (
    customer_id VARCHAR(50) PRIMARY KEY,  -- Aadhar-based ID
    aadhar_number VARCHAR(255) NOT NULL ENCRYPTED,  -- Encrypted
    name VARCHAR(255) NOT NULL,
    phone VARCHAR(20) NOT NULL ENCRYPTED,
    email VARCHAR(255) NOT NULL ENCRYPTED,
    address TEXT NOT NULL,
    address_proof_id VARCHAR(100),
    customer_type VARCHAR(50) DEFAULT 'RESIDENTIAL',  -- RESIDENTIAL, COMMERCIAL, INDUSTRIAL
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(50) DEFAULT 'ACTIVE',
    
    UNIQUE (aadhar_number),
    INDEX idx_customer_phone (phone),
    INDEX idx_customer_name (name)
);

CREATE TABLE electricity_meters (
    meter_id UUID PRIMARY KEY,
    meter_number VARCHAR(50) NOT NULL UNIQUE,
    customer_id VARCHAR(50) NOT NULL REFERENCES electricity_customers(customer_id),
    meter_type VARCHAR(50),  -- SINGLE_PHASE, THREE_PHASE
    sanctioned_load DECIMAL(10, 2),  -- in kW
    installation_date DATE,
    meter_status VARCHAR(50) DEFAULT 'ACTIVE',  -- ACTIVE, INACTIVE, SUSPENDED
    location_coordinates GEOGRAPHY,
    meter_reading_type VARCHAR(50),  -- MANUAL, AUTOMATIC, SMART
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_meter_customer (customer_id),
    INDEX idx_meter_status (meter_status),
    INDEX idx_meter_number (meter_number)
);

CREATE TABLE electricity_bills (
    bill_id UUID PRIMARY KEY,
    meter_id UUID NOT NULL REFERENCES electricity_meters(meter_id),
    bill_number VARCHAR(100) NOT NULL UNIQUE,
    billing_period VARCHAR(10) NOT NULL,  -- YYYY-MM format
    consumption_units DECIMAL(10, 2) NOT NULL,  -- in kWh
    rate_per_unit DECIMAL(10, 4) NOT NULL,
    fixed_charges DECIMAL(10, 2),
    variable_charges DECIMAL(10, 2),
    tax_amount DECIMAL(10, 2),
    bill_amount DECIMAL(10, 2) NOT NULL,
    amount_paid DECIMAL(10, 2) DEFAULT 0,
    bill_date DATE NOT NULL,
    due_date DATE NOT NULL,
    bill_status VARCHAR(50) DEFAULT 'PENDING',  -- PENDING, PAID, OVERDUE, WRITTEN_OFF
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE (meter_id, billing_period),
    INDEX idx_bill_meter (meter_id),
    INDEX idx_bill_status (bill_status),
    INDEX idx_bill_period (billing_period),
    INDEX idx_bill_due_date (due_date)
);

CREATE TABLE electricity_payments (
    payment_id UUID PRIMARY KEY,
    bill_id UUID REFERENCES electricity_bills(bill_id),
    customer_id VARCHAR(50) NOT NULL REFERENCES electricity_customers(customer_id),
    amount_paid DECIMAL(10, 2) NOT NULL,
    payment_method VARCHAR(50) NOT NULL,  -- CARD, UPI, NET_BANKING, CASH, CHEQUE
    payment_date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    payment_status VARCHAR(50) DEFAULT 'SUCCESS',  -- SUCCESS, FAILED, PENDING
    gateway_name VARCHAR(100),  -- RazorPay, PayU, etc.
    gateway_reference_id VARCHAR(255),
    gateway_response JSONB,
    payment_proof_url VARCHAR(500),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_payment_customer (customer_id),
    INDEX idx_payment_status (payment_status),
    INDEX idx_payment_date (payment_date),
    INDEX idx_payment_bill (bill_id)
);

CREATE TABLE electricity_service_transfers (
    transfer_id UUID PRIMARY KEY,
    service_request_id UUID NOT NULL REFERENCES service_requests(service_request_id),
    meter_id UUID NOT NULL REFERENCES electricity_meters(meter_id),
    old_customer_id VARCHAR(50) NOT NULL REFERENCES electricity_customers(customer_id),
    new_customer_id VARCHAR(50) NOT NULL REFERENCES electricity_customers(customer_id),
    identity_proof_id VARCHAR(100),
    ownership_proof_id VARCHAR(100),
    consent_doc_id VARCHAR(100),
    effective_date DATE NOT NULL,
    transfer_status VARCHAR(50) DEFAULT 'PENDING',  -- PENDING, APPROVED, EXECUTED, REJECTED
    approved_by VARCHAR(100),
    approval_date TIMESTAMP,
    transferred_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_transfer_request (service_request_id),
    INDEX idx_transfer_meter (meter_id),
    INDEX idx_transfer_old_customer (old_customer_id),
    INDEX idx_transfer_new_customer (new_customer_id),
    INDEX idx_transfer_status (transfer_status)
);

CREATE TABLE electricity_complaints (
    complaint_id UUID PRIMARY KEY,
    service_request_id UUID NOT NULL REFERENCES service_requests(service_request_id),
    customer_id VARCHAR(50) NOT NULL REFERENCES electricity_customers(customer_id),
    meter_id UUID REFERENCES electricity_meters(meter_id),
    complaint_category VARCHAR(100) NOT NULL,  -- BILLING, SERVICE, METER, CONNECTION, OTHER
    complaint_description TEXT NOT NULL,
    complaint_priority VARCHAR(50) DEFAULT 'NORMAL',  -- LOW, NORMAL, HIGH, URGENT
    complaint_status VARCHAR(50) DEFAULT 'OPEN',  -- OPEN, ACKNOWLEDGED, IN_PROGRESS, RESOLVED, CLOSED
    assigned_to VARCHAR(100),
    resolution_notes TEXT,
    resolved_at TIMESTAMP,
    customer_satisfaction_rating INTEGER,  -- 1-5
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_complaint_customer (customer_id),
    INDEX idx_complaint_status (complaint_status),
    INDEX idx_complaint_priority (complaint_priority),
    INDEX idx_complaint_created (created_at)
);

CREATE TABLE electricity_meter_readings (
    reading_id UUID PRIMARY KEY,
    meter_id UUID NOT NULL REFERENCES electricity_meters(meter_id),
    reading_value DECIMAL(10, 2) NOT NULL,
    reading_date DATE NOT NULL,
    reading_type VARCHAR(50),  -- MANUAL, AUTOMATIC, ESTIMATED
    consumption_units DECIMAL(10, 2),  -- Calculated from previous reading
    submitted_by VARCHAR(50),
    submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE (meter_id, reading_date),
    INDEX idx_reading_meter (meter_id),
    INDEX idx_reading_date (reading_date)
);

CREATE TABLE electricity_connection_requests (
    request_id UUID PRIMARY KEY,
    service_request_id UUID NOT NULL REFERENCES service_requests(service_request_id),
    applicant_id VARCHAR(50) NOT NULL REFERENCES electricity_customers(customer_id),
    address TEXT NOT NULL,
    load_requirement DECIMAL(10, 2) NOT NULL,  -- in kW
    property_documents JSONB,  -- Document references
    requested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    approved_at TIMESTAMP,
    activation_date TIMESTAMP,
    assigned_meter_id UUID REFERENCES electricity_meters(meter_id),
    request_status VARCHAR(50) DEFAULT 'PENDING',  -- PENDING, APPROVED, REJECTED, ACTIVATED
    
    INDEX idx_connection_applicant (applicant_id),
    INDEX idx_connection_status (request_status)
);

CREATE TABLE electricity_meter_changes (
    change_id UUID PRIMARY KEY,
    service_request_id UUID NOT NULL REFERENCES service_requests(service_request_id),
    old_meter_id UUID NOT NULL REFERENCES electricity_meters(meter_id),
    new_meter_id UUID REFERENCES electricity_meters(meter_id),
    reason_code VARCHAR(100) NOT NULL,
    reason_description TEXT,
    inspection_report_id VARCHAR(100),
    inspection_date DATE,
    inspected_by VARCHAR(100),
    change_status VARCHAR(50) DEFAULT 'PENDING',  -- PENDING, INSPECTED, APPROVED, COMPLETED
    completed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_change_request (service_request_id),
    INDEX idx_change_status (change_status)
);


# ============================================================================
# AUDIT & SECURITY TABLES
# ============================================================================

CREATE TABLE service_audit_log (
    log_id UUID PRIMARY KEY,
    service_request_id UUID REFERENCES service_requests(service_request_id),
    actor_id VARCHAR(50) NOT NULL,
    actor_role VARCHAR(50) NOT NULL,
    action VARCHAR(100) NOT NULL,
    action_details JSONB,
    ip_address VARCHAR(45),
    user_agent VARCHAR(500),
    timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_audit_request (service_request_id),
    INDEX idx_audit_timestamp (timestamp),
    INDEX idx_audit_actor (actor_id)
);

CREATE TABLE payment_audit_log (
    log_id UUID PRIMARY KEY,
    payment_id UUID NOT NULL REFERENCES electricity_payments(payment_id),
    event_type VARCHAR(100) NOT NULL,  -- INITIATED, VALIDATED, GATEWAY_CALLED, CONFIRMED, FAILED
    event_details JSONB,
    timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_payment_log (payment_id),
    INDEX idx_payment_log_timestamp (timestamp)
);


# ============================================================================
# REPORTING & ANALYTICS TABLES
# ============================================================================

CREATE TABLE daily_metrics (
    metric_date DATE PRIMARY KEY,
    total_bills_generated INTEGER,
    total_payments_received DECIMAL(15, 2),
    average_payment_value DECIMAL(10, 2),
    total_complaints_received INTEGER,
    complaints_resolved INTEGER,
    service_transfers_completed INTEGER,
    new_connections_activated INTEGER,
    system_uptime_percentage DECIMAL(5, 2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE customer_analytics (
    customer_id VARCHAR(50) PRIMARY KEY REFERENCES electricity_customers(customer_id),
    total_bills_paid INTEGER,
    total_amount_paid DECIMAL(15, 2),
    average_billing_cycle_days DECIMAL(5, 2),
    avg_payment_time_days DECIMAL(5, 2),
    total_complaints_filed INTEGER,
    complaints_resolved INTEGER,
    last_payment_date DATE,
    total_overdue_amount DECIMAL(10, 2),
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


# ============================================================================
# INDEXES FOR PERFORMANCE
# ============================================================================

CREATE INDEX idx_service_requests_composite ON service_requests(service_type, status, created_at);
CREATE INDEX idx_bills_composite ON electricity_bills(meter_id, bill_status, due_date);
CREATE INDEX idx_payments_composite ON electricity_payments(customer_id, payment_status, payment_date);
CREATE INDEX idx_complaints_composite ON electricity_complaints(customer_id, complaint_status, created_at);


# ============================================================================
# VIEWS FOR COMMON QUERIES
# ============================================================================

CREATE VIEW customer_outstanding_bills AS
SELECT 
    c.customer_id,
    c.name,
    c.phone,
    em.meter_number,
    eb.bill_number,
    eb.bill_amount,
    eb.amount_paid,
    (eb.bill_amount - eb.amount_paid) as outstanding_amount,
    eb.due_date,
    DATEDIFF(day, eb.due_date, CURRENT_DATE) as days_overdue
FROM electricity_customers c
JOIN electricity_meters em ON c.customer_id = em.customer_id
JOIN electricity_bills eb ON em.meter_id = eb.meter_id
WHERE eb.bill_status IN ('PENDING', 'OVERDUE')
ORDER BY eb.due_date ASC;

CREATE VIEW pending_service_requests AS
SELECT 
    sr.service_request_id,
    sr.service_type,
    sr.initiator_id,
    sr.beneficiary_id,
    sr.status,
    sr.created_at,
    sr.updated_at,
    sr.current_owner,
    COUNT(srh.history_id) as status_changes
FROM service_requests sr
LEFT JOIN service_request_history srh ON sr.service_request_id = srh.service_request_id
WHERE sr.status IN ('SUBMITTED', 'ACKNOWLEDGED', 'PENDING', 'IN_PROGRESS')
GROUP BY sr.service_request_id
ORDER BY sr.created_at ASC;

CREATE VIEW payment_summary AS
SELECT 
    payment_date::date,
    COUNT(*) as total_transactions,
    SUM(amount_paid) as total_amount,
    payment_method,
    payment_status,
    COUNT(CASE WHEN payment_status = 'SUCCESS' THEN 1 END) as successful_payments,
    COUNT(CASE WHEN payment_status = 'FAILED' THEN 1 END) as failed_payments
FROM electricity_payments
GROUP BY payment_date::date, payment_method, payment_status;


# ============================================================================
# SAMPLE DATA INSERTION (For Testing)
# ============================================================================

INSERT INTO electricity_customers (customer_id, aadhar_number, name, phone, email, address, customer_type)
VALUES 
    ('123456789012', 'ENCRYPTED_AADHAR_1', 'Raj Kumar', 'ENCRYPTED_PHONE_1', 'raj@example.com', '123 Main St', 'RESIDENTIAL'),
    ('987654321098', 'ENCRYPTED_AADHAR_2', 'Priya Singh', 'ENCRYPTED_PHONE_2', 'priya@example.com', '456 Oak Ave', 'RESIDENTIAL'),
    ('555666777888', 'ENCRYPTED_AADHAR_3', 'ABC Corporation', 'ENCRYPTED_PHONE_3', 'info@abccorp.com', '789 Business Park', 'COMMERCIAL');

INSERT INTO electricity_meters (meter_number, customer_id, meter_type, sanctioned_load, meter_status)
VALUES 
    ('ELEC123456', '123456789012', 'SINGLE_PHASE', 5.00, 'ACTIVE'),
    ('ELEC789012', '987654321098', 'THREE_PHASE', 10.00, 'ACTIVE'),
    ('ELEC345678', '555666777888', 'THREE_PHASE', 25.00, 'ACTIVE');


# ============================================================================
# STORED PROCEDURES (For Complex Operations)
# ============================================================================

-- Procedure to calculate bill
CREATE OR REPLACE FUNCTION calculate_electricity_bill(
    p_meter_id UUID,
    p_billing_period VARCHAR,
    p_current_reading DECIMAL,
    p_previous_reading DECIMAL
) RETURNS TABLE (
    consumption_units DECIMAL,
    bill_amount DECIMAL,
    fixed_charges DECIMAL,
    variable_charges DECIMAL,
    tax_amount DECIMAL
) AS $$
DECLARE
    v_consumption DECIMAL;
    v_rate DECIMAL;
    v_fixed DECIMAL;
    v_tax_percent DECIMAL := 0.18;  -- 18% GST
    v_variable DECIMAL;
    v_total DECIMAL;
BEGIN
    -- Calculate consumption
    v_consumption := p_current_reading - p_previous_reading;
    
    -- Get rate from tariff table (simplified)
    v_rate := 5.50;  -- Per unit cost
    v_fixed := 100.00;  -- Fixed monthly charge
    
    -- Calculate charges
    v_variable := v_consumption * v_rate;
    v_total := v_fixed + v_variable;
    
    -- Calculate tax
    v_tax := v_total * (v_tax_percent / 100);
    
    RETURN QUERY SELECT v_consumption, (v_total + v_tax), v_fixed, v_variable, v_tax;
END;
$$ LANGUAGE plpgsql;

