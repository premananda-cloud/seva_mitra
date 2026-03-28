"""
database/models.py
==================
Single source of truth for ALL ORM models.
Fixes the dual-Base bug from the original codebase.

Tables:
  users, admins, service_requests
  electricity_meters, water_consumers, municipal_consumers
  payments, payment_profiles, refunds
"""

import os as _os
from sqlalchemy import (
    Column, Integer, String, DateTime, Boolean, Float,
    ForeignKey, Text, Enum as SAEnum, Numeric, Index, JSON
)
# JSONB for PostgreSQL, plain JSON for SQLite (dev)
_DB = _os.getenv("DATABASE_URL", "sqlite")
if "postgresql" in _DB or "postgres" in _DB:
    from sqlalchemy.dialects.postgresql import JSONB
else:
    JSONB = JSON  # type: ignore  # noqa: N816

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

Base = declarative_base()  # ONE Base for everything


# ─── Enums ────────────────────────────────────────────────────────────────────

class ServiceStatusEnum(str, enum.Enum):
    DRAFT        = "DRAFT"
    SUBMITTED    = "SUBMITTED"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    PENDING      = "PENDING"
    APPROVED     = "APPROVED"
    DENIED       = "DENIED"
    IN_PROGRESS  = "IN_PROGRESS"
    DELIVERED    = "DELIVERED"
    FAILED       = "FAILED"
    CANCELLED    = "CANCELLED"


class DepartmentEnum(str, enum.Enum):
    ELECTRICITY = "electricity"
    WATER       = "water"
    GAS         = "gas"
    MUNICIPAL   = "municipal"


class PaymentStatusEnum(str, enum.Enum):
    PENDING        = "pending"
    PAID           = "paid"
    FAILED         = "failed"
    REFUNDED       = "refunded"
    OFFLINE_QUEUED = "offline_queued"


# ─── Users ────────────────────────────────────────────────────────────────────

class User(Base):
    __tablename__ = "users"

    id               = Column(Integer, primary_key=True, index=True)
    username         = Column(String(50),  unique=True, index=True, nullable=False)
    email            = Column(String(255), unique=True, index=True, nullable=True)
    full_name        = Column(String(255), nullable=False)
    hashed_password  = Column(String(255), nullable=False)

    phone_number     = Column(String(20),  nullable=True)
    address          = Column(Text,        nullable=True)
    city             = Column(String(100), nullable=True)
    state            = Column(String(100), nullable=True)
    postal_code      = Column(String(10),  nullable=True)

    is_active        = Column(Boolean, default=True)
    is_verified      = Column(Boolean, default=False)
    email_verified   = Column(Boolean, default=False)

    created_at       = Column(DateTime, default=datetime.utcnow)
    updated_at       = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login       = Column(DateTime, nullable=True)
    google_id        = Column(String(255), nullable=True, unique=True)

    # Relationships
    service_requests      = relationship("ServiceRequest",      back_populates="user", cascade="all, delete-orphan")
    electricity_meters    = relationship("ElectricityMeter",    back_populates="user", cascade="all, delete-orphan")
    water_consumers       = relationship("WaterConsumer",       back_populates="user", cascade="all, delete-orphan")
    gas_consumers         = relationship("GasConsumer",         back_populates="user", cascade="all, delete-orphan")
    municipal_consumers   = relationship("MunicipalConsumer",   back_populates="user", cascade="all, delete-orphan")
    payment_profile       = relationship("PaymentProfile",      back_populates="user", uselist=False)


# ─── Admins ───────────────────────────────────────────────────────────────────

class Admin(Base):
    """
    Separate admin/merchant table.
    Admins authenticate via /admin/login and get a scoped JWT.
    department=None means super-admin (sees everything).
    """
    __tablename__ = "admins"

    id              = Column(Integer, primary_key=True, index=True)
    username        = Column(String(50),  unique=True, index=True, nullable=False)
    email           = Column(String(255), unique=True, index=True, nullable=False)
    full_name       = Column(String(255), nullable=False)
    hashed_password = Column(String(255), nullable=False)

    # Role: "super_admin" | "department_admin" | "merchant"
    role            = Column(String(50), default="department_admin", nullable=False)

    # If role == "department_admin" or "merchant" — scope to one dept
    # NULL means super-admin (all departments)
    department      = Column(String(50), nullable=True)

    # Merchant payment config — stored as JSONB
    # {"gateway": "portone", "merchant_id": "...", "channel_key": "..."}
    merchant_config = Column(JSONB, default=dict)

    is_active       = Column(Boolean, default=True)
    created_at      = Column(DateTime, default=datetime.utcnow)
    updated_at      = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login      = Column(DateTime, nullable=True)

    __table_args__ = (
        Index("idx_admin_role",       "role"),
        Index("idx_admin_department", "department"),
    )


