"""
api/main.py
============
KOISK Unified FastAPI Backend — SUVIDHA 2026

Departments:   Electricity  |  Water  |  Municipal (new)
Payment:       Mock (default) | PortOne | Razorpay
Admin:         Super-admin | Department admin | Merchant setup

Fixes applied vs original koisk_api.py:
  ✅ payment_router now registered (was missing)
  ✅ Single Base — all models in one file
  ✅ Municipal department added
  ✅ Admin API with JWT scoping
  ✅ Mock payment works per department without real keys
  ✅ GET /api/v1/{dept}/bills endpoint added
"""

import logging
import os
import random
import secrets
import hashlib
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from fastapi import Depends, FastAPI, Header, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from src.department.database.database import get_db, init_db
from src.department.database.models import (
    Admin, ElectricityMeter, MunicipalConsumer, Payment,
    ServiceRequest as ServiceRequestModel, User, WaterConsumer,
    KioskSession, KioskConfig,
)
from ..payment.payment_handler import (
    CompletePaymentRequest, CustomerRegisterRequest, ErrorResponse,
    InitiatePaymentRequest, handle_portone_webhook, handle_razorpay_webhook,
    svc_get_history, svc_get_status, svc_register_customer,
    verify_portone_webhook, verify_razorpay_webhook,
    create_razorpay_customer_with_key,
)
from src.payment.mock_payment_engine import svc_complete, svc_initiate

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ─── App ──────────────────────────────────────────────────────────────────────

app = FastAPI(
    title="KOISK Utility Services API",
    description="Electricity · Water · Municipal — with mock payment support",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "http://localhost:5173").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup():
    init_db()
    logger.info("✅ KOISK API started")


# ─── Auth helpers ─────────────────────────────────────────────────────────────

SECRET_KEY = os.getenv("SECRET_KEY", "koisk-dev-secret-change-in-production")
ALGORITHM  = "HS256"

try:
    from jose import JWTError, jwt
    from passlib.context import CryptContext
    _pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")
    JWT_AVAILABLE = True
except ImportError:
    JWT_AVAILABLE = False
    logger.warning("python-jose / passlib not installed — auth endpoints disabled")


def _verify_password(plain: str, hashed: str) -> bool:
    if not JWT_AVAILABLE:
        return plain == "Admin@1234"   # dev fallback
    return _pwd.verify(plain, hashed)


def _create_token(data: dict, expires_minutes: int = 480) -> str:
    if not JWT_AVAILABLE:
        return "dev-token"
    payload = {**data, "exp": datetime.utcnow() + timedelta(minutes=expires_minutes)}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def _decode_token(token: str) -> Dict:
    if not JWT_AVAILABLE:
        return {"sub": "dev", "role": "super_admin", "department": None}
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired token")


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/admin/login", auto_error=False)


