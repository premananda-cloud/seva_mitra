"""
SUVIDHA Gas Services Package
============================

A comprehensive service framework for gas utility operations in smart cities.
Implements Service Transfer Framework with state machine lifecycle management.

This package provides:
- Gas-specific service implementations (bill payment, connections, emergencies, safety inspections, etc.)
- State-driven lifecycle management following canonical status set
- Emergency response handling with SLA compliance
- Safety inspection and certification workflows
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

from .Gas_services import (
    # Enums
    ServiceStatus,
    ServiceType,
    ActorRole,
    OwnershipType,
    ErrorCode,
    EmergencySeverity,
    EmergencyType,
    ComplaintCategory,
    ConnectionType,
    InspectionType,
    
    # Core Models
    ServiceRequest,
    
    # Service Implementations
    GasPayBillService,
    GasConnectionRequestService,
    GasMeterChangeService,
    GasSafetyInspectionService,
    GasEmergencyComplaintService,
    GasMeterReadingService,
    GasComplaintService,
    
    # Managers & APIs
    GasServiceManager,
    GasKioskAPI,
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
    "EmergencySeverity",
    "EmergencyType",
    "ComplaintCategory",
    "ConnectionType",
    "InspectionType",
    
    # Core Models
    "ServiceRequest",
    
    # Service Classes
    "GasPayBillService",
    "GasConnectionRequestService",
    "GasMeterChangeService",
    "GasSafetyInspectionService",
    "GasEmergencyComplaintService",
    "GasMeterReadingService",
    "GasComplaintService",
    
    # Managers
    "GasServiceManager",
    
    # APIs
    "GasKioskAPI",
    
    # Package Info
    "__version__",
    "__author__",
    "__license__",
    
    # Helper Functions
    "get_service_types",
    "get_error_descriptions",
    "get_status_flow",
    "get_emergency_sla",
    "version_info",
    "initialize_package",
    "create_kiosk_api",
    "get_service_handler_map",
    "get_emergency_types",
    "get_inspection_types",
]

# ============================================================================
# Convenience Functions
# ============================================================================

def get_service_types() -> dict:
    """
    Returns dictionary of available gas service types with descriptions.
    
    Returns:
        dict: Service type name -> description mapping
    """
    return {
        ServiceType.GAS_PAY_BILL.value: "Gas Bill Payment",
        ServiceType.GAS_CONNECTION_REQUEST.value: "New Gas Connection Request",
        ServiceType.GAS_METER_CHANGE.value: "Gas Meter Change/Replacement",
        ServiceType.GAS_SAFETY_INSPECTION.value: "Gas Safety Inspection",
        ServiceType.GAS_EMERGENCY_COMPLAINT.value: "Gas Emergency Report",
        ServiceType.GAS_METER_READING_SUBMISSION.value: "Gas Meter Reading Submission",
        ServiceType.GAS_COMPLAINT_GRIEVANCE.value: "General Gas Complaint/Grievance",
    }


def get_service_handler_map() -> dict:
    """
    Returns mapping of service types to their handler classes.
    
    Returns:
        dict: ServiceType -> Handler class mapping
    """
    return {
        ServiceType.GAS_PAY_BILL: GasPayBillService,
        ServiceType.GAS_CONNECTION_REQUEST: GasConnectionRequestService,
        ServiceType.GAS_METER_CHANGE: GasMeterChangeService,
        ServiceType.GAS_SAFETY_INSPECTION: GasSafetyInspectionService,
        ServiceType.GAS_EMERGENCY_COMPLAINT: GasEmergencyComplaintService,
        ServiceType.GAS_METER_READING_SUBMISSION: GasMeterReadingService,
        ServiceType.GAS_COMPLAINT_GRIEVANCE: GasComplaintService,
    }


def get_error_descriptions() -> dict:
    """
    Returns human-readable descriptions for gas error codes.
    
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
        ErrorCode.SAFETY_HAZARD: "Safety hazard detected at premises",
        ErrorCode.CAPACITY_LIMIT: "Service capacity limit reached",
        
        # Meter Errors
        ErrorCode.METER_NOT_FOUND: "Meter not found in system",
        ErrorCode.METER_LOCKED: "Meter locked due to disputes/non-payment",
        ErrorCode.METER_MISMATCH: "Meter details do not match",
        ErrorCode.INSTALLATION_FAILED: "Meter installation failed",
        ErrorCode.CERTIFICATION_FAILURE: "Meter certification failed",
        
        # Reading Errors
        ErrorCode.READING_INVALID: "Invalid meter reading submitted",
        ErrorCode.READING_BELOW_PREVIOUS: "Reading lower than previous reading",
        ErrorCode.PHOTO_UNCLEAR: "Meter photo unclear for verification",
        
        # Inspection Errors
        ErrorCode.INSPECTION_OVERDUE: "Safety inspection overdue",
        ErrorCode.SAFETY_HAZARD_DETECTED: "Safety hazards detected during inspection",
        
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