# ─── Service Requests ─────────────────────────────────────────────────────────

class ServiceRequest(Base):
    """
    Every service request from any department lands here.
    This is the audit log / state machine table.
    """
    __tablename__ = "service_requests"

    id                 = Column(Integer,     primary_key=True, index=True)
    service_request_id = Column(String(50),  unique=True, index=True, nullable=False)
    user_id            = Column(Integer,     ForeignKey("users.id"), nullable=True)  # nullable for guest requests

    # Department + type
    department         = Column(String(50),  nullable=False, index=True)   # electricity | water | municipal
    service_type       = Column(String(80),  nullable=False, index=True)   # e.g. ELECTRICITY_PAY_BILL

    # State machine
    status             = Column(String(30),  default="SUBMITTED", index=True)

    # Full request payload as JSON
    payload            = Column(JSONB,       default=dict)

    # Admin who last acted (optional)
    handled_by_admin   = Column(Integer,     ForeignKey("admins.id"), nullable=True)

    # Error info
    error_code         = Column(String(50),  nullable=True)
    error_message      = Column(Text,        nullable=True)

    # Link to payment (if this request involved payment)
    payment_id         = Column(String(200), ForeignKey("payments.id"), nullable=True)

    # Timestamps
    created_at         = Column(DateTime, default=datetime.utcnow)
    updated_at         = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at       = Column(DateTime, nullable=True)

    # Relationships
    user    = relationship("User",    back_populates="service_requests")
    admin   = relationship("Admin")
    payment = relationship("Payment", foreign_keys=[payment_id])

    __table_args__ = (
        Index("idx_sr_department",   "department"),
        Index("idx_sr_service_type", "service_type"),
        Index("idx_sr_status",       "status"),
        Index("idx_sr_created_at",   "created_at"),
    )


# ─── Electricity ──────────────────────────────────────────────────────────────

class ElectricityMeter(Base):
    __tablename__ = "electricity_meters"

    id                  = Column(Integer, primary_key=True, index=True)
    user_id             = Column(Integer, ForeignKey("users.id"), nullable=False)
    meter_number        = Column(String(50), unique=True, index=True, nullable=False)
    meter_type          = Column(String(50), nullable=True)
    status              = Column(String(20), default="ACTIVE")
    load_requirement    = Column(Float, nullable=True)
    monthly_bill        = Column(Float, default=0.0)
    outstanding_amount  = Column(Float, default=0.0)
    last_reading        = Column(Float, nullable=True)
    last_reading_date   = Column(DateTime, nullable=True)
    created_at          = Column(DateTime, default=datetime.utcnow)
    updated_at          = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="electricity_meters")


# ─── Water ────────────────────────────────────────────────────────────────────

class WaterConsumer(Base):
    __tablename__ = "water_consumers"

    id                  = Column(Integer, primary_key=True, index=True)
    user_id             = Column(Integer, ForeignKey("users.id"), nullable=False)
    consumer_number     = Column(String(50), unique=True, index=True, nullable=False)
    property_type       = Column(String(50), nullable=True)
    status              = Column(String(20), default="ACTIVE")
    monthly_bill        = Column(Float, default=0.0)
    outstanding_amount  = Column(Float, default=0.0)
    last_reading        = Column(Float, nullable=True)
    last_reading_date   = Column(DateTime, nullable=True)
    usage_limit         = Column(Float, nullable=True)
    created_at          = Column(DateTime, default=datetime.utcnow)
    updated_at          = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="water_consumers")


# ─── Gas ─────────────────────────────────────────────────────────────────────

class GasConsumer(Base):
    __tablename__ = "gas_consumers"

    id                  = Column(Integer, primary_key=True, index=True)
    user_id             = Column(Integer, ForeignKey("users.id"), nullable=False)
    consumer_number     = Column(String(50), unique=True, index=True, nullable=False)
    connection_type     = Column(String(50), nullable=True)   # domestic | commercial
    status              = Column(String(20), default="ACTIVE")
    monthly_bill        = Column(Float, default=0.0)
    outstanding_amount  = Column(Float, default=0.0)
    meter_number        = Column(String(50), nullable=True, unique=True)
    last_reading        = Column(Float, nullable=True)
    last_reading_date   = Column(DateTime, nullable=True)
    created_at          = Column(DateTime, default=datetime.utcnow)
    updated_at          = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="gas_consumers")


