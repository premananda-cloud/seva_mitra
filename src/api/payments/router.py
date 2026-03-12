"""
src/api/payments/router.py
==========================
Payment endpoints (initiate, complete, status, history, webhooks)
and shared service-request status lookup.
"""

import uuid
from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from sqlalchemy.orm import Session

from src.department.database.database import get_db
from src.department.database.models import ServiceRequest as ServiceRequestModel
from src.payment.payment_handler import (
    CompletePaymentRequest, CustomerRegisterRequest,
    InitiatePaymentRequest,
    handle_portone_webhook, handle_razorpay_webhook,
    svc_get_history, svc_get_status, svc_register_customer,
    verify_portone_webhook, verify_razorpay_webhook,
)
from src.payment.mock_payment_engine import svc_complete, svc_initiate
from src.api.shared.schemas import ServiceStatusResponse
from src.api.shared.utils import to_response

router = APIRouter(tags=["Payments"])


# ─── Payment endpoints ────────────────────────────────────────────────────────

@router.post("/api/v1/payments/customer/register")
async def register_customer(req: CustomerRegisterRequest, db: Session = Depends(get_db)):
    return await svc_register_customer(req, db)


@router.post("/api/v1/payments/initiate")
async def initiate_payment(req: InitiatePaymentRequest, db: Session = Depends(get_db)):
    internal_id = str(uuid.uuid4())
    return await svc_initiate(
        internal_id=internal_id, user_id=req.userId,
        bill_id=req.billId, department=req.dept,
        amount=req.amount, currency=req.currency,
        method=req.method, gateway=req.gateway, db=db,
        consumer_number=req.consumerNumber or "",
        billing_period=req.billingPeriod or "",
    )


@router.post("/api/v1/payments/complete")
async def complete_payment(req: CompletePaymentRequest, db: Session = Depends(get_db)):
    return await svc_complete(
        payment_id=req.paymentId, order_id=req.orderId,
        gateway=req.gateway, gateway_payment_id=req.gatewayPaymentId,
        razorpay_signature=req.razorpaySignature, db=db,
    )


@router.get("/api/v1/payments/status/{payment_id}")
async def payment_status(payment_id: str, db: Session = Depends(get_db)):
    return await svc_get_status(payment_id, db)


@router.get("/api/v1/payments/history/{user_id}")
async def payment_history(user_id: str, db: Session = Depends(get_db)):
    return await svc_get_history(user_id, db)


@router.post("/api/v1/payments/webhook", include_in_schema=False)
async def payment_webhook(
    request:              Request,
    db:                   Session = Depends(get_db),
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


# ─── Shared service-request lookup ───────────────────────────────────────────

@router.get("/api/v1/requests/{request_id}", response_model=ServiceStatusResponse, tags=["Shared"])
async def get_request_status(request_id: str, db: Session = Depends(get_db)):
    row = db.query(ServiceRequestModel).filter(
        ServiceRequestModel.service_request_id == request_id
    ).first()
    if not row:
        raise HTTPException(status_code=404, detail=f"Request {request_id} not found")
    return to_response(row)


@router.get("/api/v1/requests/user/{user_id}", tags=["Shared"])
async def get_user_requests(
    user_id:    str,
    department: Optional[str] = None,
    db:         Session = Depends(get_db),
):
    # service_requests.user_id is an Integer FK (NULL for guest/kiosk requests).
    # Department routers pass user_id as a string in the payload dict.
    # We match on payload->'user_id' so all kiosk requests are findable by their string id.
    from sqlalchemy import cast, String
    q = db.query(ServiceRequestModel).filter(
        ServiceRequestModel.payload["user_id"].as_string() == user_id
    )
    if department:
        q = q.filter(ServiceRequestModel.department == department)
    rows = q.order_by(ServiceRequestModel.created_at.desc()).all()
    return {"userId": user_id, "total": len(rows), "requests": [to_response(r) for r in rows]}
