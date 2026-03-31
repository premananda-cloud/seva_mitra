"""
src/api/admin/router.py
=======================
Admin auth, registration, user management, merchant setup, and kiosk-config endpoints.

Auth endpoints (all /admin/*  — localhost-only via middleware in main.py):
  POST   /admin/login                  — get JWT
  POST   /admin/register               — super_admin creates a new admin
  GET    /admin/users                  — list all admins (super_admin only)
  PATCH  /admin/users/{id}/password    — change own password or super_admin changes anyone's
  PATCH  /admin/users/{id}/deactivate  — deactivate an admin (super_admin only)
  PATCH  /admin/users/{id}/activate    — re-activate an admin (super_admin only)
  DELETE /admin/users/{id}             — permanently delete (super_admin only)
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr, field_validator
from sqlalchemy.orm import Session

from src.department.database.database import get_db
from src.department.database.models import Admin, Payment, ServiceRequest as ServiceRequestModel, KioskConfig
from src.api.shared.deps import (
    verify_password, create_token, hash_password,
    get_current_admin, require_super_admin,
)
from src.api.shared.utils import to_response

router = APIRouter(tags=["Admin"])


# ─── Shared response schema ───────────────────────────────────────────────────

def _admin_out(a: Admin) -> dict:
    return {
        "id":          a.id,
        "username":    a.username,
        "email":       a.email,
        "full_name":   a.full_name,
        "role":        a.role,
        "department":  a.department,
        "is_active":   a.is_active,
        "created_at":  a.created_at.isoformat() if a.created_at else None,
        "last_login":  a.last_login.isoformat() if a.last_login else None,
    }


# ─── Auth ─────────────────────────────────────────────────────────────────────

class AdminLoginResponse(BaseModel):
    access_token: str
    token_type:   str = "bearer"
    role:         str
    department:   Optional[str]
    admin_id:     int


@router.post("/admin/login", response_model=AdminLoginResponse)
async def admin_login(
    form: OAuth2PasswordRequestForm = Depends(),
    db:   Session = Depends(get_db),
):
    """Authenticate an admin and return a JWT."""
    admin = db.query(Admin).filter(Admin.username == form.username).first()
    if not admin or not verify_password(form.password, admin.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    if not admin.is_active:
        raise HTTPException(status_code=403, detail="Account disabled — contact a super admin")

    token = create_token({"sub": admin.username, "role": admin.role, "department": admin.department})
    admin.last_login = datetime.utcnow()
    db.commit()

    return AdminLoginResponse(
        access_token=token, role=admin.role,
        department=admin.department, admin_id=admin.id,
    )


# ─── Register ─────────────────────────────────────────────────────────────────

class AdminRegisterBody(BaseModel):
    username:   str
    email:      str
    full_name:  str
    password:   str
    role:       str = "department_admin"   # "department_admin" | "super_admin"
    department: Optional[str] = None       # required for department_admin

    @field_validator("role")
    @classmethod
    def valid_role(cls, v):
        allowed = {"super_admin", "department_admin"}
        if v not in allowed:
            raise ValueError(f"role must be one of {allowed}")
        return v

    @field_validator("department")
    @classmethod
    def dept_required_for_dept_admin(cls, v, info):
        role = info.data.get("role", "")
        if role == "department_admin" and not v:
            raise ValueError("department is required for department_admin")
        valid_depts = {"electricity", "water", "gas", "municipal"}
        if v and v not in valid_depts:
            raise ValueError(f"department must be one of {sorted(valid_depts)}")
        return v

    @field_validator("password")
    @classmethod
    def strong_password(cls, v):
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        return v

    @field_validator("username")
    @classmethod
    def username_format(cls, v):
        v = v.strip()
        if len(v) < 3:
            raise ValueError("Username must be at least 3 characters")
        if not v.replace("_", "").replace("-", "").isalnum():
            raise ValueError("Username may only contain letters, numbers, hyphens, underscores")
        return v


@router.post("/admin/register", status_code=201)
async def admin_register(
    body:  AdminRegisterBody,
    admin: Admin = Depends(require_super_admin),
    db:    Session = Depends(get_db),
):
    """
    Create a new admin account. Only super_admins may call this.
    department_admin must be scoped to one department.
    super_admin has no department restriction.
    """
    if db.query(Admin).filter(Admin.username == body.username).first():
        raise HTTPException(status_code=409, detail="Username already taken")
    if db.query(Admin).filter(Admin.email == body.email).first():
        raise HTTPException(status_code=409, detail="Email already registered")

    new_admin = Admin(
        username        = body.username,
        email           = body.email,
        full_name       = body.full_name,
        hashed_password = hash_password(body.password),
        role            = body.role,
        department      = body.department if body.role == "department_admin" else None,
        is_active       = True,
        created_at      = datetime.utcnow(),
    )
    db.add(new_admin)
    db.commit()
    db.refresh(new_admin)

    return {"success": True, "admin": _admin_out(new_admin)}


# ─── List admins ──────────────────────────────────────────────────────────────

@router.get("/admin/users")
async def admin_list_users(
    admin: Admin = Depends(require_super_admin),
    db:    Session = Depends(get_db),
):
    """Return all admin accounts. super_admin only."""
    rows = db.query(Admin).order_by(Admin.created_at.desc()).all()
    return {"total": len(rows), "admins": [_admin_out(a) for a in rows]}


# ─── Change password ──────────────────────────────────────────────────────────

class ChangePasswordBody(BaseModel):
    current_password: Optional[str] = None   # required when changing own password
    new_password:     str

    @field_validator("new_password")
    @classmethod
    def strong(cls, v):
        if len(v) < 8:
            raise ValueError("New password must be at least 8 characters")
        return v


@router.patch("/admin/users/{target_id}/password")
async def change_password(
    target_id: int,
    body:      ChangePasswordBody,
    admin:     Admin = Depends(get_current_admin),
    db:        Session = Depends(get_db),
):
    """
    Change password.
    - Own account: current_password required.
    - Super admin changing someone else's: current_password not required.
    """
    target = db.query(Admin).filter(Admin.id == target_id).first()
    if not target:
        raise HTTPException(status_code=404, detail="Admin not found")

    is_own   = admin.id == target_id
    is_super = admin.role == "super_admin"

    if not is_super and not is_own:
        raise HTTPException(status_code=403, detail="You can only change your own password")

    if is_own:
        if not body.current_password:
            raise HTTPException(status_code=400, detail="current_password required")
        if not verify_password(body.current_password, target.hashed_password):
            raise HTTPException(status_code=401, detail="Current password is incorrect")

    target.hashed_password = hash_password(body.new_password)
    target.updated_at      = datetime.utcnow()
    db.commit()

    return {"success": True, "message": "Password updated"}


# ─── Deactivate / Activate ────────────────────────────────────────────────────

@router.patch("/admin/users/{target_id}/deactivate")
async def deactivate_admin(
    target_id: int,
    admin:     Admin = Depends(require_super_admin),
    db:        Session = Depends(get_db),
):
    """Disable an admin account. super_admin only. Cannot deactivate yourself."""
    target = db.query(Admin).filter(Admin.id == target_id).first()
    if not target:
        raise HTTPException(status_code=404, detail="Admin not found")
    if target.id == admin.id:
        raise HTTPException(status_code=400, detail="Cannot deactivate your own account")

    target.is_active  = False
    target.updated_at = datetime.utcnow()
    db.commit()
    return {"success": True, "message": f"{target.username} deactivated"}


@router.patch("/admin/users/{target_id}/activate")
async def activate_admin(
    target_id: int,
    admin:     Admin = Depends(require_super_admin),
    db:        Session = Depends(get_db),
):
    """Re-enable a deactivated admin. super_admin only."""
    target = db.query(Admin).filter(Admin.id == target_id).first()
    if not target:
        raise HTTPException(status_code=404, detail="Admin not found")

    target.is_active  = True
    target.updated_at = datetime.utcnow()
    db.commit()
    return {"success": True, "message": f"{target.username} activated"}


# ─── Delete ───────────────────────────────────────────────────────────────────

@router.delete("/admin/users/{target_id}")
async def delete_admin(
    target_id: int,
    admin:     Admin = Depends(require_super_admin),
    db:        Session = Depends(get_db),
):
    """Permanently delete an admin. super_admin only. Cannot delete yourself."""
    target = db.query(Admin).filter(Admin.id == target_id).first()
    if not target:
        raise HTTPException(status_code=404, detail="Admin not found")
    if target.id == admin.id:
        raise HTTPException(status_code=400, detail="Cannot delete your own account")

    db.delete(target)
    db.commit()
    return {"success": True, "message": f"{target.username} permanently deleted"}


# ─── Service Request Management ───────────────────────────────────────────────

@router.get("/admin/requests")
async def admin_list_all_requests(
    department: Optional[str] = None,
    status:     Optional[str] = None,
    limit:      int = 50,
    offset:     int = 0,
    admin:      Admin = Depends(get_current_admin),
    db:         Session = Depends(get_db),
):
    q = db.query(ServiceRequestModel)
    if admin.role != "super_admin" and admin.department:
        q = q.filter(ServiceRequestModel.department == admin.department)
    elif department:
        q = q.filter(ServiceRequestModel.department == department)
    if status:
        q = q.filter(ServiceRequestModel.status == status.upper())

    total = q.count()
    rows  = q.order_by(ServiceRequestModel.created_at.desc()).offset(offset).limit(limit).all()
    return {"total": total, "limit": limit, "offset": offset, "requests": [to_response(r) for r in rows]}


@router.get("/admin/requests/{request_id}")
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
    return to_response(row)


class AdminUpdateStatusBody(BaseModel):
    status:        str
    note:          Optional[str] = None
    error_code:    Optional[str] = None
    error_message: Optional[str] = None


@router.patch("/admin/requests/{request_id}/status")
async def admin_update_request_status(
    request_id: str,
    body:       AdminUpdateStatusBody,
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

    row.status           = body.status.upper()
    row.handled_by_admin = admin.id
    row.updated_at       = datetime.utcnow()
    if body.error_code:    row.error_code    = body.error_code
    if body.error_message: row.error_message = body.error_message
    if row.status in ("DELIVERED", "FAILED", "CANCELLED"):
        row.completed_at = datetime.utcnow()

    db.commit()
    return {"success": True, "service_request_id": request_id, "new_status": row.status}


# ─── Payments ─────────────────────────────────────────────────────────────────

@router.get("/admin/payments")
async def admin_list_payments(
    department: Optional[str] = None,
    status:     Optional[str] = None,
    limit:      int = 50,
    offset:     int = 0,
    admin:      Admin = Depends(get_current_admin),
    db:         Session = Depends(get_db),
):
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
        "total": total,
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


# ─── Merchant Setup ───────────────────────────────────────────────────────────

class MerchantSetupBody(BaseModel):
    gateway:     str
    merchant_id: str
    channel_key: Optional[str] = None
    api_key:     Optional[str] = None
    notes:       Optional[str] = None


@router.post("/admin/merchant/setup")
async def admin_merchant_setup(
    body:  MerchantSetupBody,
    admin: Admin = Depends(get_current_admin),
    db:    Session = Depends(get_db),
):
    config = {
        "gateway":       body.gateway,
        "merchant_id":   body.merchant_id,
        "channel_key":   body.channel_key,
        "notes":         body.notes,
        "configured_at": datetime.utcnow().isoformat(),
    }
    if body.api_key:
        config["api_key_hint"] = f"****{body.api_key[-4:]}"

    admin.merchant_config = config
    db.commit()
    return {
        "success": True, "admin_id": admin.id,
        "department": admin.department, "gateway": body.gateway,
        "merchant_id": body.merchant_id,
    }


@router.get("/admin/merchant/config")
async def admin_get_merchant_config(admin: Admin = Depends(get_current_admin)):
    cfg = admin.merchant_config or {}
    return {
        "admin_id":      admin.id,
        "department":    admin.department,
        "role":          admin.role,
        "gateway":       cfg.get("gateway"),
        "merchant_id":   cfg.get("merchant_id"),
        "channel_key":   cfg.get("channel_key"),
        "configured_at": cfg.get("configured_at"),
    }


# ─── Kiosk Config ─────────────────────────────────────────────────────────────

class KioskConfigSetRequest(BaseModel):
    department:          str
    razorpay_key_id:     Optional[str]  = None
    razorpay_key_secret: Optional[str]  = None
    razorpay_mode:       Optional[str]  = "test"
    is_active:           Optional[bool] = None
    settings:            Optional[Dict[str, Any]] = None


class KioskConfigResponse(BaseModel):
    department:           str
    razorpay_key_id_hint: Optional[str]
    razorpay_mode:        Optional[str]
    is_active:            bool
    settings:             Dict[str, Any]
    configured_at:        Optional[str]


def _cfg_to_response(cfg: KioskConfig) -> KioskConfigResponse:
    return KioskConfigResponse(
        department           = cfg.department,
        razorpay_key_id_hint = cfg.razorpay_key_id_hint,
        razorpay_mode        = cfg.razorpay_mode,
        is_active            = cfg.is_active,
        settings             = cfg.settings or {},
        configured_at        = cfg.updated_at.isoformat() if cfg.updated_at else None,
    )


@router.post("/admin/kiosk-config", response_model=KioskConfigResponse)
async def admin_set_kiosk_config(
    body:  KioskConfigSetRequest,
    admin: Admin = Depends(require_super_admin),
    db:    Session = Depends(get_db),
):
    valid_departments = {"water", "electricity", "municipal", "global"}
    if body.department not in valid_departments:
        raise HTTPException(status_code=400, detail=f"department must be one of {sorted(valid_departments)}")

    cfg = db.query(KioskConfig).filter(KioskConfig.department == body.department).first()
    if not cfg:
        cfg = KioskConfig(department=body.department)
        db.add(cfg)

    if body.razorpay_key_id is not None:
        cfg.razorpay_key_id      = body.razorpay_key_id
        cfg.razorpay_key_id_hint = (
            f"****{body.razorpay_key_id[-4:]}" if len(body.razorpay_key_id) >= 4 else body.razorpay_key_id
        )
    if body.razorpay_key_secret is not None:
        cfg.razorpay_key_secret = body.razorpay_key_secret
    if body.razorpay_mode is not None:
        if body.razorpay_mode not in ("test", "live"):
            raise HTTPException(status_code=400, detail="razorpay_mode must be 'test' or 'live'")
        cfg.razorpay_mode = body.razorpay_mode
    if body.is_active is not None:
        cfg.is_active = body.is_active
    if body.settings:
        cfg.settings = {**(cfg.settings or {}), **body.settings}

    cfg.configured_by_admin = admin.id
    cfg.updated_at          = datetime.utcnow()
    db.commit()
    db.refresh(cfg)
    return _cfg_to_response(cfg)


@router.get("/admin/kiosk-config")
async def admin_get_kiosk_config(
    admin: Admin = Depends(require_super_admin),
    db:    Session = Depends(get_db),
):
    rows = db.query(KioskConfig).order_by(KioskConfig.department).all()
    return {"configs": [_cfg_to_response(r) for r in rows]}


@router.get("/admin/kiosk-config/{department}", response_model=KioskConfigResponse)
async def admin_get_kiosk_config_dept(
    department: str,
    admin:      Admin = Depends(require_super_admin),
    db:         Session = Depends(get_db),
):
    cfg = db.query(KioskConfig).filter(KioskConfig.department == department).first()
    if not cfg:
        raise HTTPException(status_code=404, detail=f"No config found for department '{department}'")
    return _cfg_to_response(cfg)