def get_emergency_sla() -> dict:
    """
    Returns SLA response times for different emergency severity levels.
    
    Returns:
        dict: EmergencySeverity -> response time in minutes
    """
    return {
        EmergencySeverity.CRITICAL: 15,   # 15 minutes for critical emergencies
        EmergencySeverity.HIGH: 30,       # 30 minutes for high severity
        EmergencySeverity.LOW: 120,       # 2 hours for low severity
    }


def get_emergency_types() -> dict:
    """
    Returns descriptions for different types of gas emergencies.
    
    Returns:
        dict: EmergencyType -> description
    """
    return {
        EmergencyType.GAS_SMELL: "Smell of gas detected",
        EmergencyType.PIPE_LEAK: "Gas pipe leak detected",
        EmergencyType.PRESSURE_DROP: "Sudden pressure drop in supply",
        EmergencyType.NO_GAS_FLOW: "No gas flow to appliances",
        EmergencyType.HISSING_SOUND: "Hissing sound from pipes/meter",
        EmergencyType.SAFETY_HAZARD: "Visible safety hazard",
    }


def get_inspection_types() -> dict:
    """
    Returns descriptions for different types of safety inspections.
    
    Returns:
        dict: InspectionType -> description
    """
    return {
        InspectionType.PERIODIC: "Routine periodic safety inspection",
        InspectionType.ON_DEMAND: "Customer-requested inspection",
        InspectionType.PRE_ACTIVATION: "Inspection before new connection activation",
    }


def get_complaint_categories() -> dict:
    """
    Returns descriptions for gas complaint categories.
    
    Returns:
        dict: ComplaintCategory -> description
    """
    return {
        ComplaintCategory.BILLING_ISSUE: "Billing related complaint",
        ComplaintCategory.SERVICE_INTERRUPTION: "Service interruption complaint",
        ComplaintCategory.METER_ISSUE: "Meter related complaint",
        ComplaintCategory.PRESSURE_ISSUE: "Gas pressure issue complaint",
        ComplaintCategory.QUALITY_ISSUE: "Gas quality complaint",
        ComplaintCategory.WRONG_CHARGES: "Incorrect charges complaint",
        ComplaintCategory.DISCONNECTION: "Disconnection related complaint",
        ComplaintCategory.OTHER: "Other complaint",
    }


def get_connection_types() -> dict:
    """
    Returns descriptions for gas connection types.
    
    Returns:
        dict: ConnectionType -> description
    """
    return {
        ConnectionType.DOMESTIC: "Domestic/household connection",
        ConnectionType.COMMERCIAL: "Commercial/business connection",
        ConnectionType.INDUSTRIAL: "Industrial connection",
    }


def get_safety_certificate_validity() -> int:
    """
    Returns safety certificate validity period in days.
    
    Returns:
        int: Validity period in days
    """
    return 730  # 2 years (365 * 2)


# ============================================================================
# Package Initialization
# ============================================================================

def initialize_package(db_service=None, payment_gateway=None) -> GasServiceManager:
    """
    Convenience function to initialize the package and return a manager instance.
    
    Args:
        db_service: Database service instance (optional)
        payment_gateway: Payment gateway instance (optional)
    
    Returns:
        GasServiceManager: Initialized service manager
    """
    return GasServiceManager(db_service=db_service, payment_gateway=payment_gateway)


def create_kiosk_api(db_service=None, payment_gateway=None) -> GasKioskAPI:
    """
    Create and return a ready-to-use KIOSK API instance.
    
    Args:
        db_service: Database service instance (optional)
        payment_gateway: Payment gateway instance (optional)
    
    Returns:
        GasKioskAPI: Initialized KIOSK API
    """
    manager = initialize_package(db_service, payment_gateway)
    return GasKioskAPI(manager)


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
        "name": "suvidha-gas-services",
        "version": __version__,
        "author": __author__,
        "license": __license__,
        "description": "Gas utility service framework for SUVIDHA KIOSK system",
        "service_count": len(get_service_types()),
        "supported_services": list(get_service_types().keys()),
        "emergency_types": list(get_emergency_types().keys()),
        "inspection_types": list(get_inspection_types().keys()),
        "safety_cert_validity_days": get_safety_certificate_validity(),
    }


# ============================================================================
# Package-level logging configuration
# ============================================================================

import logging
from datetime import datetime

