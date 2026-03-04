# src/database/models.py
"""
Database Models
SQLAlchemy ORM models for KOISK application
"""

from sqlalchemy import Column, Integer, String, DateTime, Boolean, Float, ForeignKey, Text, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from passlib.context import CryptContext

Base = declarative_base()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class User(Base):
    """User model for authentication"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    full_name = Column(String(255), nullable=False)
    hashed_password = Column(String(255), nullable=False)
    
    # Profile
    phone_number = Column(String(20), nullable=True)
    address = Column(Text, nullable=True)
    city = Column(String(100), nullable=True)
    state = Column(String(100), nullable=True)
    postal_code = Column(String(10), nullable=True)
    
    # Status
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    email_verified = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)
    
    # OAuth
    google_id = Column(String(255), nullable=True, unique=True)
    
    # Relationships
    service_requests = relationship("ServiceRequest", back_populates="user", cascade="all, delete-orphan")
    electricity_meters = relationship("ElectricityMeter", back_populates="user", cascade="all, delete-orphan")
    water_consumers = relationship("WaterConsumer", back_populates="user", cascade="all, delete-orphan")
    gas_consumers = relationship("GasConsumer", back_populates="user", cascade="all, delete-orphan")

    def set_password(self, password: str):
        """Hash and set password"""
        self.hashed_password = pwd_context.hash(password)

    def verify_password(self, password: str) -> bool:
        """Verify password"""
        return pwd_context.verify(password, self.hashed_password)


class ServiceRequest(Base):
    """Service request model"""
    __tablename__ = "service_requests"

    id = Column(Integer, primary_key=True, index=True)
    service_request_id = Column(String(50), unique=True, index=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Service details
    service_type = Column(String(50), nullable=False)  # ELECTRICITY_PAY_BILL, WATER_LEAK_COMPLAINT, etc
    status = Column(String(20), default="DRAFT")  # DRAFT, SUBMITTED, ACKNOWLEDGED, PENDING, APPROVED, IN_PROGRESS, DELIVERED, FAILED, CANCELLED
    
    # Request data
    payload = Column(Text, nullable=True)  # JSON string
    correlation_id = Column(String(100), nullable=True)
    
    # Error handling
    error_code = Column(String(50), nullable=True)
    error_message = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="service_requests")


class ElectricityMeter(Base):
    """Electricity meter model"""
    __tablename__ = "electricity_meters"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    meter_number = Column(String(50), unique=True, index=True, nullable=False)
    
    # Meter details
    meter_type = Column(String(50), nullable=True)  # Single phase, Three phase, etc
    status = Column(String(20), default="ACTIVE")  # ACTIVE, INACTIVE, FAULTY
    load_requirement = Column(Float, nullable=True)  # in kW
    
    # Billing
    monthly_bill = Column(Float, default=0.0)
    outstanding_amount = Column(Float, default=0.0)
    last_reading = Column(Float, nullable=True)
    last_reading_date = Column(DateTime, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="electricity_meters")


class WaterConsumer(Base):
    """Water consumer model"""
    __tablename__ = "water_consumers"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    consumer_number = Column(String(50), unique=True, index=True, nullable=False)
    
    # Consumer details
    property_type = Column(String(50), nullable=True)  # Residential, Commercial
    status = Column(String(20), default="ACTIVE")  # ACTIVE, INACTIVE, SUSPENDED
    
    # Billing
    monthly_bill = Column(Float, default=0.0)
    outstanding_amount = Column(Float, default=0.0)
    last_reading = Column(Float, nullable=True)
    last_reading_date = Column(DateTime, nullable=True)
    usage_limit = Column(Float, nullable=True)  # in cubic meters
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="water_consumers")


class GasConsumer(Base):
    """Gas consumer model"""
    __tablename__ = "gas_consumers"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    consumer_number = Column(String(50), unique=True, index=True, nullable=False)
    
    # Consumer details
    connection_type = Column(String(50), nullable=True)  # Domestic, Commercial
    status = Column(String(20), default="ACTIVE")  # ACTIVE, INACTIVE, SUSPENDED
    
    # Billing
    monthly_bill = Column(Float, default=0.0)
    outstanding_amount = Column(Float, default=0.0)
    last_reading = Column(Float, nullable=True)
    last_reading_date = Column(DateTime, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="gas_consumers")


class PaymentHistory(Base):
    """Payment history model"""
    __tablename__ = "payment_history"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    service_request_id = Column(Integer, ForeignKey("service_requests.id"), nullable=True)
    
    # Payment details
    service_type = Column(String(50), nullable=False)  # electricity, water, gas
    amount = Column(Float, nullable=False)
    payment_method = Column(String(50), nullable=False)  # UPI, Card, NetBanking, etc
    payment_status = Column(String(20), default="PENDING")  # PENDING, SUCCESS, FAILED
    
    # Reference
    transaction_id = Column(String(100), nullable=True)
    reference_number = Column(String(100), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)


# Create all tables
def init_db(engine):
    """Initialize database tables"""
    Base.metadata.create_all(bind=engine)
