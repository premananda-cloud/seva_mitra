"""
src/api/gas/router.py
=====================
Gas department endpoints.

Endpoints
---------
GET  /api/v1/gas/bills/{user_id}        — fetch outstanding gas bills
POST /api/v1/gas/pay-bill               — pay a gas bill (mock payment engine)
POST /api/v1/gas/new-connection         — apply for a new gas connection
POST /api/v1/gas/safety-complaint       — report a gas leak / safety hazard
"""

import uuid
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from src.department.database.database import get_db
from src.department.database.models import GasConsumer, User
from src.payment.mock_payment_engine import svc_complete, svc_initiate
from src.api.shared.schemas import SuccessResponse
from src.api.shared.utils import save_request

router = APIRouter(prefix="/api/v1/gas", tags=["Gas"])


# ─── Schemas ──────────────────────────────────────────────────────────────────

class GasPayBillRequest(BaseModel):
    user_id:         str
    consumer_number: str
    billing_period:  str
    amount:          float
    payment_method:  str
    gateway:         str = "mock"


class GasConnectionRequest(BaseModel):
    applicant_name:  str
    applicant_id:    str
    address:         str
    connection_type: str                # domestic | commercial
    identity_proof:  str                # aadhaar | pan | voter
    id_number:       str
    phone:           str


class GasSafetyComplaintRequest(BaseModel):
    consumer_id:  str
    consumer_no:  str
    issue_type:   str                   # leak | smell | pressure | meter | other
    location:     str
    description:  str
    phone:        str


# ─── Routes ───────────────────────────────────────────────────────────────────

@router.get("/bills/{user_id}")
async def gas_get_bills(user_id: str, db: Session = Depends(get_db)):
    """Return outstanding gas bills for the given user."""
    consumers = db.query(GasConsumer).join(User).filter(User.username == user_id).all()
    bills = []
    for c in consumers:
        if c.outstanding_amount > 0:
            bills.append({
                "id":         f"BILL-GAS-{c.consumer_number}",
                "dept":       "gas",
                "consumerNo": c.consumer_number,
                "amountDue":  c.outstanding_amount,
                "billMonth":  datetime.utcnow().strftime("%Y-%m"),
                "dueDate":    (datetime.utcnow() + timedelta(days=10)).strftime("%Y-%m-%d"),
                "status":     "UNPAID",
            })
    return {"userId": user_id, "bills": bills}


@router.post("/pay-bill", response_model=SuccessResponse)
async def gas_pay_bill(req: GasPayBillRequest, db: Session = Depends(get_db)):
    """Process a gas bill payment via the mock payment engine."""
    internal_id = str(uuid.uuid4())

    pay_result = await svc_initiate(
        internal_id=internal_id, user_id=req.user_id,
        bill_id=f"BILL-GAS-{req.consumer_number}-{req.billing_period}",
        department="gas", amount=req.amount,
        method=req.payment_method, gateway=req.gateway, db=db,
        consumer_number=req.consumer_number, billing_period=req.billing_period,
    )

    complete_result = {}
    if pay_result.get("isMock"):
        complete_result = await svc_complete(
            payment_id=internal_id, order_id=pay_result["orderId"],
            gateway="mock", gateway_payment_id=f"pay_mock_{uuid.uuid4().hex[:10]}", db=db,
        )

    row = save_request(
        db=db, req_id=str(uuid.uuid4()),
        dept="gas", stype="GAS_PAY_BILL",
        status_str="DELIVERED" if pay_result.get("isMock") else "SUBMITTED",
        payload=req.dict(), payment_id=internal_id,
    )
    return SuccessResponse(
        success=True, service_request_id=row.service_request_id,
        department="gas", status=row.status,
        message="Gas bill payment processed",
        data=complete_result.get("receipt") or pay_result,
    )


@router.post("/new-connection", response_model=SuccessResponse)
async def gas_new_connection(req: GasConnectionRequest, db: Session = Depends(get_db)):
    """Submit a new gas connection application."""
    row = save_request(
        db=db, req_id=str(uuid.uuid4()),
        dept="gas", stype="GAS_CONNECTION_REQUEST",
        status_str="SUBMITTED", payload=req.dict(),
    )
    return SuccessResponse(
        success=True, service_request_id=row.service_request_id,
        department="gas", status=row.status,
        message="Gas connection request submitted. Expect installation within 15 working days.",
    )


@router.post("/safety-complaint", response_model=SuccessResponse)
async def gas_safety_complaint(req: GasSafetyComplaintRequest, db: Session = Depends(get_db)):
    """Log a gas safety complaint. Gas leaks are auto-escalated to IN_PROGRESS."""
    is_critical = req.issue_type == "leak"
    status_str  = "IN_PROGRESS" if is_critical else "SUBMITTED"
    message     = (
        "🚨 CRITICAL: Gas leak reported — emergency team dispatched immediately. "
        "Please evacuate and call 1906."
        if is_critical else
        "Safety complaint submitted. Our team will inspect within 24 hours."
    )

    row = save_request(
        db=db, req_id=str(uuid.uuid4()),
        dept="gas", stype="GAS_SAFETY_COMPLAINT",
        status_str=status_str, payload=req.dict(),
    )
    return SuccessResponse(
        success=True, service_request_id=row.service_request_id,
        department="gas", status=row.status,
        message=message,
    )
