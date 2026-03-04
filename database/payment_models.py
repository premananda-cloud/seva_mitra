"""
project/database/payment_models.py
=====================================
SQLAlchemy ORM models for the payment tables specified in Section 3
of KOISK_Payment_Requirements.md.

Add to database/models.py:
  from database.payment_models import PaymentProfile, Payment, Refund
  (or paste the classes directly into models.py)

Also run payment_migrations.sql to create the tables in PostgreSQL.
"""

from sqlalchemy import (
    Column, String, Numeric, Boolean, DateTime, Text,
    ForeignKey, Index
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()   # reuse the same Base from models.py in practice


class PaymentProfile(Base):
    """
    One row per KOISK user — stores their gateway customer IDs.
    Created on first payment attempt (Section 1.3, Option A).
    """
    __tablename__ = "payment_profiles"

    # id == user.id — makes lookups O(1) by primary key
    id                   = Column(String(200), primary_key=True)
    user_id              = Column(String(200), nullable=False, index=True)

    portone_customer_id  = Column(String(200), unique=True, nullable=True)
    razorpay_customer_id = Column(String(200), nullable=True)

    # Snapshot of user fields at registration time
    name                 = Column(String(200), nullable=False)
    contact              = Column(String(20),  nullable=False)   # +91XXXXXXXXXX
    email                = Column(String(200), nullable=True)

    default_method       = Column(String(50),  nullable=True)    # upi | card | netbanking
    preferred_gateway    = Column(String(50),  default="portone")
    is_default           = Column(Boolean,     default=True)

    created_at           = Column(DateTime, default=datetime.utcnow)
    updated_at           = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index("idx_pp_user_id",    "user_id"),
        Index("idx_pp_portone_id", "portone_customer_id"),
    )


class Payment(Base):
    """
    Every payment attempt — pending through paid/failed.
    Status values match Section 3.3 exactly (lowercase strings).
    """
    __tablename__ = "payments"

    id                   = Column(String(200), primary_key=True, default=lambda: str(__import__('uuid').uuid4()))
    user_id              = Column(String(200), nullable=False)
    bill_id              = Column(String(100), nullable=False)
    department           = Column(String(50),  nullable=False)   # electricity | gas | water

    amount               = Column(Numeric(10, 2), nullable=False)
    currency             = Column(String(3),   default="INR")

    # Gateway fields
    gateway              = Column(String(50),  nullable=False)   # portone | razorpay | mock
    gateway_payment_id   = Column(String(200), nullable=True)
    gateway_order_id     = Column(String(200), nullable=True)
    gateway_status       = Column(String(50),  nullable=True)

    payment_method       = Column(String(50),  nullable=True)    # upi | card | netbanking
    consumer_number      = Column(String(100), nullable=True)
    billing_period       = Column(String(20),  nullable=True)    # YYYY-MM

    # Section 3.3 status strings
    reference_no         = Column(String(100), unique=True, nullable=True)
    status               = Column(String(50),  nullable=False, default="pending")
    # pending | paid | failed | refunded | offline_queued
    error_message        = Column(Text, nullable=True)

    created_at           = Column(DateTime, default=datetime.utcnow)
    updated_at           = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    paid_at              = Column(DateTime, nullable=True)

    metadata_            = Column("metadata", JSONB, default=dict)

    # Relationship to refunds
    refunds              = relationship("Refund", back_populates="payment",
                                        cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_pay_user_id",    "user_id"),
        Index("idx_pay_status",     "status"),
        Index("idx_pay_dept",       "department"),
        Index("idx_pay_created_at", "created_at"),
    )


class Refund(Base):
    """Refunds linked to a completed payment."""
    __tablename__ = "refunds"

    id                = Column(String(200), primary_key=True, default=lambda: str(__import__('uuid').uuid4()))
    payment_id        = Column(String(200), ForeignKey("payments.id"), nullable=False)
    amount            = Column(Numeric(10, 2), nullable=False)
    reason            = Column(Text, nullable=True)
    gateway_refund_id = Column(String(200), nullable=True)
    status            = Column(String(50),  default="pending")   # pending | processed | failed

    created_at        = Column(DateTime, default=datetime.utcnow)

    payment           = relationship("Payment", back_populates="refunds")

    __table_args__ = (
        Index("idx_refunds_payment_id", "payment_id"),
    )
