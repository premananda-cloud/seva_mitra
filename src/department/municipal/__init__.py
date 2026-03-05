"""
src/department/municipal
========================
SUVIDHA Municipal Services Package — KOISK 2026

Provides service implementations for municipal department operations:
  - Property Tax Payment
  - Trade License (new + renewal)
  - Birth / Death Certificates
  - Building Plan Approval
  - Sanitation Complaints
  - General Grievances

Version: 1.0.0
Author:  SUVIDHA 2026 Team
License: MIT
"""

__version__ = "1.0.0"
__author__  = "SUVIDHA 2026 Team"
__license__ = "MIT"

from .municipal_services import (
    # Enums
    ServiceStatus,
    ServiceType,
    ActorRole,
    OwnershipType,
    ErrorCode,

    # Core Model
    ServiceRequest,

    # Service Classes
    MunicipalPropertyTaxService,
    MunicipalTradeLicenseService,
    MunicipalBirthCertService,
    MunicipalDeathCertService,
    MunicipalBuildingPlanService,
    MunicipalComplaintService,
    MunicipalGrievanceService,

    # Manager + Kiosk API
    MunicipalServiceManager,
    MunicipalKioskAPI,
)

import logging

logger = logging.getLogger("suvidha_municipal_services")
if not logger.handlers:
    _h = logging.StreamHandler()
    _h.setFormatter(logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))
    logger.addHandler(_h)
    logger.setLevel(logging.INFO)


# ── Convenience functions ──────────────────────────────────────────────────────

def get_service_types() -> dict:
    return {
        ServiceType.MUNICIPAL_PROPERTY_TAX_PAYMENT.value:  "Property Tax Payment",
        ServiceType.MUNICIPAL_TRADE_LICENSE_NEW.value:      "New Trade License",
        ServiceType.MUNICIPAL_TRADE_LICENSE_RENEWAL.value:  "Trade License Renewal",
        ServiceType.MUNICIPAL_BIRTH_CERTIFICATE.value:      "Birth Certificate",
        ServiceType.MUNICIPAL_DEATH_CERTIFICATE.value:      "Death Certificate",
        ServiceType.MUNICIPAL_BUILDING_PLAN_APPROVAL.value: "Building Plan Approval",
        ServiceType.MUNICIPAL_SANITATION_COMPLAINT.value:   "Sanitation Complaint",
        ServiceType.MUNICIPAL_GENERAL_GRIEVANCE.value:      "General Grievance",
    }


def get_service_handler_map() -> dict:
    return {
        ServiceType.MUNICIPAL_PROPERTY_TAX_PAYMENT:  MunicipalPropertyTaxService,
        ServiceType.MUNICIPAL_TRADE_LICENSE_NEW:      MunicipalTradeLicenseService,
        ServiceType.MUNICIPAL_TRADE_LICENSE_RENEWAL:  MunicipalTradeLicenseService,
        ServiceType.MUNICIPAL_BIRTH_CERTIFICATE:      MunicipalBirthCertService,
        ServiceType.MUNICIPAL_DEATH_CERTIFICATE:      MunicipalDeathCertService,
        ServiceType.MUNICIPAL_BUILDING_PLAN_APPROVAL: MunicipalBuildingPlanService,
        ServiceType.MUNICIPAL_SANITATION_COMPLAINT:   MunicipalComplaintService,
        ServiceType.MUNICIPAL_GENERAL_GRIEVANCE:      MunicipalGrievanceService,
    }


def initialize_package(db_service=None, payment_gateway=None) -> MunicipalServiceManager:
    return MunicipalServiceManager(db_service=db_service, payment_gateway=payment_gateway)


def create_kiosk_api(db_service=None, payment_gateway=None) -> MunicipalKioskAPI:
    manager = initialize_package(db_service, payment_gateway)
    return MunicipalKioskAPI(manager)


def version_info() -> dict:
    return {
        "name":               "suvidha-municipal-services",
        "version":            __version__,
        "author":             __author__,
        "license":            __license__,
        "description":        "Municipal service framework for SUVIDHA KIOSK system",
        "service_count":      len(get_service_types()),
        "supported_services": list(get_service_types().keys()),
    }


__all__ = [
    # Enums
    "ServiceStatus", "ServiceType", "ActorRole", "OwnershipType", "ErrorCode",
    # Model
    "ServiceRequest",
    # Services
    "MunicipalPropertyTaxService", "MunicipalTradeLicenseService",
    "MunicipalBirthCertService", "MunicipalDeathCertService",
    "MunicipalBuildingPlanService", "MunicipalComplaintService",
    "MunicipalGrievanceService",
    # Manager + API
    "MunicipalServiceManager", "MunicipalKioskAPI",
    # Helpers
    "get_service_types", "get_service_handler_map",
    "initialize_package", "create_kiosk_api", "version_info",
    # Package meta
    "__version__", "__author__", "__license__", "logger",
]
