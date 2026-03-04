"""
SUVIDHA Electricity Services Package
====================================

A comprehensive service framework for electricity utility operations in smart cities.
Implements Service Transfer Framework with state machine lifecycle management.

This package provides:
- Electricity-specific service implementations (bill payment, transfers, connections, etc.)
- State-driven lifecycle management following canonical status set
- Audit trail and comprehensive error handling
- KIOSK API layer for citizen interaction
- Integration with payment gateways and department systems

Version: 1.0.0
Author: SUVIDHA 2026 Team
License: MIT
"""

__version__ = "1.0.0"
__author__ = "SUVIDHA 2026 Team"
__license__ = "MIT"

# ============================================================================
# Core Exports - Enums & Constants
# ============================================================================

from .Electricity_Services import (
    # Enums
    ServiceStatus,
    ServiceType,
    ActorRole,
    OwnershipType,
    ErrorCode,
    
    # Core Models
    ServiceRequest,
    PaymentDetails,
    MeterInfo,
    BillInfo,
    
    # Validation Service
    ElectricityValidationService,
    
    # Service Implementations
    ElectricityPayBillService,
    ElectricityServiceTransferService,
    ElectricityMeterChangeService,
    ElectricityConnectionRequestService,
    
    # Managers & APIs
    ElectricityServiceManager,
    ElectricityKioskAPI,
)

# ============================================================================
# Package Metadata & Shortcuts
# ============================================================================

__all__ = [
    # Enums
    "ServiceStatus",
    "ServiceType",
    "ActorRole",
    "OwnershipType",
    "ErrorCode",
    
    # Core Models
    "ServiceRequest",
    "PaymentDetails",
    "MeterInfo",
    "BillInfo",
    
    # Services
    "ElectricityValidationService",
    "ElectricityPayBillService",
    "ElectricityServiceTransferService",
    "ElectricityMeterChangeService",
    "ElectricityConnectionRequestService",
    
    # Managers & APIs
    "ElectricityServiceManager",
    "ElectricityKioskAPI",
    
    # Package Info
    "__version__",
    "__author__",
    "__license__",
    
    # Helper Functions
    "get_service_types",
    "get_error_descriptions",
    "get_status_flow",
    "version_info",
    "initialize_package",
    "create_kiosk_api",
    "get_service_handler_map",
]

# ============================================================================
# Convenience Functions
# ============================================================================

def get_service_types() -> dict:
    """
    Returns dictionary of available electricity service types with descriptions.
    
    Returns:
        dict: Service type name -> description mapping
    """
    return {
        ServiceType.ELECTRICITY_PAY_BILL.value: "Electricity Bill Payment",
        ServiceType.ELECTRICITY_SERVICE_TRANSFER.value: "Electricity Service Transfer",
        ServiceType.ELECTRICITY_METER_CHANGE.value: "Electricity Meter Change/Replacement",
        ServiceType.ELECTRICITY_CONNECTION_REQUEST.value: "New Electricity Connection",
        ServiceType.ELECTRICITY_COMPLAINT.value: "Electricity Complaint/Grievance",
        ServiceType.ELECTRICITY_METER_READING_SUBMISSION.value: "Electricity Meter Reading Submission",
    }


def get_service_handler_map() -> dict:
    """
    Returns mapping of service types to their handler classes.
    
    Returns:
        dict: ServiceType -> Handler class mapping
    """
    return {
        ServiceType.ELECTRICITY_PAY_BILL: ElectricityPayBillService,
        ServiceType.ELECTRICITY_SERVICE_TRANSFER: ElectricityServiceTransferService,
        ServiceType.ELECTRICITY_METER_CHANGE: ElectricityMeterChangeService,
        ServiceType.ELECTRICITY_CONNECTION_REQUEST: ElectricityConnectionRequestService,
    }


def get_error_descriptions() -> dict:
    """
    Returns human-readable descriptions for electricity error codes.
    
    Returns:
        dict: ErrorCode -> description mapping
    """
    return {
        # User Errors
        ErrorCode.INVALID_DATA: "Invalid data provided",
        ErrorCode.UNAUTHORIZED: "User not authorized for this action",
        ErrorCode.CONFLICT: "Request conflicts with existing data",
        
        # Meter Errors
        ErrorCode.METER_NOT_FOUND: "Meter not found in system",
        ErrorCode.METER_INACTIVE: "Meter is inactive or suspended",
        ErrorCode.METER_NOT_OWNED_BY_USER: "User does not own this meter",
        
        # Bill Errors
        ErrorCode.BILL_NOT_FOUND: "No bill found for specified period",
        ErrorCode.INSUFFICIENT_AMOUNT: "Payment amount insufficient",
        ErrorCode.PAYMENT_FAILED: "Payment processing failed",
        
        # Transfer Errors
        ErrorCode.PENDING_TRANSFER_EXISTS: "Pending transfer already exists for this meter",
        ErrorCode.TRANSFER_AUTHORIZATION_FAILED: "Transfer authorization failed",
        
        # System Errors
        ErrorCode.DEPARTMENT_TIMEOUT: "Department system timeout",
        ErrorCode.INTEGRATION_FAILURE: "External system integration failure",
        ErrorCode.INTERNAL_ERROR: "Internal system error",
    }


