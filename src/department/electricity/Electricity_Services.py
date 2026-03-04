"""
SUVIDHA 2026 - Electricity Services Module
==========================================
Implements Service Transfer Framework for Electricity Department Services
Follows Core Terms & Framework: ServiceRequest as state machine

Author: SUVIDHA Team
Version: 1.0
"""

from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any, List
from uuid import uuid4
from decimal import Decimal
import logging

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
    """Electricity-specific service types"""
    ELECTRICITY_PAY_BILL = "ELECTRICITY_PAY_BILL"
    ELECTRICITY_SERVICE_TRANSFER = "ELECTRICITY_SERVICE_TRANSFER"
    ELECTRICITY_METER_CHANGE = "ELECTRICITY_METER_CHANGE"
    ELECTRICITY_CONNECTION_REQUEST = "ELECTRICITY_CONNECTION_REQUEST"
    ELECTRICITY_COMPLAINT = "ELECTRICITY_COMPLAINT"
    ELECTRICITY_METER_READING_SUBMISSION = "ELECTRICITY_METER_READING_SUBMISSION"


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
    """Error codes for service failures"""
    # User Errors
    INVALID_DATA = "INVALID_DATA"
    UNAUTHORIZED = "UNAUTHORIZED"
    CONFLICT = "CONFLICT"
    
    # System Errors
    DEPARTMENT_TIMEOUT = "DEPARTMENT_TIMEOUT"
    INTEGRATION_FAILURE = "INTEGRATION_FAILURE"
    INTERNAL_ERROR = "INTERNAL_ERROR"
    
    # Meter Errors
    METER_NOT_FOUND = "METER_NOT_FOUND"
    METER_INACTIVE = "METER_INACTIVE"
    METER_NOT_OWNED_BY_USER = "METER_NOT_OWNED_BY_USER"
    
    # Bill Errors
    BILL_NOT_FOUND = "BILL_NOT_FOUND"
    INSUFFICIENT_AMOUNT = "INSUFFICIENT_AMOUNT"
    PAYMENT_FAILED = "PAYMENT_FAILED"
    
    # Transfer Errors
    PENDING_TRANSFER_EXISTS = "PENDING_TRANSFER_EXISTS"
    TRANSFER_AUTHORIZATION_FAILED = "TRANSFER_AUTHORIZATION_FAILED"


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
        # Add initial status to history
        self._add_status_history(self.status, "Service request created")
    
    def _add_status_history(self, status: ServiceStatus, reason: str, metadata: Dict = None):
        """
        Append-only status history - never overwrite
        """
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
        """
        Transition to new status with validation
        """
        if not self._is_valid_transition(self.status, new_status):
            raise ValueError(f"Invalid transition: {self.status.value} → {new_status.value}")
        
        self.status = new_status
        self.updated_at = datetime.utcnow()
        if new_owner:
            self.current_owner = new_owner
        self._add_status_history(new_status, reason, metadata)
    
    @staticmethod
    def _is_valid_transition(from_status: ServiceStatus, to_status: ServiceStatus) -> bool:
        """
        Validate state machine transitions
        """
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
        """
        Status visibility rules based on actor role
        """
        if viewer_role == ActorRole.DEPARTMENT_OFFICER:
            # Department sees from SUBMITTED onwards
            return self.status if self.status != ServiceStatus.DRAFT else None
        elif viewer_role == ActorRole.END_USER:
            # User sees DRAFT through DELIVERED/DENIED
            return self.status
        else:  # AUTOMATED_SYSTEM
            # System sees all
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
# 3. ELECTRICITY-SPECIFIC DATA MODELS
# ============================================================================

@dataclass
class PaymentDetails:
    """Payment details for bill payments"""
    payment_method: str  # CARD, UPI, NET_BANKING
    payment_reference: str  # Transaction ID from payment gateway
    amount: Decimal
    payment_date: datetime = field(default_factory=datetime.utcnow)
    gateway_response: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MeterInfo:
    """Meter information"""
    meter_number: str
    meter_type: str  # SINGLE_PHASE, THREE_PHASE
    sanctioned_load: float  # in kW
    customer_id: str
    status: str  # ACTIVE, INACTIVE, SUSPENDED
    installation_date: datetime = None


@dataclass
class BillInfo:
    """Bill information"""
    bill_number: str
    meter_number: str
    billing_period: str  # e.g., "2026-01"
    consumption_units: float  # in kWh
    rate_per_unit: Decimal
    bill_amount: Decimal
    amount_paid: Decimal = Decimal("0")
    bill_date: datetime = None
    due_date: datetime = None
    status: str = "PENDING"  # PENDING, PAID, OVERDUE


# ============================================================================
# 4. VALIDATION SERVICE
# ============================================================================

class ElectricityValidationService:
    """Validates electricity-specific business rules"""
    
    @staticmethod
    def validate_meter_number(meter_number: str) -> bool:
        """Validate meter number format"""
        if not meter_number or len(meter_number) < 8:
            return False
        return meter_number.isalnum()
    
    @staticmethod
    def validate_aadhar(aadhar: str) -> bool:
        """Validate Aadhar number format"""
        if not aadhar or len(aadhar) != 12:
            return False
        return aadhar.isdigit()
    
    @staticmethod
    def validate_amount(amount: Decimal, minimum: Decimal = None) -> bool:
        """Validate payment amount"""
        if amount <= 0:
            return False
        if minimum and amount < minimum:
            return False
        return True
    
    @staticmethod
    def validate_effective_date(effective_date: datetime) -> bool:
        """Validate transfer effective date (must be in future)"""
        return effective_date > datetime.utcnow()


# ============================================================================
# 5. ELECTRICITY SERVICES
# ============================================================================

