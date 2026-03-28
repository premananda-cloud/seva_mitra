"""
SUVIDHA 2026 - Gas Services Module
====================================
Implements Service Transfer Framework for Gas Department Services
Follows Core Terms & Framework: ServiceRequest as state machine

Author: SUVIDHA Team
Version: 1.0
"""

from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from uuid import uuid4
from decimal import Decimal
import logging
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ============================================================================
# 1. ENUMS & CONSTANTS
# ============================================================================

class ServiceStatus(Enum):
    """Canonical status set - Global across all services"""
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


class ServiceType(Enum):
    """Gas-specific service types"""
    GAS_PAY_BILL            = "GAS_PAY_BILL"
    GAS_CONNECTION_REQUEST  = "GAS_CONNECTION_REQUEST"
    GAS_SAFETY_COMPLAINT    = "GAS_SAFETY_COMPLAINT"
    GAS_METER_ISSUE         = "GAS_METER_ISSUE"
    GAS_COMPLAINT_GRIEVANCE = "GAS_COMPLAINT_GRIEVANCE"


class ActorRole(Enum):
    END_USER            = "END_USER"
    DEPARTMENT_OFFICER  = "DEPARTMENT_OFFICER"
    AUTOMATED_SYSTEM    = "AUTOMATED_SYSTEM"


class OwnershipType(Enum):
    USER       = "USER"
    SYSTEM     = "SYSTEM"
    DEPARTMENT = "DEPARTMENT"


class ErrorCode(Enum):
    # User Errors
    INVALID_DATA   = "INVALID_DATA"
    UNAUTHORIZED   = "UNAUTHORIZED"
    CONFLICT       = "CONFLICT"

    # System Errors
    DEPARTMENT_TIMEOUT   = "DEPARTMENT_TIMEOUT"
    INTEGRATION_FAILURE  = "INTEGRATION_FAILURE"
    INTERNAL_ERROR       = "INTERNAL_ERROR"

    # Consumer/Account Errors
    CONSUMER_NOT_FOUND   = "CONSUMER_NOT_FOUND"
    ACCOUNT_INACTIVE     = "ACCOUNT_INACTIVE"
    BILL_NOT_FOUND       = "BILL_NOT_FOUND"
    INSUFFICIENT_AMOUNT  = "INSUFFICIENT_AMOUNT"
    PAYMENT_FAILED       = "PAYMENT_FAILED"
    DUPLICATE_PAYMENT    = "DUPLICATE_PAYMENT"

    # Connection Errors
    OUT_OF_SERVICE_AREA  = "OUT_OF_SERVICE_AREA"
    EXISTING_CONNECTION  = "EXISTING_CONNECTION"
    DOCUMENT_INVALID     = "DOCUMENT_INVALID"
    APPLICANT_UNVERIFIED = "APPLICANT_UNVERIFIED"
    CAPACITY_LIMIT       = "CAPACITY_LIMIT"

    # Safety / Meter Errors
    METER_NOT_FOUND     = "METER_NOT_FOUND"
    SAFETY_ESCALATED    = "SAFETY_ESCALATED"


# ============================================================================
# 2. DATA MODELS
# ============================================================================

@dataclass
class GasConsumerRecord:
    """In-memory representation of a gas consumer"""
    consumer_id:        str
    consumer_number:    str
    full_name:          str
    address:            str
    phone:              str
    connection_type:    str          # domestic | commercial
    status:             str          # ACTIVE | INACTIVE | SUSPENDED
    outstanding_amount: Decimal      = Decimal("0.00")
    monthly_bill:       Decimal      = Decimal("0.00")
    billing_period:     str          = ""
    meter_number:       Optional[str] = None
    created_at:         datetime     = field(default_factory=datetime.utcnow)
    updated_at:         datetime     = field(default_factory=datetime.utcnow)


@dataclass
class ServiceRequest:
    """State-machine service request — mirrors DB ServiceRequest"""
    service_request_id: str
    service_type:       ServiceType
    status:             ServiceStatus
    consumer_id:        str
    department:         str          = "gas"
    payload:            Dict[str, Any] = field(default_factory=dict)
    payment_id:         Optional[str]  = None
    error_code:         Optional[ErrorCode] = None
    error_message:      Optional[str]  = None
    created_at:         datetime       = field(default_factory=datetime.utcnow)
    updated_at:         datetime       = field(default_factory=datetime.utcnow)
    completed_at:       Optional[datetime] = None
    audit_trail:        List[Dict]     = field(default_factory=list)

    def transition(self, new_status: ServiceStatus, actor: ActorRole, note: str = "") -> None:
        old = self.status
        self.status     = new_status
        self.updated_at = datetime.utcnow()
        self.audit_trail.append({
            "from":      old.value,
            "to":        new_status.value,
            "actor":     actor.value,
            "note":      note,
            "timestamp": self.updated_at.isoformat(),
        })
        logger.info(f"[GasService] {self.service_request_id} | {old.value} → {new_status.value} | {note}")