def get_status_flow() -> dict:
    """
    Returns the valid state transitions for service requests.
    
    Returns:
        dict: From status -> list of valid to statuses
    """
    return {
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


def get_status_descriptions() -> dict:
    """
    Returns human-readable descriptions for service statuses.
    
    Returns:
        dict: ServiceStatus -> description mapping
    """
    return {
        ServiceStatus.DRAFT: "Draft - Being prepared by user",
        ServiceStatus.SUBMITTED: "Submitted - Awaiting system acknowledgment",
        ServiceStatus.ACKNOWLEDGED: "Acknowledged - Request received by system",
        ServiceStatus.PENDING: "Pending - Awaiting department action",
        ServiceStatus.APPROVED: "Approved - Authorized for execution",
        ServiceStatus.IN_PROGRESS: "In Progress - Execution underway",
        ServiceStatus.DELIVERED: "Delivered - Service completed successfully",
        ServiceStatus.DENIED: "Denied - Request rejected",
        ServiceStatus.FAILED: "Failed - System error during execution",
        ServiceStatus.CANCELLED: "Cancelled - Withdrawn by user",
    }


def get_ownership_rules() -> dict:
    """
    Returns ownership rules for different service statuses.
    
    Returns:
        dict: Status -> default ownership
    """
    return {
        ServiceStatus.DRAFT: OwnershipType.USER,
        ServiceStatus.SUBMITTED: OwnershipType.SYSTEM,
        ServiceStatus.ACKNOWLEDGED: OwnershipType.SYSTEM,
        ServiceStatus.PENDING: OwnershipType.DEPARTMENT,
        ServiceStatus.APPROVED: OwnershipType.DEPARTMENT,
        ServiceStatus.IN_PROGRESS: OwnershipType.SYSTEM,
        ServiceStatus.DELIVERED: OwnershipType.SYSTEM,
        ServiceStatus.DENIED: OwnershipType.DEPARTMENT,
        ServiceStatus.FAILED: OwnershipType.SYSTEM,
        ServiceStatus.CANCELLED: OwnershipType.USER,
    }


def get_visibility_rules() -> dict:
    """
    Returns status visibility rules for different actor roles.
    
    Returns:
        dict: ActorRole -> list of visible statuses
    """
    return {
        ActorRole.END_USER: [
            ServiceStatus.DRAFT.value,
            ServiceStatus.SUBMITTED.value,
            ServiceStatus.ACKNOWLEDGED.value,
            ServiceStatus.PENDING.value,
            ServiceStatus.APPROVED.value,
            ServiceStatus.IN_PROGRESS.value,
            ServiceStatus.DELIVERED.value,
            ServiceStatus.DENIED.value,
            ServiceStatus.FAILED.value,
            ServiceStatus.CANCELLED.value,
        ],
        ActorRole.DEPARTMENT_OFFICER: [
            ServiceStatus.SUBMITTED.value,
            ServiceStatus.ACKNOWLEDGED.value,
            ServiceStatus.PENDING.value,
            ServiceStatus.APPROVED.value,
            ServiceStatus.IN_PROGRESS.value,
            ServiceStatus.DELIVERED.value,
            ServiceStatus.DENIED.value,
            ServiceStatus.FAILED.value,
        ],
        ActorRole.AUTOMATED_SYSTEM: [
            status.value for status in ServiceStatus
        ],
    }


def get_payment_methods() -> list:
    """
    Returns supported payment methods for electricity bill payments.
    
    Returns:
        list: Supported payment methods
    """
    return [
        "CARD",  # Credit/Debit Card
        "UPI",  # Unified Payments Interface
        "NET_BANKING",  # Net Banking
        "WALLET",  # Digital Wallet (Paytm, PhonePe, etc.)
        "BANK_TRANSFER",  # Bank Transfer/RTGS/NEFT
        "CASH",  # Cash (at counter)
    ]


def get_meter_types() -> list:
    """
    Returns supported electricity meter types.
    
    Returns:
        list: Supported meter types
    """
    return [
        "SINGLE_PHASE",
        "THREE_PHASE",
        "DIGITAL",
        "SMART",
        "PREPAID",
        "POSTPAID",
    ]


# ============================================================================
# Package Initialization
# ============================================================================

def initialize_package(db_service=None, payment_gateway=None) -> ElectricityServiceManager:
    """
    Convenience function to initialize the package and return a manager instance.
    
    Args:
        db_service: Database service instance (optional)
        payment_gateway: Payment gateway instance (optional)
    
    Returns:
        ElectricityServiceManager: Initialized service manager
    """
    return ElectricityServiceManager(db_service=db_service, payment_gateway=payment_gateway)


def create_kiosk_api(db_service=None, payment_gateway=None) -> ElectricityKioskAPI:
    """
    Create and return a ready-to-use KIOSK API instance.
    
    Args:
        db_service: Database service instance (optional)
        payment_gateway: Payment gateway instance (optional)
    
    Returns:
        ElectricityKioskAPI: Initialized KIOSK API
    """
    manager = initialize_package(db_service, payment_gateway)
    return ElectricityKioskAPI(manager)


# ============================================================================
# Version Info
# ============================================================================

def version_info() -> dict:
    """
    Returns comprehensive version information about the package.
    
    Returns:
        dict: Package metadata
    """
    return {
        "name": "suvidha-electricity-services",
        "version": __version__,
        "author": __author__,
        "license": __license__,
        "description": "Electricity utility service framework for SUVIDHA KIOSK system",
        "service_count": len(get_service_types()),
        "supported_services": list(get_service_types().keys()),
        "supported_payment_methods": get_payment_methods(),
        "supported_meter_types": get_meter_types(),
    }


# ============================================================================
# Package-level logging configuration
# ============================================================================

import logging

# Create package logger
logger = logging.getLogger("suvidha_electricity_services")

# Default logging configuration if not already configured
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

# Export logger
__all__.append("logger")


# ============================================================================
# Data Import/Export Utilities
# ============================================================================

def export_service_request(request: ServiceRequest, include_history: bool = True) -> dict:
    """
    Export service request data in a standardized format.
    
    Args:
        request: ServiceRequest instance
        include_history: Whether to include status history
    
    Returns:
        dict: Standardized export data
    """
    data = request.to_dict(include_history=include_history)
    
    # Add additional metadata
    data["_export_metadata"] = {
        "export_timestamp": datetime.utcnow().isoformat(),
        "package_version": __version__,
        "service_type_description": get_service_types().get(data["service_type"], "Unknown"),
    }
    
    return data


def import_service_request(data: dict) -> ServiceRequest:
    """
    Import service request data from exported format.
    
    Args:
        data: Exported service request data
    
    Returns:
        ServiceRequest: Reconstructed service request
    
    Note: This is a simplified implementation. In production,
          you'd need to properly reconstruct all fields.
    """
    from datetime import datetime
    
    # Create basic service request
    request = ServiceRequest(
        service_request_id=data.get("service_request_id"),
        service_type=ServiceType(data["service_type"]),
        initiator_id=data.get("initiator_id"),
        beneficiary_id=data.get("beneficiary_id"),
        status=ServiceStatus(data["status"]),
        created_at=datetime.fromisoformat(data["created_at"]),
        updated_at=datetime.fromisoformat(data["updated_at"]),
        current_owner=OwnershipType(data["current_owner"]),
        correlation_id=data.get("correlation_id"),
        payload=data.get("payload", {}),
        error_code=ErrorCode(data["error_code"]) if data.get("error_code") else None,
        error_message=data.get("error_message"),
    )
    
    # Restore status history if present
    if "status_history" in data:
        request.status_history = data["status_history"]
    
    return request


# ============================================================================
# Sample Data Generation (for testing/demo)
# ============================================================================

def generate_sample_bill_request() -> ServiceRequest:
    """
    Generate a sample bill payment request for testing/demo.
    
    Returns:
        ServiceRequest: Sample bill payment request
    """
    from decimal import Decimal
    
    manager = ElectricityServiceManager()
    return manager.pay_bill_service.create_pay_bill_request(
        meter_number="ELEC789012345",
        customer_id="123456789012",
        billing_period="2026-01",
        amount=Decimal("1850.50"),
        payment_method="UPI"
    )


def generate_sample_transfer_request() -> ServiceRequest:
    """
    Generate a sample service transfer request for testing/demo.
    
    Returns:
        ServiceRequest: Sample transfer request
    """
    from datetime import datetime, timedelta
    
    manager = ElectricityServiceManager()
    return manager.transfer_service.create_transfer_request(
        meter_number="ELEC789012345",
        old_customer_id="123456789012",
        new_customer_id="987654321098",
        identity_proof_ref="AADHAR_REF_001",
        ownership_proof_ref="PROPERTY_DEED_001",
        consent_ref="CONSENT_FORM_001",
        effective_date=datetime.utcnow() + timedelta(days=30)
    )


# Add sample data functions to exports
__all__.extend([
    "export_service_request",
    "import_service_request",
    "generate_sample_bill_request",
    "generate_sample_transfer_request",
])