# Create package logger
logger = logging.getLogger("suvidha_gas_services")

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
# Safety & Compliance Functions
# ============================================================================

def check_safety_guidelines(location_type: str) -> dict:
    """
    Returns safety guidelines for different types of locations.
    
    Args:
        location_type: Type of location (RESIDENTIAL, COMMERCIAL, INDUSTRIAL)
    
    Returns:
        dict: Safety guidelines
    """
    guidelines = {
        "RESIDENTIAL": {
            "inspection_frequency": "Every 2 years",
            "emergency_contacts": ["Fire Department: 101", "Gas Emergency: 1800-XXX-XXXX"],
            "safety_tips": [
                "Install gas leak detectors",
                "Keep gas appliances well-ventilated",
                "Regularly check gas pipelines",
                "Never use open flames near gas sources"
            ]
        },
        "COMMERCIAL": {
            "inspection_frequency": "Every year",
            "emergency_contacts": ["Fire Department: 101", "Gas Emergency: 1800-XXX-XXXX"],
            "safety_tips": [
                "Train staff on gas safety procedures",
                "Maintain proper ventilation systems",
                "Install automatic shut-off valves",
                "Regular safety drills"
            ]
        },
        "INDUSTRIAL": {
            "inspection_frequency": "Every 6 months",
            "emergency_contacts": ["Fire Department: 101", "Gas Emergency: 1800-XXX-XXXX"],
            "safety_tips": [
                "Install multiple gas detectors",
                "Maintain emergency shutdown systems",
                "Regular pipeline integrity testing",
                "24/7 safety monitoring"
            ]
        }
    }
    
    return guidelines.get(location_type.upper(), guidelines["RESIDENTIAL"])


def validate_emergency_severity(issue_type: EmergencyType, symptoms: list) -> EmergencySeverity:
    """
    Validates and suggests emergency severity based on issue type and symptoms.
    
    Args:
        issue_type: Type of gas emergency
        symptoms: List of observed symptoms
    
    Returns:
        EmergencySeverity: Suggested severity level
    """
    # Critical conditions
    critical_indicators = [
        "strong gas smell",
        "hissing sound",
        "visible flames",
        "difficulty breathing",
        "feeling dizzy"
    ]
    
    # High severity conditions
    high_indicators = [
        "mild gas smell",
        "pressure fluctuation",
        "appliance malfunction",
        "unusual sound"
    ]
    
    # Check for critical indicators
    for symptom in symptoms:
        if any(indicator in symptom.lower() for indicator in critical_indicators):
            return EmergencySeverity.CRITICAL
    
    # Check for high severity indicators
    for symptom in symptoms:
        if any(indicator in symptom.lower() for indicator in high_indicators):
            return EmergencySeverity.HIGH
    
    return EmergencySeverity.LOW


def calculate_bill(consumption_units: int, connection_type: ConnectionType) -> dict:
    """
    Calculate gas bill based on consumption and connection type.
    
    Args:
        consumption_units: Units of gas consumed
        connection_type: Type of gas connection
    
    Returns:
        dict: Bill calculation details
    """
    # Rate slabs (mock data - in production, fetch from database)
    rates = {
        ConnectionType.DOMESTIC: {
            "slab1_rate": 30.00,  # First 30 units
            "slab2_rate": 50.00,  # 31-100 units
            "slab3_rate": 75.00,  # Above 100 units
            "fixed_charges": 100.00
        },
        ConnectionType.COMMERCIAL: {
            "rate_per_unit": 85.00,
            "fixed_charges": 200.00
        },
        ConnectionType.INDUSTRIAL: {
            "rate_per_unit": 110.00,
            "fixed_charges": 500.00
        }
    }
    
    rate_info = rates.get(connection_type, rates[ConnectionType.DOMESTIC])
    
    if connection_type == ConnectionType.DOMESTIC:
        if consumption_units <= 30:
            variable_charges = consumption_units * rate_info["slab1_rate"]
        elif consumption_units <= 100:
            variable_charges = (30 * rate_info["slab1_rate"]) + \
                              ((consumption_units - 30) * rate_info["slab2_rate"])
        else:
            variable_charges = (30 * rate_info["slab1_rate"]) + \
                              (70 * rate_info["slab2_rate"]) + \
                              ((consumption_units - 100) * rate_info["slab3_rate"])
    else:
        variable_charges = consumption_units * rate_info["rate_per_unit"]
    
    total_amount = variable_charges + rate_info["fixed_charges"]
    
    return {
        "consumption_units": consumption_units,
        "connection_type": connection_type.value,
        "variable_charges": round(variable_charges, 2),
        "fixed_charges": rate_info["fixed_charges"],
        "total_amount": round(total_amount, 2),
        "tax_rate": "18%",  # GST
        "due_date": (datetime.utcnow() + timedelta(days=15)).strftime("%Y-%m-%d")
    }