# ─── Municipal ────────────────────────────────────────────────────────────────

class MunicipalConsumer(Base):
    """
    Municipal services: property tax, trade license, birth/death certificates,
    building plan approval, health certificates, solid waste management, etc.
    """
    __tablename__ = "municipal_consumers"

    id                  = Column(Integer, primary_key=True, index=True)
    user_id             = Column(Integer, ForeignKey("users.id"), nullable=False)
    consumer_number     = Column(String(50), unique=True, index=True, nullable=False)

    # Property details for property-tax-based services
    property_id         = Column(String(50), nullable=True, index=True)
    property_type       = Column(String(50), nullable=True)   # Residential | Commercial | Industrial
    ward_number         = Column(String(20), nullable=True)
    zone                = Column(String(50), nullable=True)

    # Trade license (if applicable)
    trade_license_no    = Column(String(50), nullable=True)
    business_name       = Column(String(200), nullable=True)

    # Billing
    annual_tax          = Column(Float, default=0.0)
    outstanding_amount  = Column(Float, default=0.0)
    last_paid_date      = Column(DateTime, nullable=True)

    status              = Column(String(20), default="ACTIVE")
    created_at          = Column(DateTime, default=datetime.utcnow)
    updated_at          = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="municipal_consumers")

    __table_args__ = (
        Index("idx_muni_property_id", "property_id"),
        Index("idx_muni_ward",        "ward_number"),
    )


# ─── Payment Profile ─────────────────────────────────────────────────────────

class PaymentProfile(Base):
    """Gateway customer IDs — one per user."""
    __tablename__ = "payment_profiles"

    id                   = Column(String(200), primary_key=True)
    user_id              = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True, index=True)
    portone_customer_id  = Column(String(200), unique=True, nullable=True)
    razorpay_customer_id = Column(String(200), nullable=True)
    name                 = Column(String(200), nullable=False)
    contact              = Column(String(20),  nullable=False)
    email                = Column(String(200), nullable=True)
    default_method       = Column(String(50),  nullable=True)
    preferred_gateway    = Column(String(50),  default="portone")
    is_default           = Column(Boolean,     default=True)
    created_at           = Column(DateTime, default=datetime.utcnow)
    updated_at           = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="payment_profile")

    __table_args__ = (
        Index("idx_pp_portone_id", "portone_customer_id"),
    )


# ─── Payments ─────────────────────────────────────────────────────────────────

class Payment(Base):
    """Every payment attempt across all departments."""
    __tablename__ = "payments"

    id                 = Column(String(200), primary_key=True)
    user_id            = Column(String(200), nullable=False, index=True)
    bill_id            = Column(String(100), nullable=False)
    department         = Column(String(50),  nullable=False, index=True)  # electricity|water|municipal

    amount             = Column(Numeric(10, 2), nullable=False)
    currency           = Column(String(3),   default="INR")

    gateway            = Column(String(50),  nullable=False)   # portone|razorpay|mock
    gateway_payment_id = Column(String(200), nullable=True)
    gateway_order_id   = Column(String(200), nullable=True, index=True)
    gateway_status     = Column(String(50),  nullable=True)

    payment_method     = Column(String(50),  nullable=True)    # upi|card|netbanking
    consumer_number    = Column(String(100), nullable=True)
    billing_period     = Column(String(20),  nullable=True)    # YYYY-MM or YYYY for annual tax

    reference_no       = Column(String(100), unique=True, nullable=True)
    status             = Column(String(50),  nullable=False, default="pending", index=True)
    error_message      = Column(Text, nullable=True)

    created_at         = Column(DateTime, default=datetime.utcnow)
    updated_at         = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    paid_at            = Column(DateTime, nullable=True)

    metadata_          = Column("metadata", JSONB, default=dict)

    refunds            = relationship("Refund", back_populates="payment", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_pay_status",     "status"),
        Index("idx_pay_dept",       "department"),
        Index("idx_pay_created_at", "created_at"),
    )


# ─── Refunds ─────────────────────────────────────────────────────────────────

class Refund(Base):
    __tablename__ = "refunds"

    id                = Column(String(200), primary_key=True)
    payment_id        = Column(String(200), ForeignKey("payments.id"), nullable=False, index=True)
    amount            = Column(Numeric(10, 2), nullable=False)
    reason            = Column(Text, nullable=True)
    gateway_refund_id = Column(String(200), nullable=True)
    status            = Column(String(50),  default="pending")
    created_at        = Column(DateTime, default=datetime.utcnow)

    payment = relationship("Payment", back_populates="refunds")


