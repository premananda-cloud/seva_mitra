-- database/init.sql
-- PostgreSQL initialization script for KOISK database
-- Run with: psql -U koisk_user -d koisk_db -f init.sql

-- Enable extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ============================================================================
-- Users Table
-- ============================================================================

CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    
    -- Profile
    phone_number VARCHAR(20),
    address TEXT,
    city VARCHAR(100),
    state VARCHAR(100),
    postal_code VARCHAR(10),
    
    -- Status
    is_active BOOLEAN DEFAULT true,
    is_verified BOOLEAN DEFAULT false,
    email_verified BOOLEAN DEFAULT false,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP,
    
    -- OAuth
    google_id VARCHAR(255) UNIQUE,
    
    -- Indexes
    INDEX idx_username (username),
    INDEX idx_email (email)
);

-- ============================================================================
-- Service Requests Table
-- ============================================================================

CREATE TABLE IF NOT EXISTS service_requests (
    id SERIAL PRIMARY KEY,
    service_request_id VARCHAR(50) UNIQUE NOT NULL,
    user_id INTEGER NOT NULL REFERENCES users(id),
    
    -- Service details
    service_type VARCHAR(50) NOT NULL,
    status VARCHAR(20) DEFAULT 'DRAFT',
    
    -- Request data
    payload TEXT,
    correlation_id VARCHAR(100),
    
    -- Error handling
    error_code VARCHAR(50),
    error_message TEXT,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    
    -- Indexes
    INDEX idx_service_request_id (service_request_id),
    INDEX idx_user_id (user_id),
    INDEX idx_service_type (service_type),
    INDEX idx_status (status)
);

-- ============================================================================
-- Electricity Meters Table
-- ============================================================================

CREATE TABLE IF NOT EXISTS electricity_meters (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    meter_number VARCHAR(50) UNIQUE NOT NULL,
    
    -- Meter details
    meter_type VARCHAR(50),
    status VARCHAR(20) DEFAULT 'ACTIVE',
    load_requirement FLOAT,
    
    -- Billing
    monthly_bill FLOAT DEFAULT 0.0,
    outstanding_amount FLOAT DEFAULT 0.0,
    last_reading FLOAT,
    last_reading_date TIMESTAMP,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Indexes
    INDEX idx_meter_number (meter_number),
    INDEX idx_user_id (user_id)
);

-- ============================================================================
-- Water Consumers Table
-- ============================================================================

CREATE TABLE IF NOT EXISTS water_consumers (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    consumer_number VARCHAR(50) UNIQUE NOT NULL,
    
    -- Consumer details
    property_type VARCHAR(50),
    status VARCHAR(20) DEFAULT 'ACTIVE',
    
    -- Billing
    monthly_bill FLOAT DEFAULT 0.0,
    outstanding_amount FLOAT DEFAULT 0.0,
    last_reading FLOAT,
    last_reading_date TIMESTAMP,
    usage_limit FLOAT,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Indexes
    INDEX idx_consumer_number (consumer_number),
    INDEX idx_user_id (user_id)
);

-- ============================================================================
-- Gas Consumers Table
-- ============================================================================

CREATE TABLE IF NOT EXISTS gas_consumers (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    consumer_number VARCHAR(50) UNIQUE NOT NULL,
    
    -- Consumer details
    connection_type VARCHAR(50),
    status VARCHAR(20) DEFAULT 'ACTIVE',
    
    -- Billing
    monthly_bill FLOAT DEFAULT 0.0,
    outstanding_amount FLOAT DEFAULT 0.0,
    last_reading FLOAT,
    last_reading_date TIMESTAMP,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Indexes
    INDEX idx_consumer_number (consumer_number),
    INDEX idx_user_id (user_id)
);

-- ============================================================================
-- Payment History Table
-- ============================================================================

CREATE TABLE IF NOT EXISTS payment_history (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    service_request_id INTEGER REFERENCES service_requests(id),
    
    -- Payment details
    service_type VARCHAR(50) NOT NULL,
    amount FLOAT NOT NULL,
    payment_method VARCHAR(50) NOT NULL,
    payment_status VARCHAR(20) DEFAULT 'PENDING',
    
    -- Reference
    transaction_id VARCHAR(100),
    reference_number VARCHAR(100),
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    
    -- Indexes
    INDEX idx_user_id (user_id),
    INDEX idx_service_request_id (service_request_id),
    INDEX idx_payment_status (payment_status)
);

