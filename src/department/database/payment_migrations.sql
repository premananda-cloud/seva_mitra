-- project/database/payment_migrations.sql
-- ==========================================
-- Adds the 3 payment tables from Section 3 of KOISK_Payment_Requirements.md
-- and patches the existing users table.
--
-- Run AFTER init.sql:
--   psql -U koisk_user -d koisk_db -f database/payment_migrations.sql
--
-- Safe to re-run — all statements use IF NOT EXISTS / IF EXISTS guards.

-- Enable uuid generation if not already enabled
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ============================================================================
-- Patch existing users table (Section 3.2)
-- ============================================================================

ALTER TABLE users ADD COLUMN IF NOT EXISTS email               VARCHAR(200);
ALTER TABLE users ADD COLUMN IF NOT EXISTS portone_customer_id VARCHAR(200);

-- ============================================================================
-- payment_profiles  (Section 3.1)
-- ============================================================================

CREATE TABLE IF NOT EXISTS payment_profiles (
    -- id == user.id for O(1) lookup by primary key
    id                   VARCHAR(200) PRIMARY KEY,
    user_id              VARCHAR(200) NOT NULL,

    portone_customer_id  VARCHAR(200) UNIQUE,
    razorpay_customer_id VARCHAR(200),

    -- Snapshot of user data at time of gateway registration
    name                 VARCHAR(200) NOT NULL,
    contact              VARCHAR(20)  NOT NULL,   -- +91XXXXXXXXXX
    email                VARCHAR(200),

    default_method       VARCHAR(50),             -- upi | card | netbanking
    preferred_gateway    VARCHAR(50)  DEFAULT 'portone',
    is_default           BOOLEAN      DEFAULT TRUE,

    created_at           TIMESTAMP    DEFAULT CURRENT_TIMESTAMP,
    updated_at           TIMESTAMP    DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_pp_user_id    ON payment_profiles(user_id);
CREATE INDEX IF NOT EXISTS idx_pp_portone_id ON payment_profiles(portone_customer_id);

-- auto-update updated_at
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_trigger WHERE tgname = 'trigger_payment_profiles_updated_at'
    ) THEN
        CREATE TRIGGER trigger_payment_profiles_updated_at
        BEFORE UPDATE ON payment_profiles
        FOR EACH ROW EXECUTE FUNCTION update_updated_at();
    END IF;
END $$;

-- ============================================================================
-- payments  (Section 3.1)
-- ============================================================================

CREATE TABLE IF NOT EXISTS payments (
    id                   VARCHAR(200) PRIMARY KEY,
    user_id              VARCHAR(200) NOT NULL,
    bill_id              VARCHAR(100) NOT NULL,
    department           VARCHAR(50)  NOT NULL,   -- electricity | gas | water

    amount               DECIMAL(10,2) NOT NULL,
    currency             VARCHAR(3)    DEFAULT 'INR',

    -- Gateway fields
    gateway              VARCHAR(50)   NOT NULL,  -- portone | razorpay | mock
    gateway_payment_id   VARCHAR(200),
    gateway_order_id     VARCHAR(200),
    gateway_status       VARCHAR(50),

    payment_method       VARCHAR(50),             -- upi | card | netbanking
    consumer_number      VARCHAR(100),
    billing_period       VARCHAR(20),             -- YYYY-MM

    -- Section 3.3 status values (lowercase, match frontend constants exactly)
    -- pending | paid | failed | refunded | offline_queued
    reference_no         VARCHAR(100) UNIQUE,
    status               VARCHAR(50)  NOT NULL DEFAULT 'pending',
    error_message        TEXT,

    created_at           TIMESTAMP    DEFAULT CURRENT_TIMESTAMP,
    updated_at           TIMESTAMP    DEFAULT CURRENT_TIMESTAMP,
    paid_at              TIMESTAMP,

    metadata             JSONB        DEFAULT '{}'
);

CREATE INDEX IF NOT EXISTS idx_pay_user_id    ON payments(user_id);
CREATE INDEX IF NOT EXISTS idx_pay_status     ON payments(status);
CREATE INDEX IF NOT EXISTS idx_pay_dept       ON payments(department);
CREATE INDEX IF NOT EXISTS idx_pay_created_at ON payments(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_pay_gw_order   ON payments(gateway_order_id);

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_trigger WHERE tgname = 'trigger_payments_updated_at'
    ) THEN
        CREATE TRIGGER trigger_payments_updated_at
        BEFORE UPDATE ON payments
        FOR EACH ROW EXECUTE FUNCTION update_updated_at();
    END IF;
END $$;

-- ============================================================================
-- refunds  (Section 3.1)
-- ============================================================================

CREATE TABLE IF NOT EXISTS refunds (
    id                VARCHAR(200) PRIMARY KEY,
    payment_id        VARCHAR(200) NOT NULL REFERENCES payments(id) ON DELETE CASCADE,
    amount            DECIMAL(10,2) NOT NULL,
    reason            TEXT,
    gateway_refund_id VARCHAR(200),
    status            VARCHAR(50)  DEFAULT 'pending',   -- pending | processed | failed
    created_at        TIMESTAMP    DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_refunds_payment_id ON refunds(payment_id);

-- ============================================================================
-- Grant permissions to app user
-- ============================================================================

GRANT SELECT, INSERT, UPDATE, DELETE
    ON payment_profiles, payments, refunds
    TO koisk_user;

-- ============================================================================
-- Demo seed data — matches localDB demo bills in requirements Section 1.5
-- ============================================================================

INSERT INTO payments (
    id, user_id, bill_id, department, amount, currency,
    gateway, payment_method, consumer_number, billing_period,
    reference_no, status, paid_at, created_at
)
VALUES
    -- Electricity bill — paid (demo history record)
    (
        gen_random_uuid()::text,
        'demo-user-ramesh-001',
        'BILL-ELEC-202601',
        'electricity',
        1420.00, 'INR',
        'portone', 'upi', 'ELEC-MH-00234', '2026-01',
        'PAY-ELEC-20260210-0001', 'paid',
        '2026-02-10 09:30:00', '2026-02-10 09:28:00'
    ),
    -- Water bill — paid
    (
        gen_random_uuid()::text,
        'demo-user-ramesh-001',
        'BILL-WATER-202601',
        'water',
        310.00, 'INR',
        'razorpay', 'upi', 'WAT-MH-00891', '2026-01',
        'PAY-WAT-20260205-0001', 'paid',
        '2026-02-05 11:15:00', '2026-02-05 11:13:00'
    )
ON CONFLICT DO NOTHING;

SELECT 'Payment migration completed successfully' AS status;
SELECT COUNT(*) AS payment_profile_rows FROM payment_profiles;
SELECT COUNT(*) AS payment_rows          FROM payments;