class ElectricityPayBillService:
    """
    ELECTRICITY_PAY_BILL Service
    Payment of outstanding electricity dues for a meter
    """
    
    def __init__(self, db_service=None, payment_gateway=None):
        """
        Initialize with external dependencies
        
        Args:
            db_service: Database service for meter/bill queries
            payment_gateway: Payment gateway integration (RazorPay, PayU, etc.)
        """
        self.db_service = db_service
        self.payment_gateway = payment_gateway
        self.validator = ElectricityValidationService()
    
    def create_pay_bill_request(self, meter_number: str, customer_id: str,
                               billing_period: str, amount: Decimal,
                               payment_method: str) -> ServiceRequest:
        """
        Create a bill payment service request
        
        Args:
            meter_number: Customer's meter number
            customer_id: Customer ID / Aadhar
            billing_period: Billing period (e.g., "2026-01")
            amount: Amount to pay
            payment_method: Payment method (CARD, UPI, NET_BANKING)
        
        Returns:
            ServiceRequest in DRAFT status
        
        Raises:
            ValueError: If validation fails
        """
        # Input validation
        if not self.validator.validate_meter_number(meter_number):
            raise ValueError(ErrorCode.INVALID_DATA.value, "Invalid meter number format")
        
        if not self.validator.validate_amount(amount):
            raise ValueError(ErrorCode.INVALID_DATA.value, "Invalid amount")
        
        # Create service request
        request = ServiceRequest(
            service_type=ServiceType.ELECTRICITY_PAY_BILL,
            initiator_id=customer_id,
            beneficiary_id=customer_id,  # Self-service
            current_owner=OwnershipType.USER,
            payload={
                "meter_number": meter_number,
                "billing_period": billing_period,
                "amount": str(amount),
                "payment_method": payment_method,
                "created_timestamp": datetime.utcnow().isoformat()
            }
        )
        
        logger.info(f"Created bill payment request: {request.service_request_id}")
        return request
    
    def submit_payment(self, service_request: ServiceRequest) -> ServiceRequest:
        """
        Submit payment request for processing
        
        Args:
            service_request: Service request in DRAFT status
        
        Returns:
            Updated ServiceRequest with SUBMITTED status
        """
        if service_request.status != ServiceStatus.DRAFT:
            raise ValueError(f"Cannot submit request in {service_request.status.value} status")
        
        # Move to SUBMITTED
        service_request.update_status(
            ServiceStatus.SUBMITTED,
            "Payment request submitted by user",
            new_owner=OwnershipType.SYSTEM
        )
        
        return service_request
    
    def process_payment(self, service_request: ServiceRequest) -> ServiceRequest:
        """
        Process payment via payment gateway
        
        Args:
            service_request: Service request in SUBMITTED status
        
        Returns:
            Updated ServiceRequest with DELIVERED/FAILED status
        """
        if service_request.status != ServiceStatus.SUBMITTED:
            raise ValueError(f"Cannot process payment in {service_request.status.value} status")
        
        meter_number = service_request.payload.get("meter_number")
        amount = Decimal(service_request.payload.get("amount"))
        payment_method = service_request.payload.get("payment_method")
        
        try:
            # Step 1: Acknowledge receipt
            service_request.update_status(
                ServiceStatus.ACKNOWLEDGED,
                "Payment received and acknowledged",
                new_owner=OwnershipType.SYSTEM
            )
            
            # Step 2: Move to processing
            service_request.update_status(
                ServiceStatus.IN_PROGRESS,
                "Processing payment with gateway",
                new_owner=OwnershipType.SYSTEM
            )
            
            # Step 3: Call payment gateway (mocked here)
            payment_response = self._call_payment_gateway(
                meter_number, amount, payment_method
            )
            
            if payment_response.get("status") == "SUCCESS":
                # Payment successful
                service_request.update_status(
                    ServiceStatus.DELIVERED,
                    "Payment processed successfully",
                    new_owner=OwnershipType.SYSTEM,
                    metadata={
                        "payment_id": payment_response.get("payment_id"),
                        "transaction_date": datetime.utcnow().isoformat()
                    }
                )
                logger.info(f"Payment successful for {meter_number}: {payment_response}")
            else:
                # Payment failed
                service_request.update_status(
                    ServiceStatus.FAILED,
                    f"Payment failed: {payment_response.get('error_message')}",
                    new_owner=OwnershipType.SYSTEM
                )
                service_request.error_code = ErrorCode.PAYMENT_FAILED
                service_request.error_message = payment_response.get("error_message")
                logger.error(f"Payment failed for {meter_number}: {payment_response}")
        
        except Exception as e:
            service_request.update_status(
                ServiceStatus.FAILED,
                f"Payment processing error: {str(e)}",
                new_owner=OwnershipType.SYSTEM
            )
            service_request.error_code = ErrorCode.INTEGRATION_FAILURE
            service_request.error_message = str(e)
            logger.error(f"Error processing payment: {str(e)}")
        
        return service_request
    
    def _call_payment_gateway(self, meter_number: str, amount: Decimal, 
                             payment_method: str) -> Dict[str, Any]:
        """
        Mock payment gateway call
        Replace with actual RazorPay/PayU integration
        """
        if self.payment_gateway:
            return self.payment_gateway.process_payment(amount, payment_method)
        
        # Mock response for testing
        return {
            "status": "SUCCESS",
            "payment_id": f"PAY_{meter_number}_{int(datetime.utcnow().timestamp())}",
            "amount": str(amount),
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def generate_receipt(self, service_request: ServiceRequest) -> Dict[str, Any]:
        """
        Generate payment receipt (for DELIVERED status)
        """
        if service_request.status != ServiceStatus.DELIVERED:
            raise ValueError("Receipt can only be generated for completed payments")
        
        receipt = {
            "receipt_id": f"REC_{service_request.service_request_id[:8]}",
            "meter_number": service_request.payload.get("meter_number"),
            "amount_paid": service_request.payload.get("amount"),
            "payment_date": service_request.updated_at.isoformat(),
            "payment_reference": service_request.payload.get("payment_method"),
            "service_request_id": service_request.service_request_id,
            "status": "COMPLETED"
        }
        
        return receipt


class ElectricityServiceTransferService:
    """
    ELECTRICITY_SERVICE_TRANSFER Service
    Transfer electricity service from one user to another
    """
    
    def __init__(self, db_service=None):
        self.db_service = db_service
        self.validator = ElectricityValidationService()
    
    def create_transfer_request(self, meter_number: str, old_customer_id: str,
                               new_customer_id: str, identity_proof_ref: str,
                               ownership_proof_ref: str, consent_ref: str,
                               effective_date: datetime) -> ServiceRequest:
        """
        Create service transfer request
        
        Args:
            meter_number: Meter to be transferred
            old_customer_id: Current customer
            new_customer_id: New customer
            identity_proof_ref: Reference to identity proof
            ownership_proof_ref: Reference to ownership proof
            consent_ref: Reference to consent document
            effective_date: Date when transfer becomes effective
        
        Returns:
            ServiceRequest in DRAFT status
        """
        # Validation
        if not self.validator.validate_meter_number(meter_number):
            raise ValueError(ErrorCode.INVALID_DATA.value, "Invalid meter number")
        
        if not self.validator.validate_aadhar(old_customer_id) or \
           not self.validator.validate_aadhar(new_customer_id):
            raise ValueError(ErrorCode.INVALID_DATA.value, "Invalid customer ID")
        
        if not self.validator.validate_effective_date(effective_date):
            raise ValueError(ErrorCode.INVALID_DATA.value, "Effective date must be in future")
        
        # Create request
        request = ServiceRequest(
            service_type=ServiceType.ELECTRICITY_SERVICE_TRANSFER,
            initiator_id=old_customer_id,  # Old customer initiates
            beneficiary_id=new_customer_id,  # New customer benefits
            current_owner=OwnershipType.USER,
            payload={
                "meter_number": meter_number,
                "old_customer_id": old_customer_id,
                "new_customer_id": new_customer_id,
                "identity_proof_ref": identity_proof_ref,
                "ownership_proof_ref": ownership_proof_ref,
                "consent_ref": consent_ref,
                "effective_date": effective_date.isoformat(),
                "created_timestamp": datetime.utcnow().isoformat()
            }
        )
        
        logger.info(f"Created transfer request: {request.service_request_id}")
        return request
    
    def submit_transfer(self, service_request: ServiceRequest) -> ServiceRequest:
        """Submit transfer for department approval"""
        if service_request.status != ServiceStatus.DRAFT:
            raise ValueError(f"Cannot submit in {service_request.status.value} status")
        
        service_request.update_status(
            ServiceStatus.SUBMITTED,
            "Service transfer request submitted",
            new_owner=OwnershipType.SYSTEM
        )
        
        return service_request
    
    def acknowledge_transfer(self, service_request: ServiceRequest) -> ServiceRequest:
        """Department acknowledges receipt"""
        if service_request.status != ServiceStatus.SUBMITTED:
            raise ValueError(f"Invalid status: {service_request.status.value}")
        
        service_request.update_status(
            ServiceStatus.ACKNOWLEDGED,
            "Transfer request acknowledged by department",
            new_owner=OwnershipType.DEPARTMENT
        )
        
        return service_request
    
    def approve_transfer(self, service_request: ServiceRequest, approved_by: str) -> ServiceRequest:
        """Department approves transfer"""
        if service_request.status != ServiceStatus.ACKNOWLEDGED:
            raise ValueError(f"Invalid status: {service_request.status.value}")
        
        service_request.update_status(
            ServiceStatus.APPROVED,
            f"Transfer approved by {approved_by}",
            new_owner=OwnershipType.DEPARTMENT,
            metadata={"approved_by": approved_by}
        )
        
        return service_request
    
    def deny_transfer(self, service_request: ServiceRequest, reason: str) -> ServiceRequest:
        """Department denies transfer"""
        if service_request.status not in [ServiceStatus.ACKNOWLEDGED, ServiceStatus.PENDING]:
            raise ValueError(f"Invalid status: {service_request.status.value}")
        
        service_request.update_status(
            ServiceStatus.DENIED,
            f"Transfer denied: {reason}",
            new_owner=OwnershipType.DEPARTMENT
        )
        service_request.error_code = ErrorCode.TRANSFER_AUTHORIZATION_FAILED
        service_request.error_message = reason
        
        return service_request
    
    def complete_transfer(self, service_request: ServiceRequest) -> ServiceRequest:
        """Complete the transfer (execute on effective date)"""
        if service_request.status != ServiceStatus.APPROVED:
            raise ValueError(f"Invalid status: {service_request.status.value}")
        
        service_request.update_status(
            ServiceStatus.IN_PROGRESS,
            "Transfer execution started",
            new_owner=OwnershipType.SYSTEM
        )
        
        try:
            # Perform transfer in database/system
            # This would call the actual electricity system
            service_request.update_status(
                ServiceStatus.DELIVERED,
                "Service transfer completed successfully",
                new_owner=OwnershipType.SYSTEM,
                metadata={
                    "transfer_date": datetime.utcnow().isoformat()
                }
            )
        except Exception as e:
            service_request.update_status(
                ServiceStatus.FAILED,
                f"Transfer execution failed: {str(e)}",
                new_owner=OwnershipType.SYSTEM
            )
            service_request.error_code = ErrorCode.INTERNAL_ERROR
            service_request.error_message = str(e)
        
        return service_request


class ElectricityMeterChangeService:
    """
    ELECTRICITY_METER_CHANGE Service
    Replacement or correction of meter ID
    """
    
    def __init__(self, db_service=None):
        self.db_service = db_service
        self.validator = ElectricityValidationService()
    
    def create_meter_change_request(self, old_meter_number: str, new_meter_number: str,
                                    reason_code: str, inspection_report_ref: str) -> ServiceRequest:
        """
        Create meter change request (requires department inspection)
        """
        if not self.validator.validate_meter_number(old_meter_number) or \
           not self.validator.validate_meter_number(new_meter_number):
            raise ValueError(ErrorCode.INVALID_DATA.value, "Invalid meter number")
        
        request = ServiceRequest(
            service_type=ServiceType.ELECTRICITY_METER_CHANGE,
            initiator_id="DEPARTMENT",
            beneficiary_id="DEPARTMENT",
            current_owner=OwnershipType.DEPARTMENT,
            payload={
                "old_meter_number": old_meter_number,
                "new_meter_number": new_meter_number,
                "reason_code": reason_code,
                "inspection_report_ref": inspection_report_ref,
                "created_timestamp": datetime.utcnow().isoformat()
            }
        )
        
        return request
    
    def submit_for_inspection(self, service_request: ServiceRequest) -> ServiceRequest:
        """Submit meter change for inspection"""
        service_request.update_status(
            ServiceStatus.SUBMITTED,
            "Meter change submitted for inspection",
            new_owner=OwnershipType.DEPARTMENT
        )
        return service_request
    
    def complete_meter_change(self, service_request: ServiceRequest) -> ServiceRequest:
        """Complete meter replacement after inspection"""
        service_request.update_status(
            ServiceStatus.IN_PROGRESS,
            "Meter replacement in progress",
            new_owner=OwnershipType.SYSTEM
        )
        
        service_request.update_status(
            ServiceStatus.DELIVERED,
            "Meter replacement completed",
            new_owner=OwnershipType.SYSTEM,
            metadata={"completion_date": datetime.utcnow().isoformat()}
        )
        
        return service_request


class ElectricityConnectionRequestService:
    """
    ELECTRICITY_CONNECTION_REQUEST Service
    Request for new electricity connection
    """
    
    def __init__(self, db_service=None):
        self.db_service = db_service
        self.validator = ElectricityValidationService()
    
    def create_connection_request(self, applicant_id: str, address: str,
                                 load_requirement: float, property_documents_ref: str) -> ServiceRequest:
        """Create new connection request"""
        
        request = ServiceRequest(
            service_type=ServiceType.ELECTRICITY_CONNECTION_REQUEST,
            initiator_id=applicant_id,
            beneficiary_id=applicant_id,
            current_owner=OwnershipType.USER,
            payload={
                "applicant_id": applicant_id,
                "address": address,
                "load_requirement": load_requirement,
                "property_documents_ref": property_documents_ref,
                "created_timestamp": datetime.utcnow().isoformat()
            }
        )
        
        return request
    
    def submit_connection_request(self, service_request: ServiceRequest) -> ServiceRequest:
        """Submit connection request"""
        service_request.update_status(
            ServiceStatus.SUBMITTED,
            "Connection request submitted",
            new_owner=OwnershipType.SYSTEM
        )
        return service_request
    
    def approve_connection(self, service_request: ServiceRequest, meter_number: str) -> ServiceRequest:
        """Approve and activate connection"""
        service_request.update_status(
            ServiceStatus.APPROVED,
            "Connection approved by department",
            new_owner=OwnershipType.DEPARTMENT
        )
        
        service_request.update_status(
            ServiceStatus.IN_PROGRESS,
            "Connection activation in progress",
            new_owner=OwnershipType.SYSTEM
        )
        
        service_request.update_status(
            ServiceStatus.DELIVERED,
            "Connection activated successfully",
            new_owner=OwnershipType.SYSTEM,
            metadata={
                "meter_number": meter_number,
                "activation_date": datetime.utcnow().isoformat()
            }
        )
        
        return service_request


# ============================================================================
# 6. SERVICE FACTORY & MANAGER
# ============================================================================

class ElectricityServiceManager:
    """
    Central manager for all electricity services
    Routes service requests to appropriate handlers
    """
    
    def __init__(self, db_service=None, payment_gateway=None):
        self.db_service = db_service
        self.payment_gateway = payment_gateway
        
        # Initialize all services
        self.pay_bill_service = ElectricityPayBillService(db_service, payment_gateway)
        self.transfer_service = ElectricityServiceTransferService(db_service)
        self.meter_change_service = ElectricityMeterChangeService(db_service)
        self.connection_service = ElectricityConnectionRequestService(db_service)
        
        # Service registry
        self.service_handlers = {
            ServiceType.ELECTRICITY_PAY_BILL: self.pay_bill_service,
            ServiceType.ELECTRICITY_SERVICE_TRANSFER: self.transfer_service,
            ServiceType.ELECTRICITY_METER_CHANGE: self.meter_change_service,
            ServiceType.ELECTRICITY_CONNECTION_REQUEST: self.connection_service,
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
# 5.5 ELECTRICITY COMPLAINT SERVICE (NEW)
# ============================================================================

class ComplaintCategory(Enum):
    """Categories for electricity complaints"""
    BILLING = "BILLING"  # Wrong bill, overcharging
    POWER_OUTAGE = "POWER_OUTAGE"  # No electricity
    METER_ISSUE = "METER_ISSUE"  # Meter not working, slow/fast
    VOLTAGE_FLUCTUATION = "VOLTAGE_FLUCTUATION"  # High/low voltage
    WIRE_DAMAGE = "WIRE_DAMAGE"  # Broken wires, dangerous
    STREET_LIGHT = "STREET_LIGHT"  # Street light not working
    CONNECTION_ISSUE = "CONNECTION_ISSUE"  # Loose connection
    OTHER = "OTHER"  # Anything else


class ComplaintPriority(Enum):
    """Priority levels for complaints"""
    LOW = "LOW"  # Minor issue, can wait
    NORMAL = "NORMAL"  # Standard complaint
    HIGH = "HIGH"  # Urgent
    URGENT = "URGENT"  # Emergency (wire down, fire risk)


class ElectricityComplaintService:
    """
    ELECTRICITY_COMPLAINT Service
    Handle citizen complaints about electricity services
    - Billing disputes
    - Power outages
    - Meter problems
    - Safety hazards
    - Street light issues
    """
    
    def __init__(self, db_service=None):
        self.db_service = db_service
        self.validator = ElectricityValidationService()
    
    def create_complaint(
        self,
        customer_id: str,
        meter_number: Optional[str],  # Can be None for street lights/general
        category: ComplaintCategory,
        priority: ComplaintPriority,
        description: str,
        location: Optional[str] = None,  # For street lights/non-meter issues
        contact_phone: Optional[str] = None,
        photo_refs: Optional[List[str]] = None
    ) -> ServiceRequest:
        """
        Create a new complaint
        
        Args:
            customer_id: Customer ID / Aadhar
            meter_number: Associated meter (optional)
            category: Type of complaint
            priority: Urgency level
            description: Detailed description
            location: Location (for non-meter issues)
            contact_phone: Phone for follow-up
            photo_refs: References to uploaded photos
        
        Returns:
            ServiceRequest in DRAFT status
        """
        # Validate meter if provided
        if meter_number and not self.validator.validate_meter_number(meter_number):
            raise ValueError(ErrorCode.INVALID_DATA.value, "Invalid meter number format")
        
        # Validate description
        if not description or len(description.strip()) < 10:
            raise ValueError(ErrorCode.INVALID_DATA.value, "Description must be at least 10 characters")
        
        # Create service request
        request = ServiceRequest(
            service_type=ServiceType.ELECTRICITY_COMPLAINT,
            initiator_id=customer_id,
            beneficiary_id=customer_id,
            current_owner=OwnershipType.USER,
            payload={
                "customer_id": customer_id,
                "meter_number": meter_number,
                "complaint_category": category.value,
                "priority": priority.value,
                "description": description,
                "location": location,
                "contact_phone": contact_phone,
                "photo_refs": photo_refs or [],
                "created_timestamp": datetime.utcnow().isoformat(),
                "expected_response_hours": self._get_sla_hours(priority)
            }
        )
        
        logger.info(f"Created complaint: {request.service_request_id} - {category.value}")
        return request
    
    def submit_complaint(self, service_request: ServiceRequest) -> ServiceRequest:
        """
        Submit complaint for processing
        
        Args:
            service_request: Request in DRAFT status
        
        Returns:
            Updated request with SUBMITTED status
        """
        if service_request.status != ServiceStatus.DRAFT:
            raise ValueError(f"Cannot submit in {service_request.status.value} status")
        
        service_request.update_status(
            ServiceStatus.SUBMITTED,
            "Complaint submitted by customer",
            new_owner=OwnershipType.SYSTEM
        )
        
        return service_request
    
    def acknowledge_complaint(self, service_request: ServiceRequest, 
                             assigned_to: str) -> ServiceRequest:
        """
        Department acknowledges complaint and assigns to officer
        
        Args:
            service_request: Request in SUBMITTED status
            assigned_to: Officer ID assigned to handle
        
        Returns:
            Updated request with ACKNOWLEDGED status
        """
        if service_request.status != ServiceStatus.SUBMITTED:
            raise ValueError(f"Cannot acknowledge in {service_request.status.value} status")
        
        service_request.payload["assigned_to"] = assigned_to
        service_request.payload["acknowledged_at"] = datetime.utcnow().isoformat()
        
        service_request.update_status(
            ServiceStatus.ACKNOWLEDGED,
            f"Complaint assigned to officer {assigned_to}",
            new_owner=OwnershipType.DEPARTMENT
        )
        
        return service_request
    
    def start_investigation(self, service_request: ServiceRequest) -> ServiceRequest:
        """
        Mark complaint as being investigated
        
        Args:
            service_request: Request in ACKNOWLEDGED status
        
        Returns:
            Updated request with IN_PROGRESS status
        """
        if service_request.status != ServiceStatus.ACKNOWLEDGED:
            raise ValueError(f"Cannot investigate in {service_request.status.value} status")
        
        service_request.payload["investigation_started_at"] = datetime.utcnow().isoformat()
        
        service_request.update_status(
            ServiceStatus.IN_PROGRESS,
            "Investigation in progress",
            new_owner=OwnershipType.DEPARTMENT
        )
        
        return service_request
    
    def resolve_complaint(
        self, 
        service_request: ServiceRequest,
        resolution_notes: str,
        compensation_amount: Optional[Decimal] = None
    ) -> ServiceRequest:
        """
        Resolve the complaint
        
        Args:
            service_request: Request in IN_PROGRESS status
            resolution_notes: How the complaint was resolved
            compensation_amount: Any refund/credit given
        
        Returns:
            Updated request with DELIVERED status
        """
        if service_request.status != ServiceStatus.IN_PROGRESS:
            raise ValueError(f"Cannot resolve in {service_request.status.value} status")
        
        service_request.payload["resolution_notes"] = resolution_notes
        service_request.payload["resolved_at"] = datetime.utcnow().isoformat()
        if compensation_amount:
            service_request.payload["compensation_amount"] = str(compensation_amount)
        
        # Calculate response time for SLA tracking
        created = datetime.fromisoformat(service_request.created_at.isoformat())
        resolved = datetime.utcnow()
        response_hours = (resolved - created).total_seconds() / 3600
        service_request.payload["response_time_hours"] = round(response_hours, 2)
        
        service_request.update_status(
            ServiceStatus.DELIVERED,
            f"Complaint resolved: {resolution_notes[:50]}...",
            new_owner=OwnershipType.SYSTEM,
            metadata={
                "resolution_time_hours": response_hours,
                "compensation": str(compensation_amount) if compensation_amount else None
            }
        )
        
        return service_request
    
    def reject_complaint(self, service_request: ServiceRequest, 
                        rejection_reason: str) -> ServiceRequest:
        """
        Reject complaint as invalid
        
        Args:
            service_request: Request in any non-terminal state
            rejection_reason: Why it was rejected
        
        Returns:
            Updated request with DENIED status
        """
        service_request.payload["rejection_reason"] = rejection_reason
        service_request.payload["rejected_at"] = datetime.utcnow().isoformat()
        
        service_request.update_status(
            ServiceStatus.DENIED,
            f"Complaint rejected: {rejection_reason}",
            new_owner=OwnershipType.DEPARTMENT
        )
        service_request.error_code = ErrorCode.INVALID_DATA
        service_request.error_message = rejection_reason
        
        return service_request
    
    def _get_sla_hours(self, priority: ComplaintPriority) -> int:
        """Get expected response time based on priority"""
        sla_map = {
            ComplaintPriority.URGENT: 2,    # 2 hours
            ComplaintPriority.HIGH: 8,       # 8 hours
            ComplaintPriority.NORMAL: 24,    # 1 day
            ComplaintPriority.LOW: 48,       # 2 days
        }
        return sla_map.get(priority, 24)
    
    def escalate_complaint(self, service_request: ServiceRequest, 
                          escalation_level: str, reason: str) -> ServiceRequest:
        """
        Escalate complaint to higher authority if not resolved in time
        
        Args:
            service_request: Request in progress
            escalation_level: Next level (supervisor, manager, etc.)
            reason: Why escalation needed
        
        Returns:
            Updated request with escalated status tracking
        """
        service_request.payload["escalation"] = {
            "level": escalation_level,
            "reason": reason,
            "escalated_at": datetime.utcnow().isoformat()
        }
        
        # Add to history but keep same status
        service_request._add_status_history(
            service_request.status,
            f"Escalated to {escalation_level}: {reason}"
        )
        
        return service_request


# ============================================================================
# 5.6 ELECTRICITY METER READING SUBMISSION SERVICE (NEW)
# ============================================================================

class ReadingSource(Enum):
    """How the reading was submitted"""
    KIOSK = "KIOSK"  # At physical kiosk
    MOBILE_APP = "MOBILE_APP"  # Via smartphone app
    SMS = "SMS"  # Via text message
    IVR = "IVR"  # Phone call
    MANUAL = "MANUAL"  # Officer entered


class ReadingVerificationStatus(Enum):
    """Verification state of reading"""
    PENDING = "PENDING"  # Awaiting verification
    VERIFIED = "VERIFIED"  # Auto-verified or officer verified
    REJECTED = "REJECTED"  # Invalid reading
    FLAGGED = "FLAGGED"  # Unusual consumption, needs review


class ElectricityMeterReadingSubmissionService:
    """
    ELECTRICITY_METER_READING_SUBMISSION Service
    Allow customers to submit their own meter readings
    - Self-reading submission
    - Automatic bill calculation
    - Reading validation against history
    - Anomaly detection
    """
    
    def __init__(self, db_service=None):
        self.db_service = db_service
        self.validator = ElectricityValidationService()
    
    def create_reading_submission(
        self,
        customer_id: str,
        meter_number: str,
        reading_value: Decimal,
        reading_date: datetime,
        photo_ref: Optional[str] = None,  # Photo of meter for verification
        source: ReadingSource = ReadingSource.KIOSK,
        notes: Optional[str] = None
    ) -> ServiceRequest:
        """
        Create a meter reading submission
        
        Args:
            customer_id: Customer ID / Aadhar
            meter_number: Meter being read
            reading_value: Current meter reading in kWh
            reading_date: Date when reading was taken
            photo_ref: Reference to uploaded meter photo
            source: How reading was submitted
            notes: Additional notes
        
        Returns:
            ServiceRequest in DRAFT status
        """
        # Validate meter
        if not self.validator.validate_meter_number(meter_number):
            raise ValueError(ErrorCode.INVALID_DATA.value, "Invalid meter number format")
        
        # Validate reading
        if reading_value <= 0:
            raise ValueError(ErrorCode.INVALID_DATA.value, "Reading must be positive")
        
        # Check if reading is reasonable (not astronomically high)
        if reading_value > 1000000:  # 1 million units is suspicious
            logger.warning(f"Suspicious high reading: {reading_value} for meter {meter_number}")
            # We'll still accept but flag it
        
        # Create service request
        request = ServiceRequest(
            service_type=ServiceType.ELECTRICITY_METER_READING_SUBMISSION,
            initiator_id=customer_id,
            beneficiary_id=customer_id,
            current_owner=OwnershipType.USER,
            payload={
                "customer_id": customer_id,
                "meter_number": meter_number,
                "reading_value": str(reading_value),
                "reading_date": reading_date.isoformat(),
                "photo_ref": photo_ref,
                "submission_source": source.value,
                "notes": notes,
                "verification_status": ReadingVerificationStatus.PENDING.value,
                "created_timestamp": datetime.utcnow().isoformat()
            }
        )
        
        logger.info(f"Created meter reading submission: {request.service_request_id} for meter {meter_number}")
        return request
    
    def submit_reading(self, service_request: ServiceRequest) -> ServiceRequest:
        """
        Submit reading for processing and verification
        
        Args:
            service_request: Request in DRAFT status
        
        Returns:
            Updated request with SUBMITTED status
        """
        if service_request.status != ServiceStatus.DRAFT:
            raise ValueError(f"Cannot submit in {service_request.status.value} status")
        
        # Get previous reading for this meter (would come from DB)
        previous_reading = self._get_previous_reading(
            service_request.payload.get("meter_number")
        )
        
        current_reading = Decimal(service_request.payload.get("reading_value"))
        
        # Validate reading is not less than previous
        if previous_reading and current_reading < previous_reading:
            service_request.payload["verification_status"] = ReadingVerificationStatus.REJECTED.value
            service_request.update_status(
                ServiceStatus.FAILED,
                "Reading is less than previous reading",
                new_owner=OwnershipType.SYSTEM
            )
            service_request.error_code = ErrorCode.INVALID_DATA
            service_request.error_message = f"Reading {current_reading} is below previous {previous_reading}"
            return service_request
        
        # Calculate consumption
        if previous_reading:
            consumption = current_reading - previous_reading
            service_request.payload["consumption_units"] = str(consumption)
            service_request.payload["previous_reading"] = str(previous_reading)
            
            # Check for unusual consumption (anomaly detection)
            if self._is_unusual_consumption(previous_reading, current_reading):
                service_request.payload["verification_status"] = ReadingVerificationStatus.FLAGGED.value
                service_request.payload["flag_reason"] = "Unusual consumption pattern"
                logger.info(f"Flagged unusual consumption for meter {service_request.payload.get('meter_number')}")
        
        service_request.update_status(
            ServiceStatus.SUBMITTED,
            "Meter reading submitted for verification",
            new_owner=OwnershipType.SYSTEM
        )
        
        return service_request
    
    def verify_reading(self, service_request: ServiceRequest, 
                      verified_by: str = "SYSTEM") -> ServiceRequest:
        """
        Verify the submitted reading (auto or manual)
        
        Args:
            service_request: Request in SUBMITTED status
            verified_by: Who verified (SYSTEM or officer ID)
        
        Returns:
            Updated request with appropriate status
        """
        if service_request.status != ServiceStatus.SUBMITTED:
            raise ValueError(f"Cannot verify in {service_request.status.value} status")
        
        verification_status = service_request.payload.get("verification_status")
        
        # If flagged, need manual review
        if verification_status == ReadingVerificationStatus.FLAGGED.value:
            service_request.update_status(
                ServiceStatus.PENDING,
                "Reading flagged for manual review",
                new_owner=OwnershipType.DEPARTMENT
            )
            return service_request
        
        # Auto-verify if no issues
        service_request.payload["verification_status"] = ReadingVerificationStatus.VERIFIED.value
        service_request.payload["verified_at"] = datetime.utcnow().isoformat()
        service_request.payload["verified_by"] = verified_by
        
        # Calculate estimated bill
        if "consumption_units" in service_request.payload:
            bill = self._calculate_bill(
                Decimal(service_request.payload["consumption_units"])
            )
            service_request.payload["estimated_bill"] = {
                "amount": str(bill["amount"]),
                "breakdown": bill["breakdown"]
            }
        
        service_request.update_status(
            ServiceStatus.APPROVED,
            f"Meter reading verified by {verified_by}",
            new_owner=OwnershipType.SYSTEM
        )
        
        return service_request
    
    def generate_bill(self, service_request: ServiceRequest) -> ServiceRequest:
        """
        Generate bill from verified reading
        
        Args:
            service_request: Request in APPROVED status
        
        Returns:
            Updated request with DELIVERED status and bill details
        """
        if service_request.status != ServiceStatus.APPROVED:
            raise ValueError(f"Cannot generate bill in {service_request.status.value} status")
        
        meter_number = service_request.payload.get("meter_number")
        consumption = Decimal(service_request.payload.get("consumption_units", 0))
        billing_period = self._get_current_billing_period()
        
        # Calculate final bill
        bill = self._calculate_bill(consumption)
        
        # Generate bill number
        bill_number = f"BILL_{meter_number}_{billing_period}"
        
        service_request.payload["bill"] = {
            "bill_number": bill_number,
            "billing_period": billing_period,
            "consumption_units": str(consumption),
            "amount": str(bill["amount"]),
            "breakdown": bill["breakdown"],
            "due_date": (datetime.utcnow() + timedelta(days=15)).isoformat(),
            "generated_at": datetime.utcnow().isoformat()
        }
        
        service_request.update_status(
            ServiceStatus.DELIVERED,
            f"Bill generated for period {billing_period}",
            new_owner=OwnershipType.SYSTEM,
            metadata={
                "bill_number": bill_number,
                "bill_amount": str(bill["amount"]),
                "due_date": service_request.payload["bill"]["due_date"]
            }
        )
        
        return service_request
    
    def reject_reading(self, service_request: ServiceRequest, 
                      rejection_reason: str) -> ServiceRequest:
        """
        Reject invalid reading
        
        Args:
            service_request: Request in SUBMITTED or PENDING status
            rejection_reason: Why reading was rejected
        
        Returns:
            Updated request with DENIED status
        """
        service_request.payload["verification_status"] = ReadingVerificationStatus.REJECTED.value
        service_request.payload["rejection_reason"] = rejection_reason
        service_request.payload["rejected_at"] = datetime.utcnow().isoformat()
        
        service_request.update_status(
            ServiceStatus.DENIED,
            f"Meter reading rejected: {rejection_reason}",
            new_owner=OwnershipType.DEPARTMENT
        )
        service_request.error_code = ErrorCode.INVALID_DATA
        service_request.error_message = rejection_reason
        
        return service_request
    
    # ========== Helper Methods (would connect to DB in production) ==========
    
    def _get_previous_reading(self, meter_number: str) -> Optional[Decimal]:
        """
        Get last verified reading for this meter
        In production, this would query the database
        """
        # Mock data for demonstration
        mock_readings = {
            "ELEC123456": Decimal("1250.5"),
            "ELEC789012": Decimal("3450.75"),
        }
        return mock_readings.get(meter_number)
    
    def _is_unusual_consumption(self, previous: Decimal, current: Decimal) -> bool:
        """Detect if consumption pattern is unusual (> 2x or < 0.5x normal)"""
        if previous == 0:
            return False
        consumption = current - previous
        # This would compare against historical average in production
        # For now, flag if consumption > 1000 units (suspiciously high)
        return consumption > 1000
    
    def _calculate_bill(self, consumption: Decimal) -> dict:
        """
        Calculate bill amount based on consumption
        Simplified slab rates for demonstration
        """
        # Slab rates (simplified)
        if consumption <= 100:
            rate = 3.50
        elif consumption <= 300:
            rate = 5.00
        elif consumption <= 500:
            rate = 6.50
        else:
            rate = 8.00
        
        # Fixed charges
        fixed_charges = Decimal("100.00")
        
        # Calculate
        variable = consumption * Decimal(str(rate))
        subtotal = fixed_charges + variable
        
        # Tax (18% GST)
        tax = subtotal * Decimal("0.18")
        total = subtotal + tax
        
        return {
            "amount": total,
            "breakdown": {
                "consumption": float(consumption),
                "rate_per_unit": rate,
                "variable_charges": float(variable),
                "fixed_charges": float(fixed_charges),
                "subtotal": float(subtotal),
                "tax_percent": 18,
                "tax_amount": float(tax),
                "total": float(total)
            }
        }
    
    def _get_current_billing_period(self) -> str:
        """Get current billing period in YYYY-MM format"""
        now = datetime.utcnow()
        return now.strftime("%Y-%m")

        
# ============================================================================
# 7. API LAYER (KIOSK Interface)
# ============================================================================

class ElectricityKioskAPI:
    """
    KIOSK API Layer for Electricity Services
    Handles HTTP requests and responses
    """
    
    def __init__(self, service_manager: ElectricityServiceManager):
        self.service_manager = service_manager
    
    def pay_bill(self, user_id: str, meter_number: str, billing_period: str,
                amount: str, payment_method: str) -> Dict[str, Any]:
        """
        API endpoint: POST /api/v1/electricity/pay-bill
        """
        try:
            # Convert amount to Decimal
            amount_decimal = Decimal(amount)
            
            # Create payment request
            request = self.service_manager.pay_bill_service.create_pay_bill_request(
                meter_number, user_id, billing_period, amount_decimal, payment_method
            )
            
            # Submit for payment
            request = self.service_manager.pay_bill_service.submit_payment(request)
            
            # Process payment
            request = self.service_manager.pay_bill_service.process_payment(request)
            
            # Return response
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
    
    def transfer_service(self, old_customer_id: str, new_customer_id: str,
                        meter_number: str, identity_proof: str, ownership_proof: str,
                        consent_doc: str, effective_date: str) -> Dict[str, Any]:
        """
        API endpoint: POST /api/v1/electricity/transfer-service
        """
        try:
            effective_dt = datetime.fromisoformat(effective_date)
            
            request = self.service_manager.transfer_service.create_transfer_request(
                meter_number, old_customer_id, new_customer_id,
                identity_proof, ownership_proof, consent_doc, effective_dt
            )
            
            request = self.service_manager.transfer_service.submit_transfer(request)
            
            return {
                "success": True,
                "service_request_id": request.service_request_id,
                "status": request.status.value,
                "message": "Transfer request submitted. Awaiting department approval."
            }
        
        except Exception as e:
            logger.error(f"Error in transfer_service: {str(e)}")
            return {
                "success": False,
                "error_code": ErrorCode.INTERNAL_ERROR.value,
                "error_message": str(e)
            }
    
    def get_request_status(self, service_request_id: str, user_id: str) -> Dict[str, Any]:
        """
        API endpoint: GET /api/v1/electricity/requests/{id}/status
        """
        # In production, query from database and apply visibility rules
        return {
            "service_request_id": service_request_id,
            "status": "PENDING",
            "message": "Request is being processed"
        }


# ============================================================================
# 8. EXAMPLE USAGE
# ============================================================================

if __name__ == "__main__":
    """
    Example usage demonstrating the service framework
    """
    
    # Initialize manager
    manager = ElectricityServiceManager()
    
    # Example 1: Bill Payment
    print("\n=== EXAMPLE 1: Bill Payment ===")
    bill_request = manager.pay_bill_service.create_pay_bill_request(
        meter_number="ELEC123456",
        customer_id="123456789012",
        billing_period="2026-01",
        amount=Decimal("1500.00"),
        payment_method="UPI"
    )
    print(f"Created request: {bill_request.service_request_id}")
    print(f"Status: {bill_request.status.value}")
    print(f"Payload: {bill_request.payload}\n")
    
    # Submit payment
    bill_request = manager.pay_bill_service.submit_payment(bill_request)
    print(f"After submit - Status: {bill_request.status.value}")
    
    # Process payment
    bill_request = manager.pay_bill_service.process_payment(bill_request)
    print(f"After processing - Status: {bill_request.status.value}")
    
    # Generate receipt
    if bill_request.status == ServiceStatus.DELIVERED:
        receipt = manager.pay_bill_service.generate_receipt(bill_request)
        print(f"Receipt: {receipt}\n")
    
    # Example 2: Service Transfer
    print("\n=== EXAMPLE 2: Service Transfer ===")
    transfer_request = manager.transfer_service.create_transfer_request(
        meter_number="ELEC123456",
        old_customer_id="123456789012",
        new_customer_id="987654321098",
        identity_proof_ref="ID_REF_001",
        ownership_proof_ref="OWN_REF_001",
        consent_ref="CONS_REF_001",
        effective_date=datetime(2026, 3, 1)
    )
    print(f"Created request: {transfer_request.service_request_id}")
    
    # Progress through workflow
    transfer_request = manager.transfer_service.submit_transfer(transfer_request)
    print(f"Submitted - Status: {transfer_request.status.value}")
    
    transfer_request = manager.transfer_service.acknowledge_transfer(transfer_request)
    print(f"Acknowledged - Status: {transfer_request.status.value}")
    
    transfer_request = manager.transfer_service.approve_transfer(transfer_request, "Officer_001")
    print(f"Approved - Status: {transfer_request.status.value}")
    
    # View status history
    print(f"\nStatus History:")
    for entry in transfer_request.status_history:
        print(f"  {entry['timestamp']}: {entry['status']} - {entry['reason']}")
    
    # Export to JSON
    print(f"\nFull Request Data:")
    import json
    print(json.dumps(transfer_request.to_dict(include_history=True), indent=2, default=str))