def get_current_admin(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> Admin:
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    payload  = _decode_token(token)
    username = payload.get("sub")
    admin    = db.query(Admin).filter(Admin.username == username).first()
    if not admin or not admin.is_active:
        raise HTTPException(status_code=401, detail="Admin not found or inactive")
    return admin


def require_super_admin(admin: Admin = Depends(get_current_admin)) -> Admin:
    if admin.role != "super_admin":
        raise HTTPException(status_code=403, detail="Super admin access required")
    return admin


def require_dept_access(dept: str, admin: Admin = Depends(get_current_admin)) -> Admin:
    """Allow if super_admin OR if the admin's department matches."""
    if admin.role == "super_admin":
        return admin
    if admin.department != dept:
        raise HTTPException(status_code=403, detail=f"No access to {dept} department")
    return admin


# ─── Common Pydantic models ───────────────────────────────────────────────────

class ServiceStatusResponse(BaseModel):
    service_request_id: str
    department:         str
    service_type:       str
    status:             str
    payload:            Dict[str, Any] = {}
    created_at:         datetime
    updated_at:         datetime
    completed_at:       Optional[datetime] = None
    error_code:         Optional[str]      = None
    error_message:      Optional[str]      = None
    payment_id:         Optional[str]      = None


class SuccessResponse(BaseModel):
    success:            bool
    service_request_id: str
    department:         str
    status:             str
    message:            Optional[str] = None
    data:               Optional[Dict[str, Any]] = None


# ─── Helper: save ServiceRequest to DB ───────────────────────────────────────

def _save_request(
    db:         Session,
    req_id:     str,
    dept:       str,
    stype:      str,
    status_str: str,
    payload:    Dict,
    user_id:    Optional[int] = None,
    payment_id: Optional[str] = None,
) -> ServiceRequestModel:
    row = ServiceRequestModel(
        service_request_id=req_id,
        department=dept,
        service_type=stype,
        status=status_str,
        payload=payload,
        user_id=user_id,
        payment_id=payment_id,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    logger.info(f"[DB] Saved request {req_id}  dept={dept}  type={stype}  status={status_str}")
    return row


def _to_response(row: ServiceRequestModel) -> ServiceStatusResponse:
    return ServiceStatusResponse(
        service_request_id=row.service_request_id,
        department=row.department,
        service_type=row.service_type,
        status=row.status,
        payload=row.payload or {},
        created_at=row.created_at,
        updated_at=row.updated_at,
        completed_at=row.completed_at,
        error_code=row.error_code,
        error_message=row.error_message,
        payment_id=row.payment_id,
    )


# ─── Health ───────────────────────────────────────────────────────────────────

@app.get("/health", tags=["Health"])
async def health():
    return {
        "status":    "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "mock_payment": os.getenv("MOCK_PAYMENT", "true"),
        "departments": ["electricity", "water", "municipal"],
    }


# =============================================================================
# ADMIN AUTH
# =============================================================================

class AdminLoginResponse(BaseModel):
    access_token: str
    token_type:   str = "bearer"
    role:         str
    department:   Optional[str]
    admin_id:     int


@app.post("/admin/login", tags=["Admin"], response_model=AdminLoginResponse)
async def admin_login(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """Authenticate an admin/department officer and return a JWT."""
    admin = db.query(Admin).filter(Admin.username == form.username).first()
    if not admin or not _verify_password(form.password, admin.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    if not admin.is_active:
        raise HTTPException(status_code=403, detail="Account disabled")

    token = _create_token({"sub": admin.username, "role": admin.role, "department": admin.department})
    admin.last_login = datetime.utcnow()
    db.commit()

    return AdminLoginResponse(
        access_token=token, role=admin.role,
        department=admin.department, admin_id=admin.id
    )


# =============================================================================
# ADMIN — SERVICE REQUEST MANAGEMENT (all departments)
# =============================================================================

@app.get("/admin/requests", tags=["Admin"])
async def admin_list_all_requests(
    department: Optional[str] = None,
    status:     Optional[str] = None,
    limit:      int = 50,
    offset:     int = 0,
    admin:      Admin = Depends(get_current_admin),
    db:         Session = Depends(get_db),
):
    """List all service requests. Dept-admin sees only their department."""
    q = db.query(ServiceRequestModel)

    # Scope by admin's department if not super_admin
    if admin.role != "super_admin" and admin.department:
        q = q.filter(ServiceRequestModel.department == admin.department)
    elif department:
        q = q.filter(ServiceRequestModel.department == department)

    if status:
        q = q.filter(ServiceRequestModel.status == status.upper())

    total = q.count()
    rows  = q.order_by(ServiceRequestModel.created_at.desc()).offset(offset).limit(limit).all()

    return {
        "total":    total,
        "limit":    limit,
        "offset":   offset,
        "requests": [_to_response(r) for r in rows],
    }


@app.get("/admin/requests/{request_id}", tags=["Admin"])
async def admin_get_request(
    request_id: str,
    admin:      Admin = Depends(get_current_admin),
    db:         Session = Depends(get_db),
):
    row = db.query(ServiceRequestModel).filter(
        ServiceRequestModel.service_request_id == request_id
    ).first()
    if not row:
        raise HTTPException(status_code=404, detail="Request not found")
    if admin.role != "super_admin" and admin.department and row.department != admin.department:
        raise HTTPException(status_code=403, detail="Access denied")
    return _to_response(row)


class AdminUpdateStatusBody(BaseModel):
    status:       str
    note:         Optional[str] = None
    error_code:   Optional[str] = None
    error_message: Optional[str] = None


@app.patch("/admin/requests/{request_id}/status", tags=["Admin"])
async def admin_update_request_status(
    request_id: str,
    body:       AdminUpdateStatusBody,
    admin:      Admin = Depends(get_current_admin),
    db:         Session = Depends(get_db),
):
    """Approve, deny, mark in-progress, or deliver a service request."""
    row = db.query(ServiceRequestModel).filter(
        ServiceRequestModel.service_request_id == request_id
    ).first()
    if not row:
        raise HTTPException(status_code=404, detail="Request not found")
    if admin.role != "super_admin" and admin.department and row.department != admin.department:
        raise HTTPException(status_code=403, detail="Access denied")

    row.status           = body.status.upper()
    row.handled_by_admin = admin.id
    row.updated_at       = datetime.utcnow()
    if body.error_code:
        row.error_code    = body.error_code
    if body.error_message:
        row.error_message = body.error_message
    if row.status in ("DELIVERED", "FAILED", "CANCELLED"):
        row.completed_at = datetime.utcnow()

    db.commit()
    return {"success": True, "service_request_id": request_id, "new_status": row.status}


@app.get("/admin/payments", tags=["Admin"])
async def admin_list_payments(
    department: Optional[str] = None,
    status:     Optional[str] = None,
    limit:      int = 50,
    offset:     int = 0,
    admin:      Admin = Depends(get_current_admin),
    db:         Session = Depends(get_db),
):
    """View payment records. Scoped to admin's department automatically."""
    q = db.query(Payment)
    if admin.role != "super_admin" and admin.department:
        q = q.filter(Payment.department == admin.department)
    elif department:
        q = q.filter(Payment.department == department)
    if status:
        q = q.filter(Payment.status == status.lower())

    total = q.count()
    rows  = q.order_by(Payment.created_at.desc()).offset(offset).limit(limit).all()
    return {
        "total":    total,
        "payments": [
            {
                "id":          r.id,
                "userId":      r.user_id,
                "dept":        r.department,
                "amount":      float(r.amount),
                "status":      r.status,
                "gateway":     r.gateway,
                "method":      r.payment_method,
                "referenceNo": r.reference_no,
                "consumerNo":  r.consumer_number,
                "paidAt":      r.paid_at.isoformat() if r.paid_at else None,
                "createdAt":   r.created_at.isoformat(),
            }
            for r in rows
        ],
    }


# =============================================================================
# ADMIN — MERCHANT / PAYMENT SETUP
# =============================================================================

class MerchantSetupBody(BaseModel):
    gateway:      str              # portone | razorpay
    merchant_id:  str
    channel_key:  Optional[str] = None
    api_key:      Optional[str] = None
    notes:        Optional[str] = None


@app.post("/admin/merchant/setup", tags=["Admin"])
async def admin_merchant_setup(
    body:  MerchantSetupBody,
    admin: Admin = Depends(get_current_admin),
    db:    Session = Depends(get_db),
):
    """
    Store merchant payment gateway config for this admin/department.
    This is what you call to 'set up the merchant' after onboarding with PortOne/Razorpay.
    Super-admins can configure org-wide; dept-admins configure their own department.
    """
    config = {
        "gateway":     body.gateway,
        "merchant_id": body.merchant_id,
        "channel_key": body.channel_key,
        "notes":       body.notes,
        "configured_at": datetime.utcnow().isoformat(),
    }
    if body.api_key:
        # Store obfuscated (never return in plain)
        config["api_key_hint"] = f"****{body.api_key[-4:]}"

    admin.merchant_config = config
    admin.role = "merchant" if admin.role == "department_admin" else admin.role
    db.commit()

    return {
        "success":    True,
        "admin_id":   admin.id,
        "department": admin.department,
        "gateway":    body.gateway,
        "merchant_id": body.merchant_id,
        "message":    "Merchant payment config saved successfully",
    }


@app.get("/admin/merchant/config", tags=["Admin"])
async def admin_get_merchant_config(
    admin: Admin = Depends(get_current_admin),
    db:    Session = Depends(get_db),
):
    """Return the merchant's stored payment configuration (api keys obfuscated)."""
    cfg = admin.merchant_config or {}
    return {
        "admin_id":   admin.id,
        "department": admin.department,
        "role":       admin.role,
        "gateway":    cfg.get("gateway"),
        "merchant_id": cfg.get("merchant_id"),
        "channel_key": cfg.get("channel_key"),
        "configured_at": cfg.get("configured_at"),
    }


# =============================================================================
# ELECTRICITY ENDPOINTS
# =============================================================================

class ElectricityPayBillRequest(BaseModel):
    user_id:        str
    meter_number:   str
    billing_period: str
    amount:         float
    payment_method: str
    gateway:        str = "mock"


class ElectricityTransferRequest(BaseModel):
    old_customer_id: str
    new_customer_id: str
    meter_number:    str
    identity_proof:  str
    ownership_proof: str
    consent_doc:     str
    effective_date:  str


class ElectricityMeterChangeRequest(BaseModel):
    user_id:          str
    meter_number:     str
    reason:           str
    new_meter_number: Optional[str] = None


class ElectricityConnectionRequest(BaseModel):
    customer_name:   str
    customer_id:     str
    address:         str
    load_requirement: str
    identity_proof:  str
    address_proof:   str


@app.get("/api/v1/electricity/bills/{user_id}", tags=["Electricity"])
async def electricity_get_bills(user_id: str, db: Session = Depends(get_db)):
    """Return pending bills for a user's electricity meter."""
    meters = db.query(ElectricityMeter).join(User).filter(
        User.username == user_id
    ).all()
    # Also try direct meter lookup if user_id looks like a meter number
    bills = []
    for m in meters:
        if m.outstanding_amount > 0:
            bills.append({
                "id":            f"BILL-ELEC-{m.meter_number}",
                "dept":          "electricity",
                "consumerNo":    m.meter_number,
                "amountDue":     m.outstanding_amount,
                "billMonth":     datetime.utcnow().strftime("%Y-%m"),
                "dueDate":       (datetime.utcnow() + timedelta(days=10)).strftime("%Y-%m-%d"),
                "status":        "UNPAID",
            })
    return {"userId": user_id, "bills": bills}


@app.post("/api/v1/electricity/pay-bill", response_model=SuccessResponse, tags=["Electricity"])
async def electricity_pay_bill(req: ElectricityPayBillRequest, db: Session = Depends(get_db)):
    import uuid as _uuid
    internal_id = str(_uuid.uuid4())

    # Initiate payment
    pay_result = await svc_initiate(
        internal_id=internal_id,
        user_id=req.user_id,
        bill_id=f"BILL-ELEC-{req.meter_number}-{req.billing_period}",
        department="electricity",
        amount=req.amount,
        method=req.payment_method,
        gateway=req.gateway,
        db=db,
        consumer_number=req.meter_number,
        billing_period=req.billing_period,
    )

    # Auto-complete for mock gateway
    if pay_result.get("isMock"):
        mock_pay_id = f"pay_mock_{_uuid.uuid4().hex[:10]}"
        complete_result = await svc_complete(
            payment_id=internal_id,
            order_id=pay_result["orderId"],
            gateway="mock",
            gateway_payment_id=mock_pay_id,
            db=db,
        )
        payment_id = internal_id
    else:
        complete_result = pay_result
        payment_id = internal_id

    # Save service request
    row = _save_request(
        db=db, req_id=str(_uuid.uuid4()),
        dept="electricity", stype="ELECTRICITY_PAY_BILL",
        status_str="DELIVERED" if pay_result.get("isMock") else "SUBMITTED",
        payload={
            "user_id": req.user_id, "meter_number": req.meter_number,
            "billing_period": req.billing_period, "amount": req.amount,
            "payment_method": req.payment_method,
        },
        payment_id=payment_id,
    )

    return SuccessResponse(
        success=True,
        service_request_id=row.service_request_id,
        department="electricity",
        status=row.status,
        message="Bill payment processed",
        data=complete_result.get("receipt") or pay_result,
    )


@app.post("/api/v1/electricity/transfer-service", response_model=SuccessResponse, tags=["Electricity"])
async def electricity_transfer_service(req: ElectricityTransferRequest, db: Session = Depends(get_db)):
    import uuid as _uuid
    row = _save_request(
        db=db, req_id=str(_uuid.uuid4()),
        dept="electricity", stype="ELECTRICITY_SERVICE_TRANSFER",
        status_str="SUBMITTED",
        payload=req.dict(),
    )
    return SuccessResponse(success=True, service_request_id=row.service_request_id,
                           department="electricity", status=row.status,
                           message="Transfer request submitted. Awaiting department approval.")


@app.post("/api/v1/electricity/meter-change", response_model=SuccessResponse, tags=["Electricity"])
async def electricity_meter_change(req: ElectricityMeterChangeRequest, db: Session = Depends(get_db)):
    import uuid as _uuid
    row = _save_request(
        db=db, req_id=str(_uuid.uuid4()),
        dept="electricity", stype="ELECTRICITY_METER_CHANGE",
        status_str="SUBMITTED", payload=req.dict(),
    )
    return SuccessResponse(success=True, service_request_id=row.service_request_id,
                           department="electricity", status=row.status,
                           message="Meter change request submitted")


@app.post("/api/v1/electricity/new-connection", response_model=SuccessResponse, tags=["Electricity"])
async def electricity_new_connection(req: ElectricityConnectionRequest, db: Session = Depends(get_db)):
    import uuid as _uuid
    row = _save_request(
        db=db, req_id=str(_uuid.uuid4()),
        dept="electricity", stype="ELECTRICITY_CONNECTION_REQUEST",
        status_str="SUBMITTED", payload=req.dict(),
    )
    return SuccessResponse(success=True, service_request_id=row.service_request_id,
                           department="electricity", status=row.status,
                           message="New connection request submitted")


# =============================================================================
# WATER ENDPOINTS
# =============================================================================

class WaterPayBillRequest(BaseModel):
    user_id:         str
    consumer_number: str
    billing_period:  str
    amount:          float
    payment_method:  str
    gateway:         str = "mock"


class WaterConnectionRequest(BaseModel):
    applicant_name: str
    applicant_id:   str
    address:        str
    property_type:  str
    identity_proof: str
    address_proof:  str


class WaterLeakComplaintRequest(BaseModel):
    consumer_id:     str
    consumer_number: str
    complaint_type:  str
    location:        str
    severity:        str
    description:     Optional[str] = None


@app.get("/api/v1/water/bills/{user_id}", tags=["Water"])
async def water_get_bills(user_id: str, db: Session = Depends(get_db)):
    consumers = db.query(WaterConsumer).join(User).filter(User.username == user_id).all()
    bills = []
    for c in consumers:
        if c.outstanding_amount > 0:
            bills.append({
                "id":         f"BILL-WATER-{c.consumer_number}",
                "dept":       "water",
                "consumerNo": c.consumer_number,
                "amountDue":  c.outstanding_amount,
                "billMonth":  datetime.utcnow().strftime("%Y-%m"),
                "dueDate":    (datetime.utcnow() + timedelta(days=10)).strftime("%Y-%m-%d"),
                "status":     "UNPAID",
            })
    return {"userId": user_id, "bills": bills}


@app.post("/api/v1/water/pay-bill", response_model=SuccessResponse, tags=["Water"])
async def water_pay_bill(req: WaterPayBillRequest, db: Session = Depends(get_db)):
    import uuid as _uuid
    internal_id = str(_uuid.uuid4())
    pay_result = await svc_initiate(
        internal_id=internal_id, user_id=req.user_id,
        bill_id=f"BILL-WATER-{req.consumer_number}-{req.billing_period}",
        department="water", amount=req.amount,
        method=req.payment_method, gateway=req.gateway, db=db,
        consumer_number=req.consumer_number, billing_period=req.billing_period,
    )
    complete_result = {}
    if pay_result.get("isMock"):
        complete_result = await svc_complete(
            payment_id=internal_id, order_id=pay_result["orderId"],
            gateway="mock", gateway_payment_id=f"pay_mock_{_uuid.uuid4().hex[:10]}", db=db,
        )
    row = _save_request(
        db=db, req_id=str(_uuid.uuid4()),
        dept="water", stype="WATER_PAY_BILL",
        status_str="DELIVERED" if pay_result.get("isMock") else "SUBMITTED",
        payload=req.dict(), payment_id=internal_id,
    )
    return SuccessResponse(success=True, service_request_id=row.service_request_id,
                           department="water", status=row.status,
                           message="Water bill payment processed",
                           data=complete_result.get("receipt") or pay_result)


@app.post("/api/v1/water/new-connection", response_model=SuccessResponse, tags=["Water"])
async def water_new_connection(req: WaterConnectionRequest, db: Session = Depends(get_db)):
    import uuid as _uuid
    row = _save_request(db=db, req_id=str(_uuid.uuid4()),
                        dept="water", stype="WATER_CONNECTION_REQUEST",
                        status_str="SUBMITTED", payload=req.dict())
    return SuccessResponse(success=True, service_request_id=row.service_request_id,
                           department="water", status=row.status,
                           message="Connection request submitted")


@app.post("/api/v1/water/leak-complaint", response_model=SuccessResponse, tags=["Water"])
async def water_leak_complaint(req: WaterLeakComplaintRequest, db: Session = Depends(get_db)):
    import uuid as _uuid
    row = _save_request(db=db, req_id=str(_uuid.uuid4()),
                        dept="water", stype="WATER_LEAK_COMPLAINT",
                        status_str="SUBMITTED", payload=req.dict())
    return SuccessResponse(success=True, service_request_id=row.service_request_id,
                           department="water", status=row.status,
                           message="Leak complaint submitted. Team will attend shortly.")


# =============================================================================
# MUNICIPAL ENDPOINTS  (new department)
# =============================================================================

class MunicipalPropertyTaxRequest(BaseModel):
    user_id:         str
    consumer_number: str
    property_id:     str
    tax_year:        str     # e.g. "2025-2026"
    amount:          float
    payment_method:  str
    gateway:         str = "mock"


class MunicipalTradeLicenseRequest(BaseModel):
    applicant_id:    str
    applicant_name:  str
    business_name:   str
    business_type:   str
    address:         str
    ward_number:     str
    identity_proof:  str
    address_proof:   str
    is_renewal:      bool = False
    existing_license_no: Optional[str] = None


class MunicipalBirthCertRequest(BaseModel):
    applicant_id:    str
    child_name:      str
    dob:             str
    place_of_birth:  str
    father_name:     str
    mother_name:     str
    hospital_name:   Optional[str] = None
    identity_proof:  str


class MunicipalDeathCertRequest(BaseModel):
    applicant_id:      str
    deceased_name:     str
    date_of_death:     str
    place_of_death:    str
    cause_of_death:    str
    informant_name:    str
    identity_proof:    str
    medical_certificate: str


class MunicipalBuildingPlanRequest(BaseModel):
    applicant_id:         str
    applicant_name:       str
    property_id:          str
    plot_area:            float
    built_up_area:        float
    floors:               int
    building_type:        str
    architect_name:       str
    identity_proof:       str
    land_ownership_proof: str
    blueprint_ref:        str


class MunicipalComplaintRequest(BaseModel):
    consumer_id:        str
    complaint_category: str
    location:           str
    ward_number:        str
    description:        str
    severity:           str = "Medium"
    photo_ref:          Optional[str] = None


class MunicipalGrievanceRequest(BaseModel):
    citizen_id:  str
    subject:     str
    description: str
    dept_ref:    Optional[str] = None
    attachment:  Optional[str] = None


@app.get("/api/v1/municipal/bills/{user_id}", tags=["Municipal"])
async def municipal_get_bills(user_id: str, db: Session = Depends(get_db)):
    consumers = db.query(MunicipalConsumer).join(User).filter(User.username == user_id).all()
    bills = []
    for c in consumers:
        if c.outstanding_amount > 0:
            bills.append({
                "id":          f"BILL-MUNI-{c.consumer_number}",
                "dept":        "municipal",
                "consumerNo":  c.consumer_number,
                "propertyId":  c.property_id,
                "wardNumber":  c.ward_number,
                "amountDue":   c.outstanding_amount,
                "taxYear":     f"{datetime.utcnow().year}-{datetime.utcnow().year+1}",
                "status":      "UNPAID",
            })
    return {"userId": user_id, "bills": bills}


@app.post("/api/v1/municipal/property-tax", response_model=SuccessResponse, tags=["Municipal"])
async def municipal_property_tax(req: MunicipalPropertyTaxRequest, db: Session = Depends(get_db)):
    import uuid as _uuid
    internal_id = str(_uuid.uuid4())
    pay_result = await svc_initiate(
        internal_id=internal_id, user_id=req.user_id,
        bill_id=f"BILL-MUNI-{req.property_id}-{req.tax_year}",
        department="municipal", amount=req.amount,
        method=req.payment_method, gateway=req.gateway, db=db,
        consumer_number=req.consumer_number, billing_period=req.tax_year,
    )
    complete_result = {}
    if pay_result.get("isMock"):
        complete_result = await svc_complete(
            payment_id=internal_id, order_id=pay_result["orderId"],
            gateway="mock", gateway_payment_id=f"pay_mock_{_uuid.uuid4().hex[:10]}", db=db,
        )
    row = _save_request(
        db=db, req_id=str(_uuid.uuid4()),
        dept="municipal", stype="MUNICIPAL_PROPERTY_TAX_PAYMENT",
        status_str="DELIVERED" if pay_result.get("isMock") else "SUBMITTED",
        payload=req.dict(), payment_id=internal_id,
    )
    return SuccessResponse(success=True, service_request_id=row.service_request_id,
                           department="municipal", status=row.status,
                           message="Property tax payment processed",
                           data=complete_result.get("receipt") or pay_result)


@app.post("/api/v1/municipal/trade-license", response_model=SuccessResponse, tags=["Municipal"])
async def municipal_trade_license(req: MunicipalTradeLicenseRequest, db: Session = Depends(get_db)):
    import uuid as _uuid
    stype = "MUNICIPAL_TRADE_LICENSE_RENEWAL" if req.is_renewal else "MUNICIPAL_TRADE_LICENSE_NEW"
    row = _save_request(db=db, req_id=str(_uuid.uuid4()),
                        dept="municipal", stype=stype,
                        status_str="SUBMITTED", payload=req.dict())
    return SuccessResponse(success=True, service_request_id=row.service_request_id,
                           department="municipal", status=row.status,
                           message=f"Trade license {'renewal' if req.is_renewal else 'application'} submitted")


@app.post("/api/v1/municipal/birth-certificate", response_model=SuccessResponse, tags=["Municipal"])
async def municipal_birth_certificate(req: MunicipalBirthCertRequest, db: Session = Depends(get_db)):
    import uuid as _uuid
    row = _save_request(db=db, req_id=str(_uuid.uuid4()),
                        dept="municipal", stype="MUNICIPAL_BIRTH_CERTIFICATE",
                        status_str="SUBMITTED", payload=req.dict())
    return SuccessResponse(success=True, service_request_id=row.service_request_id,
                           department="municipal", status=row.status,
                           message="Birth certificate request submitted")


@app.post("/api/v1/municipal/death-certificate", response_model=SuccessResponse, tags=["Municipal"])
async def municipal_death_certificate(req: MunicipalDeathCertRequest, db: Session = Depends(get_db)):
    import uuid as _uuid
    row = _save_request(db=db, req_id=str(_uuid.uuid4()),
                        dept="municipal", stype="MUNICIPAL_DEATH_CERTIFICATE",
                        status_str="SUBMITTED", payload=req.dict())
    return SuccessResponse(success=True, service_request_id=row.service_request_id,
                           department="municipal", status=row.status,
                           message="Death certificate request submitted")


@app.post("/api/v1/municipal/building-plan", response_model=SuccessResponse, tags=["Municipal"])
async def municipal_building_plan(req: MunicipalBuildingPlanRequest, db: Session = Depends(get_db)):
    import uuid as _uuid
    row = _save_request(db=db, req_id=str(_uuid.uuid4()),
                        dept="municipal", stype="MUNICIPAL_BUILDING_PLAN_APPROVAL",
                        status_str="SUBMITTED", payload=req.dict())
    return SuccessResponse(success=True, service_request_id=row.service_request_id,
                           department="municipal", status=row.status,
                           message="Building plan approval request submitted")


@app.post("/api/v1/municipal/complaint", response_model=SuccessResponse, tags=["Municipal"])
async def municipal_complaint(req: MunicipalComplaintRequest, db: Session = Depends(get_db)):
    import uuid as _uuid
    row = _save_request(db=db, req_id=str(_uuid.uuid4()),
                        dept="municipal", stype="MUNICIPAL_SANITATION_COMPLAINT",
                        status_str="SUBMITTED", payload=req.dict())
    return SuccessResponse(success=True, service_request_id=row.service_request_id,
                           department="municipal", status=row.status,
                           message="Complaint registered successfully")


@app.post("/api/v1/municipal/grievance", response_model=SuccessResponse, tags=["Municipal"])
async def municipal_grievance(req: MunicipalGrievanceRequest, db: Session = Depends(get_db)):
    import uuid as _uuid
    row = _save_request(db=db, req_id=str(_uuid.uuid4()),
                        dept="municipal", stype="MUNICIPAL_GENERAL_GRIEVANCE",
                        status_str="SUBMITTED", payload=req.dict())
    return SuccessResponse(success=True, service_request_id=row.service_request_id,
                           department="municipal", status=row.status,
                           message="Grievance submitted — you will receive a response within 7 working days")


# =============================================================================
# SHARED: request status lookup
# =============================================================================

@app.get("/api/v1/requests/{request_id}", response_model=ServiceStatusResponse, tags=["Shared"])
async def get_request_status(request_id: str, db: Session = Depends(get_db)):
    row = db.query(ServiceRequestModel).filter(
        ServiceRequestModel.service_request_id == request_id
    ).first()
    if not row:
        raise HTTPException(status_code=404, detail=f"Request {request_id} not found")
    return _to_response(row)


@app.get("/api/v1/requests/user/{user_id}", tags=["Shared"])
async def get_user_requests(
    user_id:    str,
    department: Optional[str] = None,
    db:         Session = Depends(get_db),
):
    q = db.query(ServiceRequestModel).filter(ServiceRequestModel.user_id == user_id)
    if department:
        q = q.filter(ServiceRequestModel.department == department)
    rows = q.order_by(ServiceRequestModel.created_at.desc()).all()
    return {"userId": user_id, "total": len(rows), "requests": [_to_response(r) for r in rows]}


# =============================================================================
# KIOSK — DEPARTMENT + SERVICE CATALOGUE
# =============================================================================

# Static service catalogue — what each active department offers on the kiosk.
# Loaded once at startup; admin can toggle departments via /admin/kiosk-config.

_DEPARTMENT_CATALOGUE: Dict[str, Dict] = {
    "water": {
        "label":       "Water",
        "icon":        "💧",
        "description": "Water supply & utilities",
        "services": [
            {"id": "WATER_PAY_BILL",                  "label": "Pay Bill",              "has_payment": True},
            {"id": "WATER_CONNECTION_REQUEST",         "label": "New Connection",         "has_payment": False},
            {"id": "WATER_METER_CHANGE",               "label": "Meter Change",           "has_payment": False},
            {"id": "WATER_LEAK_COMPLAINT",             "label": "Report Leak",            "has_payment": False},
            {"id": "WATER_METER_READING_SUBMISSION",   "label": "Submit Meter Reading",   "has_payment": False},
            {"id": "WATER_COMPLAINT_GRIEVANCE",        "label": "Complaint / Grievance",  "has_payment": False},
        ],
    },
    "electricity": {
        "label":       "Electricity",
        "icon":        "⚡",
        "description": "Electricity supply & metering",
        "services": [
            {"id": "ELECTRICITY_PAY_BILL",                 "label": "Pay Bill",              "has_payment": True},
            {"id": "ELECTRICITY_CONNECTION_REQUEST",        "label": "New Connection",         "has_payment": False},
            {"id": "ELECTRICITY_METER_CHANGE",              "label": "Meter Change",           "has_payment": False},
            {"id": "ELECTRICITY_SERVICE_TRANSFER",          "label": "Transfer Service",       "has_payment": False},
            {"id": "ELECTRICITY_METER_READING_SUBMISSION",  "label": "Submit Meter Reading",   "has_payment": False},
            {"id": "ELECTRICITY_COMPLAINT",                 "label": "Complaint / Grievance",  "has_payment": False},
        ],
    },
    "municipal": {
        "label":       "Municipal",
        "icon":        "🏛️",
        "description": "Municipal services & certificates",
        "services": [
            {"id": "MUNICIPAL_PROPERTY_TAX_PAYMENT",  "label": "Pay Property Tax",       "has_payment": True},
            {"id": "MUNICIPAL_TRADE_LICENSE_NEW",      "label": "New Trade License",      "has_payment": False},
            {"id": "MUNICIPAL_TRADE_LICENSE_RENEWAL",  "label": "Renew Trade License",    "has_payment": False},
            {"id": "MUNICIPAL_BIRTH_CERTIFICATE",      "label": "Birth Certificate",      "has_payment": False},
            {"id": "MUNICIPAL_DEATH_CERTIFICATE",      "label": "Death Certificate",      "has_payment": False},
            {"id": "MUNICIPAL_BUILDING_PLAN_APPROVAL", "label": "Building Plan Approval", "has_payment": False},
            {"id": "MUNICIPAL_SANITATION_COMPLAINT",   "label": "Sanitation Complaint",   "has_payment": False},
            {"id": "MUNICIPAL_GENERAL_GRIEVANCE",      "label": "General Grievance",      "has_payment": False},
        ],
    },
}


@app.get("/kiosk/departments", tags=["Kiosk"])
async def kiosk_list_departments(db: Session = Depends(get_db)):
    """
    Return all active departments and their service lists.
    Active status comes from kiosk_config; defaults to True if no config row exists yet.
    Also returns the global kiosk display settings (name, location, language).
    """
    result   = []
    configs  = {row.department: row for row in db.query(KioskConfig).all()}
    global_cfg = configs.get("global")

    for dept_key, catalogue in _DEPARTMENT_CATALOGUE.items():
        cfg      = configs.get(dept_key)
        is_active = cfg.is_active if cfg else True   # default active if no config row yet
        razorpay_configured = bool(cfg and cfg.razorpay_key_id)

        result.append({
            "id":                   dept_key,
            "label":                catalogue["label"],
            "icon":                 catalogue["icon"],
            "description":          catalogue["description"],
            "is_active":            is_active,
            "razorpay_configured":  razorpay_configured,
            "razorpay_mode":        cfg.razorpay_mode if cfg else "test",
            "services":             catalogue["services"] if is_active else [],
        })

    return {
        "departments": result,
        "kiosk_settings": global_cfg.settings if global_cfg else {},
    }


# =============================================================================
# KIOSK — SESSION (identity + OTP + Razorpay customer)
# =============================================================================

# ── OTP helpers ───────────────────────────────────────────────────────────────

OTP_EXPIRY_SECONDS  = int(os.getenv("OTP_EXPIRY_SECS",   "300"))   # 5 min default
SESSION_TTL_SECONDS = int(os.getenv("SESSION_TTL_SECS", "1800"))   # 30 min default
MAX_OTP_ATTEMPTS    = 3


def _generate_otp() -> str:
    """6-digit numeric OTP."""
    return f"{random.SystemRandom().randint(0, 999999):06d}"


def _hash_otp(otp: str) -> str:
    """SHA-256 hash so we never store plaintext OTPs."""
    return hashlib.sha256(otp.encode()).hexdigest()


def _new_session_token() -> str:
    return secrets.token_urlsafe(32)


def _send_otp_sms(phone: str, otp: str) -> None:
    """
    Stub for SMS dispatch.
    Replace with your SMS provider (Twilio, MSG91, Fast2SMS, etc.).
    In dev/test the OTP is logged to console so you can use it without a real SMS gateway.
    """
    logger.info(f"[OTP] ☎  Sending OTP {otp} to {phone}  (integrate SMS provider here)")


def _get_dept_razorpay_keys(db: Session, department: str) -> tuple[str, str]:
    """
    Return (key_id, key_secret) for the given department.
    Falls back to env vars if no DB config row exists (useful in dev).
    """
    from ..payment.payment_handler import RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET
    cfg = db.query(KioskConfig).filter(KioskConfig.department == department).first()
    if cfg and cfg.razorpay_key_id and cfg.razorpay_key_secret:
        return cfg.razorpay_key_id, cfg.razorpay_key_secret
    # Fallback to global env vars
    return RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET


# ── Pydantic models ───────────────────────────────────────────────────────────

class KioskSessionStartRequest(BaseModel):
    full_name:    str
    phone_number: str   # E.164 preferred: +91XXXXXXXXXX
    email:        Optional[str] = None
    kiosk_id:     Optional[str] = None


class KioskSessionStartResponse(BaseModel):
    session_id:       int
    is_returning_user: bool
    otp_sent:         bool
    message:          str


class KioskOTPVerifyRequest(BaseModel):
    session_id: int
    otp_code:   str


class KioskOTPVerifyResponse(BaseModel):
    success:              bool
    session_token:        str
    razorpay_customer_id: Optional[str]
    full_name:            str
    is_returning_user:    bool
    message:              str


class KioskSessionEndRequest(BaseModel):
    session_token: str


# ── Routes ────────────────────────────────────────────────────────────────────

@app.post("/kiosk/session/start", response_model=KioskSessionStartResponse, tags=["Kiosk"])
async def kiosk_session_start(req: KioskSessionStartRequest, db: Session = Depends(get_db)):
    """
    Step 1 of the user flow.

    - Looks up existing session by phone number.
    - If returning user: issues a fresh OTP but keeps their razorpay_customer_id.
    - If new user: creates a new KioskSession row.
    - Sends OTP via SMS (stubbed — replace with real SMS provider).
    """
    # Check for an existing verified session with this phone (returning user)
    existing = (
        db.query(KioskSession)
        .filter(
            KioskSession.phone_number == req.phone_number,
            KioskSession.is_verified  == True,               # noqa: E712
        )
        .order_by(KioskSession.started_at.desc())
        .first()
    )

    otp = _generate_otp()

    if existing:
        # Returning user — create a fresh session row but copy over the Razorpay ID
        session = KioskSession(
            full_name            = req.full_name or existing.full_name,
            phone_number         = req.phone_number,
            email                = req.email or existing.email,
            otp_code             = _hash_otp(otp),
            otp_sent_at          = datetime.utcnow(),
            otp_attempts         = 0,
            is_verified          = False,
            razorpay_customer_id = existing.razorpay_customer_id,  # reuse
            is_returning_user    = True,
            kiosk_id             = req.kiosk_id,
        )
    else:
        # New user
        session = KioskSession(
            full_name         = req.full_name,
            phone_number      = req.phone_number,
            email             = req.email,
            otp_code          = _hash_otp(otp),
            otp_sent_at       = datetime.utcnow(),
            otp_attempts      = 0,
            is_verified       = False,
            is_returning_user = False,
            kiosk_id          = req.kiosk_id,
        )

    db.add(session)
    db.commit()
    db.refresh(session)

    _send_otp_sms(req.phone_number, otp)

    return KioskSessionStartResponse(
        session_id        = session.id,
        is_returning_user = session.is_returning_user,
        otp_sent          = True,
        message           = (
            "Welcome back! OTP sent to your registered number."
            if session.is_returning_user else
            "OTP sent to your phone number."
        ),
    )


@app.post("/kiosk/session/verify-otp", response_model=KioskOTPVerifyResponse, tags=["Kiosk"])
async def kiosk_session_verify_otp(req: KioskOTPVerifyRequest, db: Session = Depends(get_db)):
    """
    Step 2 of the user flow.

    - Validates OTP (with attempt limiting and expiry).
    - On success for new users: creates Razorpay customer using the first active
      department's key (Water → Electricity → Municipal fallback order).
    - Issues a session_token valid for SESSION_TTL_SECONDS.
    - Returns the session_token + razorpay_customer_id to the frontend.
    """
    session = db.query(KioskSession).filter(KioskSession.id == req.session_id).first()

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if session.is_verified:
        raise HTTPException(status_code=400, detail="Session already verified")

    # Check OTP expiry
    if session.otp_sent_at:
        age = (datetime.utcnow() - session.otp_sent_at).total_seconds()
        if age > OTP_EXPIRY_SECONDS:
            raise HTTPException(status_code=400, detail="OTP has expired. Please restart.")

    # Check attempt limit
    if session.otp_attempts >= MAX_OTP_ATTEMPTS:
        raise HTTPException(
            status_code=429,
            detail=f"Too many incorrect attempts. Please restart the session.",
        )

    # Verify OTP
    if session.otp_code != _hash_otp(req.otp_code):
        session.otp_attempts += 1
        db.commit()
        remaining = MAX_OTP_ATTEMPTS - session.otp_attempts
        raise HTTPException(
            status_code=400,
            detail=f"Incorrect OTP. {remaining} attempt(s) remaining.",
        )

    # ── OTP correct ──────────────────────────────────────────────────────────

    razorpay_customer_id = session.razorpay_customer_id  # may already exist (returning user)

    if not razorpay_customer_id:
        # New user — create Razorpay customer.
        # Use the first active department's key (Water → Electricity → Municipal).
        key_id, key_secret = "", ""
        for dept in ("water", "electricity", "municipal"):
            key_id, key_secret = _get_dept_razorpay_keys(db, dept)
            if key_id:
                break

        try:
            razorpay_customer_id = await create_razorpay_customer_with_key(
                name       = session.full_name,
                contact    = session.phone_number,
                email      = session.email or "",
                key_id     = key_id,
                key_secret = key_secret,
                notes      = {"source": "koisk_kiosk", "phone": session.phone_number},
            )
            logger.info(f"[kiosk] Razorpay customer created: {razorpay_customer_id}")
        except ValueError as exc:
            # Non-fatal — log and continue without a customer ID
            logger.error(f"[kiosk] Razorpay customer creation failed: {exc}")
            razorpay_customer_id = None

    # Issue session token
    token      = _new_session_token()
    expires_at = datetime.utcnow() + timedelta(seconds=SESSION_TTL_SECONDS)

    session.is_verified          = True
    session.otp_verified_at      = datetime.utcnow()
    session.razorpay_customer_id = razorpay_customer_id
    session.session_token        = token
    session.session_expires_at   = expires_at
    db.commit()

    return KioskOTPVerifyResponse(
        success              = True,
        session_token        = token,
        razorpay_customer_id = razorpay_customer_id,
        full_name            = session.full_name,
        is_returning_user    = session.is_returning_user,
        message              = "Identity verified. Welcome to SUVIDHA Kiosk.",
    )


@app.post("/kiosk/session/end", tags=["Kiosk"])
async def kiosk_session_end(req: KioskSessionEndRequest, db: Session = Depends(get_db)):
    """
    Called when user taps Done / Exit.
    Marks the session as ended. Kiosk resets to the Welcome screen.
    """
    session = (
        db.query(KioskSession)
        .filter(KioskSession.session_token == req.session_token)
        .first()
    )
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    session.ended_at      = datetime.utcnow()
    session.session_token = None   # invalidate token immediately
    db.commit()

    return {"success": True, "message": "Session ended. Goodbye!"}


@app.get("/kiosk/session/validate", tags=["Kiosk"])
async def kiosk_session_validate(
    session_token: str,
    db: Session = Depends(get_db),
):
    """
    Lightweight token check — called by the frontend before any service request
    to confirm the session is still valid (not expired, not ended).
    """
    session = (
        db.query(KioskSession)
        .filter(
            KioskSession.session_token == session_token,
            KioskSession.is_verified   == True,            # noqa: E712
        )
        .first()
    )
    if not session:
        raise HTTPException(status_code=401, detail="Invalid or expired session token")

    if session.ended_at:
        raise HTTPException(status_code=401, detail="Session has ended")

    if session.session_expires_at and datetime.utcnow() > session.session_expires_at:
        raise HTTPException(status_code=401, detail="Session has expired")

    return {
        "valid":                 True,
        "full_name":             session.full_name,
        "phone_number":          session.phone_number,
        "razorpay_customer_id":  session.razorpay_customer_id,
        "is_returning_user":     session.is_returning_user,
        "session_expires_at":    session.session_expires_at.isoformat(),
    }


# =============================================================================
# ADMIN — KIOSK CONFIG (Razorpay keys per department + global settings)
# =============================================================================

class KioskConfigSetRequest(BaseModel):
    department:         str                   # electricity | water | municipal | global
    razorpay_key_id:    Optional[str] = None
    razorpay_key_secret: Optional[str] = None
    razorpay_mode:      Optional[str] = "test"   # 'test' | 'live'
    is_active:          Optional[bool] = None
    settings:           Optional[Dict[str, Any]] = None   # freeform kiosk settings


class KioskConfigResponse(BaseModel):
    department:            str
    razorpay_key_id_hint:  Optional[str]
    razorpay_mode:         Optional[str]
    is_active:             bool
    settings:              Dict[str, Any]
    configured_at:         Optional[str]


@app.post("/admin/kiosk-config", tags=["Admin"], response_model=KioskConfigResponse)
async def admin_set_kiosk_config(
    body:  KioskConfigSetRequest,
    admin: Admin = Depends(require_super_admin),
    db:    Session = Depends(get_db),
):
    """
    Set or update Razorpay keys and kiosk settings for a department.
    Only super_admins may call this endpoint.

    Razorpay keys are stored server-side; only the last-4-char hint is returned.
    Pass razorpay_key_secret=null to leave the existing secret unchanged.

    Example — configure Water department:
        POST /admin/kiosk-config
        { "department": "water",
          "razorpay_key_id": "rzp_test_XXXX",
          "razorpay_key_secret": "XXXX",
          "razorpay_mode": "test",
          "is_active": true }

    Example — set global kiosk display settings:
        POST /admin/kiosk-config
        { "department": "global",
          "settings": { "kiosk_name": "Ward 5 SUVIDHA", "default_language": "hi" } }
    """
    valid_departments = {"water", "electricity", "municipal", "global"}
    if body.department not in valid_departments:
        raise HTTPException(
            status_code=400,
            detail=f"department must be one of {sorted(valid_departments)}",
        )

    cfg = db.query(KioskConfig).filter(KioskConfig.department == body.department).first()
    if not cfg:
        cfg = KioskConfig(department=body.department)
        db.add(cfg)

    # Update Razorpay keys
    if body.razorpay_key_id is not None:
        cfg.razorpay_key_id      = body.razorpay_key_id
        cfg.razorpay_key_id_hint = f"****{body.razorpay_key_id[-4:]}" if len(body.razorpay_key_id) >= 4 else body.razorpay_key_id

    if body.razorpay_key_secret is not None:
        # TODO: encrypt before storing (use Fernet / AWS KMS / Vault in production)
        cfg.razorpay_key_secret = body.razorpay_key_secret

    if body.razorpay_mode is not None:
        if body.razorpay_mode not in ("test", "live"):
            raise HTTPException(status_code=400, detail="razorpay_mode must be 'test' or 'live'")
        cfg.razorpay_mode = body.razorpay_mode

    if body.is_active is not None:
        cfg.is_active = body.is_active

    # Deep-merge settings (don't wipe existing keys not mentioned in this call)
    if body.settings:
        existing_settings      = cfg.settings or {}
        cfg.settings           = {**existing_settings, **body.settings}

    cfg.configured_by_admin = admin.id
    cfg.updated_at          = datetime.utcnow()
    db.commit()
    db.refresh(cfg)

    logger.info(f"[admin/kiosk-config] {body.department} updated by admin {admin.username}")

    return KioskConfigResponse(
        department           = cfg.department,
        razorpay_key_id_hint = cfg.razorpay_key_id_hint,
        razorpay_mode        = cfg.razorpay_mode,
        is_active            = cfg.is_active,
        settings             = cfg.settings or {},
        configured_at        = cfg.updated_at.isoformat(),
    )


@app.get("/admin/kiosk-config", tags=["Admin"])
async def admin_get_kiosk_config(
    admin: Admin = Depends(require_super_admin),
    db:    Session = Depends(get_db),
):
    """
    Return all department kiosk configs (Razorpay keys obfuscated).
    Only super_admins may call this.
    """
    rows = db.query(KioskConfig).order_by(KioskConfig.department).all()
    return {
        "configs": [
            KioskConfigResponse(
                department           = r.department,
                razorpay_key_id_hint = r.razorpay_key_id_hint,
                razorpay_mode        = r.razorpay_mode,
                is_active            = r.is_active,
                settings             = r.settings or {},
                configured_at        = r.updated_at.isoformat() if r.updated_at else None,
            )
            for r in rows
        ]
    }


@app.get("/admin/kiosk-config/{department}", tags=["Admin"], response_model=KioskConfigResponse)
async def admin_get_kiosk_config_dept(
    department: str,
    admin:      Admin = Depends(require_super_admin),
    db:         Session = Depends(get_db),
):
    """Get config for a single department."""
    cfg = db.query(KioskConfig).filter(KioskConfig.department == department).first()
    if not cfg:
        raise HTTPException(status_code=404, detail=f"No config found for department '{department}'")
    return KioskConfigResponse(
        department           = cfg.department,
        razorpay_key_id_hint = cfg.razorpay_key_id_hint,
        razorpay_mode        = cfg.razorpay_mode,
        is_active            = cfg.is_active,
        settings             = cfg.settings or {},
        configured_at        = cfg.updated_at.isoformat() if cfg.updated_at else None,
    )


# =============================================================================
# PAYMENTS
# =============================================================================

@app.post("/api/v1/payments/customer/register", tags=["Payments"])
async def register_customer(req: CustomerRegisterRequest, db: Session = Depends(get_db)):
    return await svc_register_customer(req, db)


@app.post("/api/v1/payments/initiate", tags=["Payments"])
async def initiate_payment(req: InitiatePaymentRequest, db: Session = Depends(get_db)):
    import uuid as _uuid
    internal_id = str(_uuid.uuid4())
    return await svc_initiate(
        internal_id=internal_id, user_id=req.userId,
        bill_id=req.billId, department=req.dept,
        amount=req.amount, currency=req.currency,
        method=req.method, gateway=req.gateway, db=db,
        consumer_number=req.consumerNumber,
        billing_period=req.billingPeriod,
    )


@app.post("/api/v1/payments/complete", tags=["Payments"])
async def complete_payment(req: CompletePaymentRequest, db: Session = Depends(get_db)):
    return await svc_complete(
        payment_id=req.paymentId, order_id=req.orderId,
        gateway=req.gateway, gateway_payment_id=req.gatewayPaymentId,
        razorpay_signature=req.razorpaySignature, db=db,
    )


@app.get("/api/v1/payments/status/{payment_id}", tags=["Payments"])
async def payment_status(payment_id: str, db: Session = Depends(get_db)):
    return await svc_get_status(payment_id, db)


@app.get("/api/v1/payments/history/{user_id}", tags=["Payments"])
async def payment_history(user_id: str, db: Session = Depends(get_db)):
    return await svc_get_history(user_id, db)


@app.post("/api/v1/payments/webhook", include_in_schema=False)
async def payment_webhook(
    request: Request,
    db:      Session = Depends(get_db),
    x_razorpay_signature: str = Header(default=""),
    x_portone_signature:  str = Header(default=""),
):
    body = await request.body()
    if x_razorpay_signature:
        if not verify_razorpay_webhook(body, x_razorpay_signature):
            raise HTTPException(status_code=400, detail="Invalid Razorpay signature")
        payload    = await request.json()
        event_type = payload.get("event", "")
        return await handle_razorpay_webhook(event_type, payload, db)
    elif x_portone_signature:
        if not verify_portone_webhook(body, x_portone_signature):
            raise HTTPException(status_code=400, detail="Invalid PortOne signature")
        payload    = await request.json()
        event_type = payload.get("type", payload.get("status", ""))
        return await handle_portone_webhook(event_type, payload, db)
    return {"received": True}
