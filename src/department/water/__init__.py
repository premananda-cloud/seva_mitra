"""
SUVIDHA Water Services Package
=============================

A comprehensive service framework for water utility operations in smart cities.
Implements Service Transfer Framework with state machine lifecycle management.

This package provides:
- Water-specific service implementations (bill payment, connections, leaks, etc.)
- State-driven lifecycle management
- Audit trail and error handling
- KIOSK API layer for citizen interaction

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

from .Water_Services_Complete import (
    # Enums
    ServiceStatus,
    ServiceType,
    ActorRole,
    OwnershipType,
    ErrorCode,
    LeakSeverity,
    LeakType,
    ComplaintCategory,
    ConnectionType,
    
    # Core Models
    ServiceRequest,
    
    # Service Implementations
    WaterPayBillService,
    WaterConnectionRequestService,
    WaterMeterChangeService,
    WaterLeakComplaintService,
    WaterMeterReadingService,
    WaterComplaintService,
    
    # Managers & APIs
    WaterServiceManager,
    WaterKioskAPI,
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
    "LeakSeverity",
    "LeakType",
    "ComplaintCategory",
    "ConnectionType",
    
    # Core Models
    "ServiceRequest",
    
    # Service Classes
    "WaterPayBillService",
    "WaterConnectionRequestService",
    "WaterMeterChangeService", 
    "WaterLeakComplaintService",
    "WaterMeterReadingService",
    "WaterComplaintService",
    
    # Managers
    "WaterServiceManager",
    
    # APIs
    "WaterKioskAPI",
    
    # Package Info
    "__version__",
    "__author__",
    "__license__",
]

# ============================================================================
# Convenience Functions
# ============================================================================

def get_service_types() -> dict:
    """
    Returns dictionary of available water service types with descriptions.
    
    Returns:
        dict: Service type name -> description mapping
    """
    return {
        ServiceType.WATER_PAY_BILL.value: "Water Bill Payment",
        ServiceType.WATER_CONNECTION_REQUEST.value: "New Water Connection Request",
        ServiceType.WATER_METER_CHANGE.value: "Water Meter Change/Replacement",
        ServiceType.WATER_LEAK_COMPLAINT.value: "Water Leak Report",
        ServiceType.WATER_METER_READING_SUBMISSION.value: "Meter Reading Submission",
        ServiceType.WATER_COMPLAINT_GRIEVANCE.value: "General Water Complaint/Grievance",
    }


def get_service_handler_map() -> dict:
    """
    Returns mapping of service types to their handler classes.
    
    Returns:
        dict: ServiceType -> Handler class mapping
    """
    return {
        ServiceType.WATER_PAY_BILL: WaterPayBillService,
        ServiceType.WATER_CONNECTION_REQUEST: WaterConnectionRequestService,
        ServiceType.WATER_METER_CHANGE: WaterMeterChangeService,
        ServiceType.WATER_LEAK_COMPLAINT: WaterLeakComplaintService,
        ServiceType.WATER_METER_READING_SUBMISSION: WaterMeterReadingService,
        ServiceType.WATER_COMPLAINT_GRIEVANCE: WaterComplaintService,
    }


def get_error_descriptions() -> dict:
    """
    Returns human-readable descriptions for error codes.
    
    Returns:
        dict: ErrorCode -> description mapping
    """
    return {
        # User Errors
        ErrorCode.INVALID_DATA: "Invalid data provided",
        ErrorCode.UNAUTHORIZED: "User not authorized for this action",
        ErrorCode.CONFLICT: "Request conflicts with existing data",
        
        # Consumer/Account Errors
        ErrorCode.CONSUMER_NOT_FOUND: "Consumer account not found",
        ErrorCode.ACCOUNT_INACTIVE: "Account is inactive or suspended",
        ErrorCode.BILL_NOT_FOUND: "No bill found for specified period",
        ErrorCode.INSUFFICIENT_AMOUNT: "Payment amount insufficient",
        ErrorCode.PAYMENT_FAILED: "Payment processing failed",
        ErrorCode.DUPLICATE_PAYMENT: "Duplicate payment detected",
        
        # Connection Errors
        ErrorCode.OUT_OF_SERVICE_AREA: "Address outside service area",
        ErrorCode.EXISTING_CONNECTION: "Active connection already exists",
        ErrorCode.DOCUMENT_INVALID: "Required documents invalid or missing",
        ErrorCode.APPLICANT_UNVERIFIED: "Applicant identity not verified",
        ErrorCode.CAPACITY_LIMIT: "Service capacity limit reached",
        
        # Meter Errors
        ErrorCode.METER_NOT_FOUND: "Meter not found in system",
        ErrorCode.METER_LOCKED: "Meter locked due to disputes/non-payment",
        ErrorCode.METER_MISMATCH: "Meter details do not match",
        ErrorCode.INSTALLATION_FAILED: "Meter installation failed",
        ErrorCode.CALIBRATION_FAILURE: "Meter calibration failed",
        
        # Reading Errors
        ErrorCode.READING_INVALID: "Invalid meter reading submitted",
        ErrorCode.READING_BELOW_PREVIOUS: "Reading lower than previous reading",
        ErrorCode.PHOTO_UNCLEAR: "Meter photo unclear for verification",
        
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


# ============================================================================
# Package Initialization
# ============================================================================

def initialize_package(db_service=None, payment_gateway=None) -> WaterServiceManager:
    """
    Convenience function to initialize the package and return a manager instance.
    
    Args:
        db_service: Database service instance (optional)
        payment_gateway: Payment gateway instance (optional)
    
    Returns:
        WaterServiceManager: Initialized service manager
    """
    return WaterServiceManager(db_service=db_service, payment_gateway=payment_gateway)


def create_kiosk_api(db_service=None, payment_gateway=None) -> WaterKioskAPI:
    """
    Create and return a ready-to-use KIOSK API instance.
    
    Args:
        db_service: Database service instance (optional)
        payment_gateway: Payment gateway instance (optional)
    
    Returns:
        WaterKioskAPI: Initialized KIOSK API
    """
    manager = initialize_package(db_service, payment_gateway)
    return WaterKioskAPI(manager)


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
        "name": "suvidha-water-services",
        "version": __version__,
        "author": __author__,
        "license": __license__,
        "description": "Water utility service framework for SUVIDHA KIOSK system",
        "service_count": len(get_service_types()),
        "supported_services": list(get_service_types().keys()),
    }


# ============================================================================
# Package-level logging configuration
# ============================================================================

import logging

# Create package logger
logger = logging.getLogger("suvidha_water_services")

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