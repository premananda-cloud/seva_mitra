"""
src/department/database/models.py
===================================
Re-exports all ORM models from the canonical models file at
src/database/models.py so that main.py's import:

    from src.department.database.models import (Admin, User, ...)

resolves correctly without duplicating the model definitions.
"""

# All models are defined in src/database/models.py (single source of truth).
# We re-export everything from there.

from src.database.models import (  # noqa: F401
    Base,
    ServiceStatusEnum,
    DepartmentEnum,
    PaymentStatusEnum,
    User,
    Admin,
    ServiceRequest,
    ElectricityMeter,
    WaterConsumer,
    MunicipalConsumer,
    PaymentProfile,
    Payment,
    Refund,
    KioskSession,
    KioskConfig,
)

__all__ = [
    "Base",
    "ServiceStatusEnum",
    "DepartmentEnum",
    "PaymentStatusEnum",
    "User",
    "Admin",
    "ServiceRequest",
    "ElectricityMeter",
    "WaterConsumer",
    "MunicipalConsumer",
    "PaymentProfile",
    "Payment",
    "Refund",
    "KioskSession",
    "KioskConfig",
]