# ============================================================================
# 3. SERVICE HANDLERS
# ============================================================================

class GasBillPaymentService:
    """Handle gas bill payment flow"""

    def initiate(self, consumer: GasConsumerRecord, amount: Decimal,
                 payment_method: str) -> ServiceRequest:
        req = ServiceRequest(
            service_request_id = str(uuid4()),
            service_type       = ServiceType.GAS_PAY_BILL,
            status             = ServiceStatus.DRAFT,
            consumer_id        = consumer.consumer_id,
            payload            = {
                "consumer_number": consumer.consumer_number,
                "amount":          str(amount),
                "billing_period":  consumer.billing_period,
                "payment_method":  payment_method,
            },
        )
        req.transition(ServiceStatus.SUBMITTED, ActorRole.END_USER, "Payment initiated")
        return req

    def complete(self, req: ServiceRequest, payment_id: str) -> ServiceRequest:
        req.payment_id = payment_id
        req.transition(ServiceStatus.DELIVERED, ActorRole.AUTOMATED_SYSTEM, "Payment confirmed")
        req.completed_at = datetime.utcnow()
        return req

    def fail(self, req: ServiceRequest, code: ErrorCode, msg: str) -> ServiceRequest:
        req.error_code    = code
        req.error_message = msg
        req.transition(ServiceStatus.FAILED, ActorRole.AUTOMATED_SYSTEM, msg)
        return req


class GasConnectionService:
    """Handle new gas connection applications"""

    # Expected turnaround by connection type
    SLA_DAYS = {"domestic": 15, "commercial": 30}

    def apply(self, applicant_name: str, applicant_id: str, address: str,
              connection_type: str, identity_proof: str,
              id_number: str) -> ServiceRequest:
        sla = self.SLA_DAYS.get(connection_type, 15)
        req = ServiceRequest(
            service_request_id = str(uuid4()),
            service_type       = ServiceType.GAS_CONNECTION_REQUEST,
            status             = ServiceStatus.DRAFT,
            consumer_id        = applicant_id,
            payload            = {
                "applicant_name":  applicant_name,
                "applicant_id":    applicant_id,
                "address":         address,
                "connection_type": connection_type,
                "identity_proof":  identity_proof,
                "id_number":       id_number,
                "expected_by":     (datetime.utcnow() + timedelta(days=sla)).date().isoformat(),
            },
        )
        req.transition(ServiceStatus.SUBMITTED, ActorRole.END_USER,
                       f"New {connection_type} connection request submitted")
        return req


class GasSafetyComplaintService:
    """Handle gas leak and safety complaints — highest priority flow"""

    # Issue severity escalation mapping
    CRITICAL_TYPES = {"leak"}

    def report(self, consumer_id: str, consumer_no: str, issue_type: str,
               location: str, description: str, phone: str) -> ServiceRequest:
        is_critical = issue_type in self.CRITICAL_TYPES
        req = ServiceRequest(
            service_request_id = str(uuid4()),
            service_type       = ServiceType.GAS_SAFETY_COMPLAINT,
            status             = ServiceStatus.DRAFT,
            consumer_id        = consumer_id,
            payload            = {
                "consumer_number": consumer_no,
                "issue_type":      issue_type,
                "location":        location,
                "description":     description,
                "phone":           phone,
                "is_critical":     is_critical,
                "emergency_ref":   f"EMG-GAS-{uuid4().hex[:8].upper()}" if is_critical else None,
            },
        )

        if is_critical:
            # Critical: skip SUBMITTED → go straight to IN_PROGRESS for immediate dispatch
            req.transition(ServiceStatus.SUBMITTED,   ActorRole.END_USER,      "Safety complaint logged")
            req.transition(ServiceStatus.IN_PROGRESS, ActorRole.AUTOMATED_SYSTEM,
                           "CRITICAL: Gas leak — emergency team dispatched")
        else:
            req.transition(ServiceStatus.SUBMITTED, ActorRole.END_USER, "Safety complaint submitted")

        return req
