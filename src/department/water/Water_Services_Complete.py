"""
SUVIDHA 2026 - Water Services Module
====================================
Implements Service Transfer Framework for Water Department Services
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

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ============================================================================
# 1. ENUMS & CONSTANTS
# ============================================================================

class ServiceStatus(Enum):
    """Canonical status set - Global across all services"""
    DRAFT = "DRAFT"
    SUBMITTED = "SUBMITTED"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    DENIED = "DENIED"
    IN_PROGRESS = "IN_PROGRESS"
    DELIVERED = "DELIVERED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class ServiceType(Enum):
    """Water-specific service types"""
    WATER_PAY_BILL = "WATER_PAY_BILL"
    WATER_CONNECTION_REQUEST = "WATER_CONNECTION_REQUEST"
    WATER_METER_CHANGE = "WATER_METER_CHANGE"
    WATER_LEAK_COMPLAINT = "WATER_LEAK_COMPLAINT"
    WATER_METER_READING_SUBMISSION = "WATER_METER_READING_SUBMISSION"
    WATER_COMPLAINT_GRIEVANCE = "WATER_COMPLAINT_GRIEVANCE"


class ActorRole(Enum):
    """Actor roles in the service request"""
    END_USER = "END_USER"
    DEPARTMENT_OFFICER = "DEPARTMENT_OFFICER"
    AUTOMATED_SYSTEM = "AUTOMATED_SYSTEM"


class OwnershipType(Enum):
    """Service request ownership at any point"""
    USER = "USER"
    SYSTEM = "SYSTEM"
    DEPARTMENT = "DEPARTMENT"


class ErrorCode(Enum):
    """Error codes for water service failures"""
    # User Errors
    INVALID_DATA = "INVALID_DATA"
    UNAUTHORIZED = "UNAUTHORIZED"
    CONFLICT = "CONFLICT"
    
    # System Errors
    DEPARTMENT_TIMEOUT = "DEPARTMENT_TIMEOUT"
    INTEGRATION_FAILURE = "INTEGRATION_FAILURE"
    INTERNAL_ERROR = "INTERNAL_ERROR"
    
    # Consumer/Account Errors
    CONSUMER_NOT_FOUND = "CONSUMER_NOT_FOUND"
    ACCOUNT_INACTIVE = "ACCOUNT_INACTIVE"
    BILL_NOT_FOUND = "BILL_NOT_FOUND"
    INSUFFICIENT_AMOUNT = "INSUFFICIENT_AMOUNT"
    PAYMENT_FAILED = "PAYMENT_FAILED"
    DUPLICATE_PAYMENT = "DUPLICATE_PAYMENT"
    
    # Connection Errors
    OUT_OF_SERVICE_AREA = "OUT_OF_SERVICE_AREA"
    EXISTING_CONNECTION = "EXISTING_CONNECTION"
    DOCUMENT_INVALID = "DOCUMENT_INVALID"
    APPLICANT_UNVERIFIED = "APPLICANT_UNVERIFIED"
    CAPACITY_LIMIT = "CAPACITY_LIMIT"
    
    # Meter Errors
    METER_NOT_FOUND = "METER_NOT_FOUND"
    METER_LOCKED = "METER_LOCKED"
    METER_MISMATCH = "METER_MISMATCH"
    INSTALLATION_FAILED = "INSTALLATION_FAILED"
    CALIBRATION_FAILURE = "CALIBRATION_FAILURE"
    
    # Reading Errors
    READING_INVALID = "READING_INVALID"
    READING_BELOW_PREVIOUS = "READING_BELOW_PREVIOUS"
    PHOTO_UNCLEAR = "PHOTO_UNCLEAR"


class LeakSeverity(Enum):
    """Leak complaint severity levels"""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class LeakType(Enum):
    """Types of water leaks"""
    MINOR = "MINOR"
    MAJOR = "MAJOR"
    WATER_MAIN_BURST = "WATER_MAIN_BURST"
    PIPE_SEEPAGE = "PIPE_SEEPAGE"


class ComplaintCategory(Enum):
    """Water complaint categories"""
    WATER_QUALITY = "WATER_QUALITY"
    BILLING_ISSUE = "BILLING_ISSUE"
    SERVICE_INTERRUPTION = "SERVICE_INTERRUPTION"
    METER_ISSUE = "METER_ISSUE"
    PRESSURE_LOW = "PRESSURE_LOW"
    DISCONNECTION = "DISCONNECTION"
    OTHER = "OTHER"


class ConnectionType(Enum):
    """Water connection types"""
    DOMESTIC = "DOMESTIC"
    COMMERCIAL = "COMMERCIAL"
    INDUSTRIAL = "INDUSTRIAL"


# ============================================================================
# 2. DATA MODELS
# ============================================================================

@dataclass
class ServiceRequest:
    """
    Abstract ServiceRequest Model
    Core to all services - represents immutable intent with state-driven lifecycle
    """
    service_request_id: str = field(default_factory=lambda: str(uuid4()))
    service_type: ServiceType = None
    initiator_id: str = None
    beneficiary_id: str = None
    status: ServiceStatus = ServiceStatus.DRAFT
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    current_owner: OwnershipType = OwnershipType.USER
    correlation_id: str = None  # Department reference ID
    payload: Dict[str, Any] = field(default_factory=dict)
    status_history: List[Dict[str, Any]] = field(default_factory=list)
    error_code: Optional[ErrorCode] = None
    error_message: Optional[str] = None
    
    def __post_init__(self):
        """Initialize correlation_id if not provided"""
        if not self.correlation_id:
            self.correlation_id = f"{self.service_type.value}_{self.service_request_id[:8]}"
        self._add_status_history(self.status, "Service request created")
    
    def _add_status_history(self, status: ServiceStatus, reason: str, metadata: Dict = None):
        """Append-only status history - never overwrite"""
        history_entry = {
            "status": status.value,
            "timestamp": datetime.utcnow().isoformat(),
            "reason": reason,
            "metadata": metadata or {}
        }
        self.status_history.append(history_entry)
        logger.info(f"Status change: {self.service_request_id} → {status.value}: {reason}")
    
    def update_status(self, new_status: ServiceStatus, reason: str, 
                     new_owner: OwnershipType = None, metadata: Dict = None):
        """Transition to new status with validation"""
        if not self._is_valid_transition(self.status, new_status):
            raise ValueError(f"Invalid transition: {self.status.value} → {new_status.value}")
        
        self.status = new_status
        self.updated_at = datetime.utcnow()
        if new_owner:
            self.current_owner = new_owner
        self._add_status_history(new_status, reason, metadata)
    
    @staticmethod
    def _is_valid_transition(from_status: ServiceStatus, to_status: ServiceStatus) -> bool:
        """Validate state machine transitions"""
        valid_transitions = {
            ServiceStatus.DRAFT: [ServiceStatus.SUBMITTED, ServiceStatus.CANCELLED],
            ServiceStatus.SUBMITTED: [ServiceStatus.ACKNOWLEDGED, ServiceStatus.DENIED],
            ServiceStatus.ACKNOWLEDGED: [ServiceStatus.PENDING, ServiceStatus.DENIED],
            ServiceStatus.PENDING: [ServiceStatus.APPROVED, ServiceStatus.DENIED],
            ServiceStatus.APPROVED: [ServiceStatus.IN_PROGRESS, ServiceStatus.CANCELLED],
            ServiceStatus.IN_PROGRESS: [ServiceStatus.DELIVERED, ServiceStatus.FAILED],
            ServiceStatus.DELIVERED: [],  # Terminal state
            ServiceStatus.DENIED: [],  # Terminal state
            ServiceStatus.FAILED: [ServiceStatus.IN_PROGRESS],  # Can retry
            ServiceStatus.CANCELLED: [],  # Terminal state
        }
        return to_status in valid_transitions.get(from_status, [])
    
    def get_visible_status(self, viewer_role: ActorRole) -> ServiceStatus:
        """Status visibility rules based on actor role"""
        if viewer_role == ActorRole.DEPARTMENT_OFFICER:
            return self.status if self.status != ServiceStatus.DRAFT else None
        elif viewer_role == ActorRole.END_USER:
            return self.status
        else:  # AUTOMATED_SYSTEM
            return self.status
    
    def to_dict(self, include_history: bool = False) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        data = {
            "service_request_id": self.service_request_id,
            "service_type": self.service_type.value,
            "initiator_id": self.initiator_id,
            "beneficiary_id": self.beneficiary_id,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "current_owner": self.current_owner.value,
            "correlation_id": self.correlation_id,
            "payload": self.payload,
            "error_code": self.error_code.value if self.error_code else None,
            "error_message": self.error_message,
        }
        if include_history:
            data["status_history"] = self.status_history
        return data


# ============================================================================
# 3. SERVICE IMPLEMENTATIONS
# ============================================================================

class WaterPayBillService:
    """
    Water Bill Payment Service
    Handles payment of outstanding water dues
    """
    
    def __init__(self, db_service=None, payment_gateway=None):
        self.db_service = db_service
        self.payment_gateway = payment_gateway
    
    def create_pay_bill_request(self, consumer_number: str, customer_id: str,
                                billing_period: str, amount: Decimal,
                                payment_method: str) -> ServiceRequest:
        """Create a water bill payment request"""
        
        request = ServiceRequest(
            service_type=ServiceType.WATER_PAY_BILL,
            initiator_id=customer_id,
            beneficiary_id=customer_id
        )
        
        request.payload = {
            "consumer_number": consumer_number,
            "billing_period": billing_period,
            "amount": str(amount),
            "payment_method": payment_method,
            "created_timestamp": datetime.utcnow().isoformat()
        }
        
        logger.info(f"Created bill payment request for consumer {consumer_number}")
        return request
    
    def submit_payment(self, request: ServiceRequest) -> ServiceRequest:
        """Submit payment for processing"""
        if request.status != ServiceStatus.DRAFT:
            raise ValueError(f"Cannot submit request in {request.status} state")
        
        # Validate consumer account
        consumer_number = request.payload.get("consumer_number")
        if not self._consumer_exists(consumer_number):
            request.error_code = ErrorCode.CONSUMER_NOT_FOUND
            request.error_message = f"Consumer account {consumer_number} not found"
            request.update_status(ServiceStatus.DENIED, "Consumer account not found")
            return request
        
        if not self._account_active(consumer_number):
            request.error_code = ErrorCode.ACCOUNT_INACTIVE
            request.error_message = "Account is inactive/suspended"
            request.update_status(ServiceStatus.DENIED, "Account is not active")
            return request
        
        # Check if bill exists
        billing_period = request.payload.get("billing_period")
        if not self._bill_exists(consumer_number, billing_period):
            request.error_code = ErrorCode.BILL_NOT_FOUND
            request.error_message = f"No bill found for period {billing_period}"
            request.update_status(ServiceStatus.DENIED, "Bill not found for given period")
            return request
        
        request.update_status(
            ServiceStatus.SUBMITTED,
            "Payment submitted for processing",
            OwnershipType.SYSTEM
        )
        return request
    
    def process_payment(self, request: ServiceRequest) -> ServiceRequest:
        """Process the payment through gateway"""
        if request.status != ServiceStatus.SUBMITTED:
            raise ValueError(f"Cannot process payment in {request.status} state")
        
        request.update_status(
            ServiceStatus.ACKNOWLEDGED,
            "Payment request acknowledged by system",
            OwnershipType.SYSTEM
        )
        
        # Call payment gateway
        amount = Decimal(request.payload.get("amount"))
        payment_method = request.payload.get("payment_method")
        
        try:
            payment_result = self._gateway_payment(amount, payment_method)
            
            if payment_result["success"]:
                request.payload["payment_reference"] = payment_result["transaction_id"]
                request.payload["payment_timestamp"] = datetime.utcnow().isoformat()
                
                request.update_status(
                    ServiceStatus.DELIVERED,
                    "Payment successful",
                    OwnershipType.SYSTEM,
                    {"transaction_id": payment_result["transaction_id"]}
                )
            else:
                request.error_code = ErrorCode.PAYMENT_FAILED
                request.error_message = payment_result.get("error", "Payment gateway error")
                request.update_status(
                    ServiceStatus.FAILED,
                    "Payment processing failed",
                    OwnershipType.SYSTEM
                )
        except Exception as e:
            logger.error(f"Payment processing error: {str(e)}")
            request.error_code = ErrorCode.INTEGRATION_FAILURE
            request.error_message = str(e)
            request.update_status(ServiceStatus.FAILED, "Payment gateway timeout")
        
        return request
    
    def generate_receipt(self, request: ServiceRequest) -> Dict[str, Any]:
        """Generate payment receipt"""
        if request.status != ServiceStatus.DELIVERED:
            return None
        
        receipt_number = f"WATER_RECEIPT_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        
        return {
            "receipt_number": receipt_number,
            "consumer_number": request.payload.get("consumer_number"),
            "amount_paid": request.payload.get("amount"),
            "billing_period": request.payload.get("billing_period"),
            "payment_method": request.payload.get("payment_method"),
            "transaction_id": request.payload.get("payment_reference"),
            "timestamp": request.payload.get("payment_timestamp"),
            "status": "PAID"
        }
    
    # Helper methods
    def _consumer_exists(self, consumer_number: str) -> bool:
        """Check if consumer exists in database"""
        # In production, query actual database
        return True
    
    def _account_active(self, consumer_number: str) -> bool:
        """Check if consumer account is active"""
        # In production, query actual database
        return True
    
    def _bill_exists(self, consumer_number: str, billing_period: str) -> bool:
        """Check if bill exists for given period"""
        # In production, query actual database
        return True
    
    def _gateway_payment(self, amount: Decimal, method: str) -> Dict[str, Any]:
        """Simulate payment gateway call"""
        return {
            "success": True,
            "transaction_id": f"TXN_{uuid4().hex[:12].upper()}",
            "amount": str(amount)
        }


class WaterConnectionRequestService:
    """
    Water New Connection Request Service
    Handles requests for new water supply connections
    """
    
    def __init__(self, db_service=None):
        self.db_service = db_service
    
    def create_connection_request(self, applicant_id: str, applicant_name: str,
                                 phone_number: str, email: str, address: str,
                                 connection_type: ConnectionType,
                                 load_requirement: int) -> ServiceRequest:
        """Create a new water connection request"""
        
        request = ServiceRequest(
            service_type=ServiceType.WATER_CONNECTION_REQUEST,
            initiator_id=applicant_id,
            beneficiary_id=applicant_id
        )
        
        request.payload = {
            "applicant_id": applicant_id,
            "applicant_name": applicant_name,
            "phone_number": phone_number,
            "email": email,
            "address": address,
            "connection_type": connection_type.value,
            "load_requirement": load_requirement,
            "created_timestamp": datetime.utcnow().isoformat()
        }
        
        logger.info(f"Created connection request for {applicant_name} at {address}")
        return request
    
    def submit_connection_request(self, request: ServiceRequest) -> ServiceRequest:
        """Submit connection request for processing"""
        if request.status != ServiceStatus.DRAFT:
            raise ValueError(f"Cannot submit request in {request.status} state")
        
        address = request.payload.get("address")
        applicant_id = request.payload.get("applicant_id")
        
        # Validate address in service area
        if not self._address_in_service_area(address):
            request.error_code = ErrorCode.OUT_OF_SERVICE_AREA
            request.error_message = "Property is outside service area"
            request.update_status(ServiceStatus.DENIED, "Address out of service area")
            return request
        
        # Check for existing connection
        if self._existing_connection_exists(address):
            request.error_code = ErrorCode.EXISTING_CONNECTION
            request.error_message = "Active connection already exists for this property"
            request.update_status(ServiceStatus.DENIED, "Existing connection found")
            return request
        
        request.update_status(
            ServiceStatus.SUBMITTED,
            "Connection request submitted",
            OwnershipType.SYSTEM
        )
        return request
    
    def acknowledge_request(self, request: ServiceRequest) -> ServiceRequest:
        """Acknowledge connection request and assign for inspection"""
        if request.status != ServiceStatus.SUBMITTED:
            raise ValueError(f"Cannot acknowledge in {request.status} state")
        
        request.update_status(
            ServiceStatus.ACKNOWLEDGED,
            "Connection request acknowledged",
            OwnershipType.DEPARTMENT,
            {"assigned_date": datetime.utcnow().isoformat()}
        )
        return request
    
    def schedule_inspection(self, request: ServiceRequest) -> ServiceRequest:
        """Schedule inspection for connection"""
        if request.status != ServiceStatus.ACKNOWLEDGED:
            raise ValueError(f"Cannot schedule inspection in {request.status} state")
        
        inspection_date = datetime.utcnow() + timedelta(days=3)
        
        request.update_status(
            ServiceStatus.PENDING,
            "Inspection scheduled",
            OwnershipType.DEPARTMENT,
            {"inspection_date": inspection_date.isoformat()}
        )
        return request
    
    def approve_connection(self, request: ServiceRequest, officer_id: str) -> ServiceRequest:
        """Approve connection request after inspection"""
        if request.status != ServiceStatus.PENDING:
            raise ValueError(f"Cannot approve in {request.status} state")
        
        request.update_status(
            ServiceStatus.APPROVED,
            "Connection approved after inspection",
            OwnershipType.DEPARTMENT,
            {"approved_by": officer_id, "approved_date": datetime.utcnow().isoformat()}
        )
        return request
    
    def activate_connection(self, request: ServiceRequest) -> ServiceRequest:
        """Activate the water connection"""
        if request.status != ServiceStatus.APPROVED:
            raise ValueError(f"Cannot activate in {request.status} state")
        
        # Generate consumer number and connection number
        consumer_number = f"WTR{uuid4().hex[:9].upper()}"
        connection_number = f"WC_{datetime.utcnow().strftime('%Y')}_{uuid4().hex[:5].upper()}"
        meter_number = f"MTR_WTR_{uuid4().hex[:6].upper()}"
        
        request.payload["consumer_number"] = consumer_number
        request.payload["connection_number"] = connection_number
        request.payload["meter_number"] = meter_number
        request.payload["activation_date"] = datetime.utcnow().isoformat()
        
        request.update_status(
            ServiceStatus.IN_PROGRESS,
            "Connection activation in progress",
            OwnershipType.DEPARTMENT
        )
        
        # Simulate installation completion
        request.update_status(
            ServiceStatus.DELIVERED,
            "Connection activated and meter installed",
            OwnershipType.SYSTEM,
            {
                "meter_installed": True,
                "installation_date": datetime.utcnow().isoformat(),
                "first_billing_date": (datetime.utcnow() + timedelta(days=30)).isoformat()
            }
        )
        
        return request


class WaterMeterChangeService:
    """
    Water Meter Change Service
    Handles meter replacement or upgrade requests
    """
    
    def __init__(self, db_service=None):
        self.db_service = db_service
    
    def create_meter_change_request(self, consumer_number: str, old_meter_number: str,
                                    reason_code: str, reason_description: str) -> ServiceRequest:
        """Create a meter change request"""
        
        request = ServiceRequest(
            service_type=ServiceType.WATER_METER_CHANGE,
            initiator_id=consumer_number,
            beneficiary_id=consumer_number
        )
        
        request.payload = {
            "consumer_number": consumer_number,
            "old_meter_number": old_meter_number,
            "reason_code": reason_code,
            "reason_description": reason_description,
            "created_timestamp": datetime.utcnow().isoformat()
        }
        
        logger.info(f"Created meter change request for consumer {consumer_number}")
        return request
    
    def submit_meter_change(self, request: ServiceRequest) -> ServiceRequest:
        """Submit meter change request"""
        if request.status != ServiceStatus.DRAFT:
            raise ValueError(f"Cannot submit in {request.status} state")
        
        consumer_number = request.payload.get("consumer_number")
        old_meter_number = request.payload.get("old_meter_number")
        
        if not self._meter_exists(old_meter_number):
            request.error_code = ErrorCode.METER_NOT_FOUND
            request.error_message = "Meter not found in system"
            request.update_status(ServiceStatus.DENIED, "Meter not found")
            return request
        
        if self._meter_has_pending_disputes(old_meter_number):
            request.error_code = ErrorCode.METER_LOCKED
            request.error_message = "Meter has pending disputes/non-payment"
            request.update_status(ServiceStatus.DENIED, "Meter locked")
            return request
        
        request.update_status(
            ServiceStatus.SUBMITTED,
            "Meter change request submitted",
            OwnershipType.SYSTEM
        )
        return request
    
    def approve_meter_change(self, request: ServiceRequest) -> ServiceRequest:
        """Approve and schedule meter change"""
        if request.status != ServiceStatus.SUBMITTED:
            raise ValueError(f"Cannot approve in {request.status} state")
        
        installation_date = datetime.utcnow() + timedelta(days=2)
        new_meter_number = f"MTR_WTR_{uuid4().hex[:6].upper()}"
        
        request.payload["new_meter_number"] = new_meter_number
        request.payload["installation_date"] = installation_date.isoformat()
        
        request.update_status(
            ServiceStatus.PENDING,
            "Meter change approved, installation scheduled",
            OwnershipType.DEPARTMENT
        )
        return request
    
    def complete_meter_change(self, request: ServiceRequest) -> ServiceRequest:
        """Complete meter installation"""
        if request.status != ServiceStatus.PENDING:
            raise ValueError(f"Cannot complete in {request.status} state")
        
        request.update_status(
            ServiceStatus.IN_PROGRESS,
            "Meter installation in progress",
            OwnershipType.DEPARTMENT
        )
        
        request.payload["final_reading_old_meter"] = 45230
        request.payload["opening_reading_new_meter"] = 0
        
        request.update_status(
            ServiceStatus.DELIVERED,
            "Meter change completed successfully",
            OwnershipType.SYSTEM,
            {"completed_date": datetime.utcnow().isoformat()}
        )
        
        return request
    
    # Helper methods
    def _meter_exists(self, meter_number: str) -> bool:
        return True
    
    def _meter_has_pending_disputes(self, meter_number: str) -> bool:
        return False


class WaterLeakComplaintService:
    """
    Water Leak Complaint Service
    Handles emergency leak reports and repairs
    """
    
    def __init__(self, db_service=None):
        self.db_service = db_service
    
    def create_leak_complaint(self, location_description: str, leak_type: LeakType,
                             severity: LeakSeverity, consumer_number: str = None,
                             affected_residents: int = 0) -> ServiceRequest:
        """Create a water leak complaint"""
        
        request = ServiceRequest(
            service_type=ServiceType.WATER_LEAK_COMPLAINT,
            initiator_id=consumer_number or "ANONYMOUS",
            beneficiary_id=consumer_number or "PUBLIC"
        )
        
        request.payload = {
            "consumer_number": consumer_number,
            "location_description": location_description,
            "leak_type": leak_type.value,
            "severity_level": severity.value,
            "affected_residents": affected_residents,
            "created_timestamp": datetime.utcnow().isoformat()
        }
        
        logger.info(f"Created leak complaint at {location_description}, severity: {severity.value}")
        return request
    
    def submit_leak_complaint(self, request: ServiceRequest) -> ServiceRequest:
        """Submit and acknowledge leak complaint"""
        if request.status != ServiceStatus.DRAFT:
            raise ValueError(f"Cannot submit in {request.status} state")
        
        request.update_status(
            ServiceStatus.SUBMITTED,
            "Leak complaint submitted",
            OwnershipType.SYSTEM
        )
        
        # Auto-acknowledge immediately
        request.update_status(
            ServiceStatus.ACKNOWLEDGED,
            "Leak complaint acknowledged, assigning to field team",
            OwnershipType.DEPARTMENT
        )
        
        return request
    
    def dispatch_field_team(self, request: ServiceRequest, team_id: str) -> ServiceRequest:
        """Dispatch field team to leak location"""
        if request.status != ServiceStatus.ACKNOWLEDGED:
            raise ValueError(f"Cannot dispatch in {request.status} state")
        
        severity = request.payload.get("severity_level")
        sla_hours = self._get_sla_hours(severity)
        
        dispatch_time = datetime.utcnow()
        arrival_estimate = dispatch_time + timedelta(hours=sla_hours)
        
        request.payload["assigned_team"] = team_id
        request.payload["dispatch_time"] = dispatch_time.isoformat()
        request.payload["estimated_arrival"] = arrival_estimate.isoformat()
        
        request.update_status(
            ServiceStatus.PENDING,
            f"Field team {team_id} dispatched",
            OwnershipType.DEPARTMENT
        )
        
        return request
    
    def mark_repair_started(self, request: ServiceRequest) -> ServiceRequest:
        """Mark repair work as started"""
        if request.status != ServiceStatus.PENDING:
            raise ValueError(f"Cannot start repair in {request.status} state")
        
        request.payload["repair_start_time"] = datetime.utcnow().isoformat()
        
        request.update_status(
            ServiceStatus.IN_PROGRESS,
            "Repair work started at site",
            OwnershipType.DEPARTMENT
        )
        
        return request
    
    def complete_repair(self, request: ServiceRequest, repair_description: str) -> ServiceRequest:
        """Complete leak repair"""
        if request.status != ServiceStatus.IN_PROGRESS:
            raise ValueError(f"Cannot complete in {request.status} state")
        
        request.payload["repair_completed_time"] = datetime.utcnow().isoformat()
        request.payload["repair_description"] = repair_description
        request.payload["pressure_test_result"] = "PASSED"
        
        request.update_status(
            ServiceStatus.DELIVERED,
            "Leak repair completed, pressure tested",
            OwnershipType.SYSTEM
        )
        
        return request
    
    # Helper methods
    def _get_sla_hours(self, severity: str) -> int:
        """Get SLA response time based on severity"""
        sla_map = {
            "CRITICAL": 2,
            "HIGH": 4,
            "MEDIUM": 8,
            "LOW": 24
        }
        return sla_map.get(severity, 24)


class WaterMeterReadingService:
    """
    Water Meter Reading Submission Service
    Handles customer meter reading submissions
    """
    
    def __init__(self, db_service=None):
        self.db_service = db_service
    
    def create_reading_submission(self, consumer_number: str, meter_number: str,
                                 billing_period: str, meter_reading: int) -> ServiceRequest:
        """Create a meter reading submission"""
        
        request = ServiceRequest(
            service_type=ServiceType.WATER_METER_READING_SUBMISSION,
            initiator_id=consumer_number,
            beneficiary_id=consumer_number
        )
        
        request.payload = {
            "consumer_number": consumer_number,
            "meter_number": meter_number,
            "billing_period": billing_period,
            "meter_reading": meter_reading,
            "reading_timestamp": datetime.utcnow().isoformat()
        }
        
        logger.info(f"Created meter reading submission for {consumer_number}")
        return request
    
    def submit_reading(self, request: ServiceRequest) -> ServiceRequest:
        """Submit meter reading for processing"""
        if request.status != ServiceStatus.DRAFT:
            raise ValueError(f"Cannot submit in {request.status} state")
        
        consumer_number = request.payload.get("consumer_number")
        reading = request.payload.get("meter_reading")
        
        # Get previous reading
        previous_reading = self._get_previous_reading(consumer_number)
        
        # Validate reading
        if reading < previous_reading:
            request.error_code = ErrorCode.READING_BELOW_PREVIOUS
            request.error_message = f"Reading {reading} is below previous {previous_reading}"
            request.update_status(ServiceStatus.DENIED, "Reading below previous reading")
            return request
        
        request.payload["previous_reading"] = previous_reading
        request.payload["consumption_units"] = reading - previous_reading
        
        request.update_status(
            ServiceStatus.SUBMITTED,
            "Meter reading submitted",
            OwnershipType.SYSTEM
        )
        
        return request
    
    def approve_reading(self, request: ServiceRequest) -> ServiceRequest:
        """Approve meter reading and trigger bill generation"""
        if request.status != ServiceStatus.SUBMITTED:
            raise ValueError(f"Cannot approve in {request.status} state")
        
        request.update_status(
            ServiceStatus.ACKNOWLEDGED,
            "Meter reading acknowledged",
            OwnershipType.SYSTEM
        )
        
        # Calculate bill
        consumption = request.payload.get("consumption_units")
        rate_per_unit = Decimal("12.00")
        fixed_charges = Decimal("50.00")
        calculated_bill = (consumption * rate_per_unit) + fixed_charges
        
        request.payload["rate_per_unit"] = str(rate_per_unit)
        request.payload["fixed_charges"] = str(fixed_charges)
        request.payload["calculated_bill"] = str(calculated_bill)
        request.payload["bill_number"] = f"WATER_BILL_{datetime.utcnow().strftime('%Y%m%d')}_{uuid4().hex[:5].upper()}"
        request.payload["due_date"] = (datetime.utcnow() + timedelta(days=15)).isoformat()
        
        request.update_status(
            ServiceStatus.IN_PROGRESS,
            "Bill calculation in progress",
            OwnershipType.SYSTEM
        )
        
        request.update_status(
            ServiceStatus.DELIVERED,
            "Bill generated based on submitted reading",
            OwnershipType.SYSTEM
        )
        
        return request
    
    # Helper methods
    def _get_previous_reading(self, consumer_number: str) -> int:
        return 45100  # Mock data


class WaterComplaintService:
    """
    Water Complaint & Grievance Service
    Handles complaints about water quality, billing, service, etc.
    """
    
    def __init__(self, db_service=None):
        self.db_service = db_service
    
    def create_complaint(self, consumer_number: str, category: ComplaintCategory,
                        subject: str, description: str, severity: str) -> ServiceRequest:
        """Create a complaint/grievance"""
        
        request = ServiceRequest(
            service_type=ServiceType.WATER_COMPLAINT_GRIEVANCE,
            initiator_id=consumer_number,
            beneficiary_id=consumer_number
        )
        
        request.payload = {
            "consumer_number": consumer_number,
            "complaint_category": category.value,
            "complaint_subject": subject,
            "complaint_description": description,
            "severity_level": severity,
            "created_timestamp": datetime.utcnow().isoformat()
        }
        
        logger.info(f"Created complaint for {consumer_number}: {subject}")
        return request
    
    def submit_complaint(self, request: ServiceRequest) -> ServiceRequest:
        """Submit complaint for processing"""
        if request.status != ServiceStatus.DRAFT:
            raise ValueError(f"Cannot submit in {request.status} state")
        
        request.update_status(
            ServiceStatus.SUBMITTED,
            "Complaint submitted",
            OwnershipType.SYSTEM
        )
        
        return request
    
    def assign_complaint(self, request: ServiceRequest, officer_id: str) -> ServiceRequest:
        """Assign complaint to department officer"""
        if request.status != ServiceStatus.SUBMITTED:
            raise ValueError(f"Cannot assign in {request.status} state")
        
        request.payload["assigned_officer"] = officer_id
        request.payload["assigned_date"] = datetime.utcnow().isoformat()
        
        request.update_status(
            ServiceStatus.ACKNOWLEDGED,
            f"Complaint assigned to officer {officer_id}",
            OwnershipType.DEPARTMENT
        )
        
        return request
    
    def start_investigation(self, request: ServiceRequest) -> ServiceRequest:
        """Start investigation into complaint"""
        if request.status != ServiceStatus.ACKNOWLEDGED:
            raise ValueError(f"Cannot start investigation in {request.status} state")
        
        request.payload["investigation_start"] = datetime.utcnow().isoformat()
        
        request.update_status(
            ServiceStatus.PENDING,
            "Investigation in progress",
            OwnershipType.DEPARTMENT
        )
        
        return request
    
    def resolve_complaint(self, request: ServiceRequest, resolution: str) -> ServiceRequest:
        """Resolve complaint with action taken"""
        if request.status not in [ServiceStatus.PENDING, ServiceStatus.IN_PROGRESS]:
            raise ValueError(f"Cannot resolve in {request.status} state")
        
        request.payload["resolution_description"] = resolution
        request.payload["resolved_date"] = datetime.utcnow().isoformat()
        
        request.update_status(
            ServiceStatus.DELIVERED,
            "Complaint resolved",
            OwnershipType.SYSTEM
        )
        
        return request


# ============================================================================
# 4. SERVICE MANAGER
# ============================================================================

class WaterServiceManager:
    """
    Central manager for all water services
    Routes service requests to appropriate handlers
    """
    
    def __init__(self, db_service=None, payment_gateway=None):
        self.db_service = db_service
        self.payment_gateway = payment_gateway
        
        # Initialize all services
        self.pay_bill_service = WaterPayBillService(db_service, payment_gateway)
        self.connection_service = WaterConnectionRequestService(db_service)
        self.meter_change_service = WaterMeterChangeService(db_service)
        self.leak_complaint_service = WaterLeakComplaintService(db_service)
        self.meter_reading_service = WaterMeterReadingService(db_service)
        self.complaint_service = WaterComplaintService(db_service)
        
        # Service registry
        self.service_handlers = {
            ServiceType.WATER_PAY_BILL: self.pay_bill_service,
            ServiceType.WATER_CONNECTION_REQUEST: self.connection_service,
            ServiceType.WATER_METER_CHANGE: self.meter_change_service,
            ServiceType.WATER_LEAK_COMPLAINT: self.leak_complaint_service,
            ServiceType.WATER_METER_READING_SUBMISSION: self.meter_reading_service,
            ServiceType.WATER_COMPLAINT_GRIEVANCE: self.complaint_service,
        }
    
    def get_handler(self, service_type: ServiceType):
        """Get appropriate handler for service type"""
        return self.service_handlers.get(service_type)
    
    def get_service_request_status(self, service_request_id: str) -> Dict[str, Any]:
        """Get current status of a service request"""
        # In production, query from database
        pass
    
    def list_user_requests(self, user_id: str) -> List[ServiceRequest]:
        """List all service requests for a user"""
        # In production, query from database
        pass


# ============================================================================
# 5. KIOSK API LAYER
# ============================================================================

class WaterKioskAPI:
    """
    KIOSK API Layer for Water Services
    Handles HTTP requests and responses
    """
    
    def __init__(self, service_manager: WaterServiceManager):
        self.service_manager = service_manager
    
    def pay_bill(self, user_id: str, consumer_number: str, billing_period: str,
                amount: str, payment_method: str) -> Dict[str, Any]:
        """
        API endpoint: POST /api/v1/water/pay-bill
        """
        try:
            amount_decimal = Decimal(amount)
            
            request = self.service_manager.pay_bill_service.create_pay_bill_request(
                consumer_number, user_id, billing_period, amount_decimal, payment_method
            )
            
            request = self.service_manager.pay_bill_service.submit_payment(request)
            request = self.service_manager.pay_bill_service.process_payment(request)
            
            return {
                "success": request.status == ServiceStatus.DELIVERED,
                "service_request_id": request.service_request_id,
                "status": request.status.value,
                "error_code": request.error_code.value if request.error_code else None,
                "error_message": request.error_message,
                "receipt": self.service_manager.pay_bill_service.generate_receipt(request)
                if request.status == ServiceStatus.DELIVERED else None
            }
        
        except Exception as e:
            logger.error(f"Error in pay_bill: {str(e)}")
            return {
                "success": False,
                "error_code": ErrorCode.INTERNAL_ERROR.value,
                "error_message": str(e)
            }
    
    def new_connection(self, applicant_id: str, applicant_name: str, phone: str,
                      email: str, address: str, connection_type: str,
                      load_requirement: int) -> Dict[str, Any]:
        """
        API endpoint: POST /api/v1/water/new-connection
        """
        try:
            conn_type = ConnectionType[connection_type.upper()]
            
            request = self.service_manager.connection_service.create_connection_request(
                applicant_id, applicant_name, phone, email, address, conn_type, load_requirement
            )
            
            request = self.service_manager.connection_service.submit_connection_request(request)
            request = self.service_manager.connection_service.acknowledge_request(request)
            request = self.service_manager.connection_service.schedule_inspection(request)
            
            return {
                "success": request.status == ServiceStatus.PENDING,
                "service_request_id": request.service_request_id,
                "status": request.status.value,
                "message": "New connection request submitted. Inspection will be scheduled soon."
            }
        
        except Exception as e:
            logger.error(f"Error in new_connection: {str(e)}")
            return {
                "success": False,
                "error_code": ErrorCode.INTERNAL_ERROR.value,
                "error_message": str(e)
            }
    
    def report_leak(self, location: str, leak_type: str, severity: str,
                   consumer_number: str = None, affected_residents: int = 0) -> Dict[str, Any]:
        """
        API endpoint: POST /api/v1/water/report-leak
        """
        try:
            leak_t = LeakType[leak_type.upper()]
            sev = LeakSeverity[severity.upper()]
            
            request = self.service_manager.leak_complaint_service.create_leak_complaint(
                location, leak_t, sev, consumer_number, affected_residents
            )
            
            request = self.service_manager.leak_complaint_service.submit_leak_complaint(request)
            request = self.service_manager.leak_complaint_service.dispatch_field_team(request, "TEAM_001")
            
            return {
                "success": request.status == ServiceStatus.PENDING,
                "service_request_id": request.service_request_id,
                "status": request.status.value,
                "complaint_number": f"LEAK_{request.service_request_id[:8].upper()}",
                "estimated_arrival": request.payload.get("estimated_arrival"),
                "message": "Leak complaint registered. Field team dispatched."
            }
        
        except Exception as e:
            logger.error(f"Error in report_leak: {str(e)}")
            return {
                "success": False,
                "error_code": ErrorCode.INTERNAL_ERROR.value,
                "error_message": str(e)
            }
    
    def get_request_status(self, service_request_id: str, user_id: str) -> Dict[str, Any]:
        """
        API endpoint: GET /api/v1/water/requests/{id}/status
        """
        return {
            "service_request_id": service_request_id,
            "status": "PENDING",
            "message": "Request is being processed"
        }


# ============================================================================
# 6. EXAMPLE USAGE
# ============================================================================

if __name__ == "__main__":
    """
    Example usage demonstrating the water service framework
    """
    
    # Initialize manager
    manager = WaterServiceManager()
    
    # Example 1: Bill Payment
    print("\n=== EXAMPLE 1: Water Bill Payment ===")
    bill_request = manager.pay_bill_service.create_pay_bill_request(
        consumer_number="WTR123456789",
        customer_id="CUST_001",
        billing_period="2026-01",
        amount=Decimal("1200.00"),
        payment_method="UPI"
    )
    print(f"Created request: {bill_request.service_request_id}")
    print(f"Status: {bill_request.status.value}")
    
    bill_request = manager.pay_bill_service.submit_payment(bill_request)
    print(f"After submit - Status: {bill_request.status.value}")
    
    bill_request = manager.pay_bill_service.process_payment(bill_request)
    print(f"After payment - Status: {bill_request.status.value}")
    
    if bill_request.status == ServiceStatus.DELIVERED:
        receipt = manager.pay_bill_service.generate_receipt(bill_request)
        print(f"Receipt: {json.dumps(receipt, indent=2)}\n")
    
    # Example 2: New Connection Request
    print("\n=== EXAMPLE 2: New Water Connection ===")
    conn_request = manager.connection_service.create_connection_request(
        applicant_id="APPL_001",
        applicant_name="Priya Sharma",
        phone_number="9876543210",
        email="priya@example.com",
        address="123 Main Street, Apt 4B",
        connection_type=ConnectionType.DOMESTIC,
        load_requirement=1000
    )
    print(f"Created request: {conn_request.service_request_id}")
    
    conn_request = manager.connection_service.submit_connection_request(conn_request)
    print(f"After submit - Status: {conn_request.status.value}")
    
    conn_request = manager.connection_service.acknowledge_request(conn_request)
    print(f"After acknowledge - Status: {conn_request.status.value}")
    
    conn_request = manager.connection_service.schedule_inspection(conn_request)
    print(f"After scheduling - Status: {conn_request.status.value}\n")
    
    # Example 3: Leak Complaint
    print("\n=== EXAMPLE 3: Water Leak Report ===")
    leak_request = manager.leak_complaint_service.create_leak_complaint(
        location_description="Main Street, Near Traffic Signal",
        leak_type=LeakType.MAJOR,
        severity=LeakSeverity.HIGH,
        consumer_number="WTR123456789",
        affected_residents=5
    )
    print(f"Created leak complaint: {leak_request.service_request_id}")
    
    leak_request = manager.leak_complaint_service.submit_leak_complaint(leak_request)
    print(f"After submit - Status: {leak_request.status.value}")
    
    leak_request = manager.leak_complaint_service.dispatch_field_team(leak_request, "TEAM_001")
    print(f"After dispatch - Status: {leak_request.status.value}")
    print(f"Estimated arrival: {leak_request.payload.get('estimated_arrival')}\n")
    
    # Example 4: Meter Reading
    print("\n=== EXAMPLE 4: Meter Reading Submission ===")
    reading_request = manager.meter_reading_service.create_reading_submission(
        consumer_number="WTR123456789",
        meter_number="MTR_WTR_0001",
        billing_period="2026-01",
        meter_reading=45230
    )
    print(f"Created reading submission: {reading_request.service_request_id}")
    
    reading_request = manager.meter_reading_service.submit_reading(reading_request)
    print(f"After submit - Status: {reading_request.status.value}")
    
    reading_request = manager.meter_reading_service.approve_reading(reading_request)
    print(f"After approval - Status: {reading_request.status.value}")
    print(f"Bill generated: {reading_request.payload.get('bill_number')}\n")
    
    # Export full request data
    print("=== Full Request History ===")
    print(json.dumps(reading_request.to_dict(include_history=True), indent=2, default=str))