# ============================================================================
# Sample Data Generation (for testing/demo)
# ============================================================================

def generate_sample_bill_request() -> ServiceRequest:
    """
    Generate a sample gas bill payment request for testing/demo.
    
    Returns:
        ServiceRequest: Sample bill payment request
    """
    from decimal import Decimal
    
    manager = GasServiceManager()
    return manager.pay_bill_service.create_pay_bill_request(
        consumer_number="GAS789012345",
        customer_id="CUST_001",
        billing_period="2026-01",
        amount=Decimal("2850.50"),
        payment_method="UPI"
    )


def generate_sample_emergency_request() -> ServiceRequest:
    """
    Generate a sample gas emergency request for testing/demo.
    
    Returns:
        ServiceRequest: Sample emergency request
    """
    manager = GasServiceManager()
    return manager.emergency_service.create_emergency_complaint(
        location="123 Main Street, Apt 4B",
        issue_type=EmergencyType.GAS_SMELL,
        severity=EmergencySeverity.CRITICAL,
        consumer_number="GAS789012345"
    )


def generate_sample_inspection_request() -> ServiceRequest:
    """
    Generate a sample safety inspection request for testing/demo.
    
    Returns:
        ServiceRequest: Sample inspection request
    """
    manager = GasServiceManager()
    return manager.safety_inspection_service.create_inspection_request(
        consumer_number="GAS789012345",
        inspection_type=InspectionType.PERIODIC
    )


# Add helper functions to exports
__all__.extend([
    "check_safety_guidelines",
    "validate_emergency_severity",
    "calculate_bill",
    "generate_sample_bill_request",
    "generate_sample_emergency_request",
    "generate_sample_inspection_request",
    "get_complaint_categories",
    "get_connection_types",
    "get_safety_certificate_validity",
])


# ============================================================================
# Emergency Response Protocol
# ============================================================================

def get_emergency_protocol(severity: EmergencySeverity) -> dict:
    """
    Returns emergency response protocol for different severity levels.
    
    Args:
        severity: Emergency severity level
    
    Returns:
        dict: Emergency protocol steps
    """
    protocols = {
        EmergencySeverity.CRITICAL: {
            "immediate_actions": [
                "Evacuate the area immediately",
                "Do not use electrical switches or phones",
                "Turn off gas supply at main valve if safe to do so",
                "Call emergency services"
            ],
            "response_time": "15 minutes",
            "team_size": "2-3 personnel",
            "equipment": [
                "Gas detectors",
                "Emergency shut-off tools",
                "Fire extinguishers",
                "First aid kit"
            ]
        },
        EmergencySeverity.HIGH: {
            "immediate_actions": [
                "Ventilate the area",
                "Turn off gas appliances",
                "Check for obvious leaks",
                "Contact gas emergency line"
            ],
            "response_time": "30 minutes",
            "team_size": "1-2 personnel",
            "equipment": [
                "Gas detectors",
                "Basic repair tools"
            ]
        },
        EmergencySeverity.LOW: {
            "immediate_actions": [
                "Monitor the situation",
                "Check appliance connections",
                "Contact customer service"
            ],
            "response_time": "2 hours",
            "team_size": "1 personnel",
            "equipment": [
                "Basic inspection tools"
            ]
        }
    }
    
    return protocols.get(severity, protocols[EmergencySeverity.LOW])


# ============================================================================
# Safety Checklist
# ============================================================================

def get_safety_checklist(connection_type: ConnectionType) -> list:
    """
    Returns safety checklist items for different connection types.
    
    Args:
        connection_type: Type of gas connection
    
    Returns:
        list: Safety checklist items
    """
    common_items = [
        "Gas meter properly installed and accessible",
        "Pipeline free from corrosion and damage",
        "No gas smell detected",
        "Appliances properly connected",
        "Ventilation adequate",
        "Emergency shut-off valve accessible"
    ]
    
    specific_items = {
        ConnectionType.DOMESTIC: [
            "Kitchen ventilation working",
            "Gas stove/geyser safety certified",
            "Children aware of gas safety"
        ],
        ConnectionType.COMMERCIAL: [
            "Commercial kitchen safety measures",
            "Staff trained in gas safety",
            "Fire safety equipment available"
        ],
        ConnectionType.INDUSTRIAL: [
            "Industrial safety protocols in place",
            "Regular maintenance records available",
            "Emergency response plan documented"
        ]
    }
    
    checklist = common_items + specific_items.get(connection_type, [])
    return [{"item": item, "check": False} for item in checklist]