# ─── Kiosk Sessions ───────────────────────────────────────────────────────────

class KioskSession(Base):
    """
    One row per kiosk visitor interaction.

    Flow:
      1. Citizen enters name / phone / email  →  row created, is_verified=False
      2. OTP sent to phone                    →  otp_code stored (hashed in prod)
      3. Citizen enters OTP                   →  is_verified=True, otp_verified_at set
      4. Razorpay customer created            →  razorpay_customer_id stored
      5. Session token issued                 →  session_token stored
      6. Citizen taps Done/Exit               →  ended_at set

    Returning visitor (same phone):
      - Existing row looked up by phone_number
      - razorpay_customer_id reused
      - New session_token issued, ended_at reset
    """
    __tablename__ = "kiosk_sessions"

    id                   = Column(Integer,      primary_key=True, index=True)

    # Identity
    full_name            = Column(String(255),  nullable=False)
    phone_number         = Column(String(20),   nullable=False, index=True)
    email                = Column(String(255),  nullable=True)

    # OTP verification
    otp_code             = Column(String(10),   nullable=True)   # store hashed in production
    otp_sent_at          = Column(DateTime,     nullable=True)
    otp_verified_at      = Column(DateTime,     nullable=True)
    otp_attempts         = Column(Integer,      default=0)
    is_verified          = Column(Boolean,      default=False)

    # Razorpay — created once, reused on return visits
    razorpay_customer_id = Column(String(200),  nullable=True, index=True)

    # Session token — issued after OTP success, used to auth subsequent kiosk calls
    session_token        = Column(String(200),  nullable=True, unique=True, index=True)
    session_expires_at   = Column(DateTime,     nullable=True)

    # Lifecycle
    is_returning_user    = Column(Boolean,      default=False)
    started_at           = Column(DateTime,     default=datetime.utcnow)
    ended_at             = Column(DateTime,     nullable=True)   # set when user taps Done/Exit

    # Which kiosk terminal (useful when multiple kiosks deployed)
    kiosk_id             = Column(String(100),  nullable=True)

    __table_args__ = (
        Index("idx_ks_phone",     "phone_number"),
        Index("idx_ks_token",     "session_token"),
        Index("idx_ks_started",   "started_at"),
    )


# ─── Kiosk Config ─────────────────────────────────────────────────────────────

class KioskConfig(Base):
    """
    Per-department Razorpay credentials and global kiosk settings.

    One row per department (electricity / water / municipal).
    One extra row with department='global' for kiosk-wide settings.

    Razorpay keys are stored encrypted at rest in production.
    The hint columns (last 4 chars) are safe to return to the UI.

    Global settings JSON shape (department='global'):
    {
        "kiosk_name":        "SUVIDHA Kiosk — Ward 5",
        "kiosk_location":    "Near Town Hall",
        "default_language":  "en",
        "otp_expiry_secs":   300,
        "session_ttl_secs":  1800,
        "support_phone":     "1800-XXX-XXXX"
    }
    """
    __tablename__ = "kiosk_config"

    id                    = Column(Integer,     primary_key=True, index=True)

    # 'electricity' | 'water' | 'municipal' | 'global'
    department            = Column(String(50),  nullable=False, unique=True, index=True)

    # Razorpay credentials for this department
    # Store full value server-side; only hint is returned to frontend
    razorpay_key_id       = Column(String(200), nullable=True)
    razorpay_key_secret   = Column(Text,        nullable=True)   # encrypted in prod
    razorpay_key_id_hint  = Column(String(10),  nullable=True)   # last 4 chars, safe to show
    razorpay_mode         = Column(String(10),  default="test")  # 'test' | 'live'

    # Whether this department is currently active on the kiosk
    is_active             = Column(Boolean,     default=True)

    # Freeform JSON for any extra per-department or global settings
    settings              = Column(JSONB,       default=dict)

    configured_by_admin   = Column(Integer,     ForeignKey("admins.id"), nullable=True)
    created_at            = Column(DateTime,    default=datetime.utcnow)
    updated_at            = Column(DateTime,    default=datetime.utcnow, onupdate=datetime.utcnow)

    admin = relationship("Admin")

    __table_args__ = (
        Index("idx_kc_department", "department"),
    )