-- ============================================================================
-- Create Indexes
-- ============================================================================

CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_created_at ON users(created_at DESC);

CREATE INDEX IF NOT EXISTS idx_service_requests_user_id ON service_requests(user_id);
CREATE INDEX IF NOT EXISTS idx_service_requests_status ON service_requests(status);
CREATE INDEX IF NOT EXISTS idx_service_requests_created_at ON service_requests(created_at DESC);

CREATE INDEX IF NOT EXISTS idx_electricity_meters_user_id ON electricity_meters(user_id);
CREATE INDEX IF NOT EXISTS idx_electricity_meters_meter_number ON electricity_meters(meter_number);

CREATE INDEX IF NOT EXISTS idx_water_consumers_user_id ON water_consumers(user_id);
CREATE INDEX IF NOT EXISTS idx_water_consumers_number ON water_consumers(consumer_number);

CREATE INDEX IF NOT EXISTS idx_gas_consumers_user_id ON gas_consumers(user_id);
CREATE INDEX IF NOT EXISTS idx_gas_consumers_number ON gas_consumers(consumer_number);

CREATE INDEX IF NOT EXISTS idx_payment_history_user_id ON payment_history(user_id);
CREATE INDEX IF NOT EXISTS idx_payment_history_status ON payment_history(payment_status);
CREATE INDEX IF NOT EXISTS idx_payment_history_created_at ON payment_history(created_at DESC);

-- ============================================================================
-- Create Triggers for Updated_at Timestamp
-- ============================================================================

CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_users_updated_at
BEFORE UPDATE ON users
FOR EACH ROW
EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER trigger_service_requests_updated_at
BEFORE UPDATE ON service_requests
FOR EACH ROW
EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER trigger_electricity_meters_updated_at
BEFORE UPDATE ON electricity_meters
FOR EACH ROW
EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER trigger_water_consumers_updated_at
BEFORE UPDATE ON water_consumers
FOR EACH ROW
EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER trigger_gas_consumers_updated_at
BEFORE UPDATE ON gas_consumers
FOR EACH ROW
EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER trigger_payment_history_updated_at
BEFORE UPDATE ON payment_history
FOR EACH ROW
EXECUTE FUNCTION update_updated_at();

-- ============================================================================
-- Sample Data (Optional - Remove for production)
-- ============================================================================

-- Insert sample user
INSERT INTO users (username, email, full_name, hashed_password, is_active, email_verified)
VALUES (
    'testuser',
    'test@example.com',
    'Test User',
    -- Password: testpassword123 (bcrypt hash)
    '$2b$12$test.hash.example.here',
    true,
    true
)
ON CONFLICT (username) DO NOTHING;

-- Insert sample electricity meter
INSERT INTO electricity_meters (user_id, meter_number, meter_type, status, load_requirement, monthly_bill)
SELECT 
    u.id,
    'ELEC123456',
    'Single Phase',
    'ACTIVE',
    5.0,
    1500.00
FROM users u
WHERE u.username = 'testuser'
ON CONFLICT (meter_number) DO NOTHING;

-- Insert sample water consumer
INSERT INTO water_consumers (user_id, consumer_number, property_type, status, monthly_bill)
SELECT 
    u.id,
    'WATER123456',
    'Residential',
    'ACTIVE',
    800.00
FROM users u
WHERE u.username = 'testuser'
ON CONFLICT (consumer_number) DO NOTHING;

-- Insert sample gas consumer
INSERT INTO gas_consumers (user_id, consumer_number, connection_type, status, monthly_bill)
SELECT 
    u.id,
    'GAS123456',
    'Domestic',
    'ACTIVE',
    1200.00
FROM users u
WHERE u.username = 'testuser'
ON CONFLICT (consumer_number) DO NOTHING;

-- ============================================================================
-- Grant Permissions
-- ============================================================================

GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO koisk_user;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO koisk_user;

-- ============================================================================
-- Display Information
-- ============================================================================

SELECT 'Database initialization completed!' as status;
SELECT COUNT(*) as users_count FROM users;
SELECT COUNT(*) as service_requests_count FROM service_requests;
