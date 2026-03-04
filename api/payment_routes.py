"""
project/payment/payment_routes.py
===================================
FastAPI router for all payment endpoints (Section 2 of requirements).
Register this router in koisk_api.py with one line:

    from payment.payment_routes import payment_router
    app.include_router(payment_router)

All routes return the standard envelope:
    { "success": bool, "data": ..., "message": str, "timestamp": ISO }
"""

import logging
from typing import Dict

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from sqlalchemy.orm import Session

from database.database import get_db
from payment.payment_handler import (
    CustomerRegisterRequest,
    InitiatePaymentRequest,
    CompletePaymentRequest,
    ErrorResponse,
    svc_register_customer,
    svc_initiate_payment,
    svc_complete_payment,
    svc_get_status,
    svc_get_history,
    handle_razorpay_webhook,
    handle_portone_webhook,
    verify_razorpay_webhook,
    verify_portone_webhook,
)

logger = logging.getLogger(__name__)

payment_router = APIRouter(prefix="/api/v1/payments", tags=["Payments"])


# ── Helper: standard error response ──────────────────────────────────────────

def _err(code: str, msg: str, http_status: int = 400):
    raise HTTPException(
        status_code=http_status,
        detail={"success": False, "error_code": code, "message": msg},
    )


# ─────────────────────────────────────────────────────────────────────────────
# POST /api/v1/payments/customer/register
# Section 2.2
# ─────────────────────────────────────────────────────────────────────────────

@payment_router.post("/customer/register", summary="Register user with payment gateways")
async def register_customer(req: CustomerRegisterRequest, db: Session = Depends(get_db)):
    """
    Idempotent — if the user is already registered, returns existing IDs.
    Creates PortOne customer (and Razorpay if configured).
    Stores customer IDs in payment_profiles table.
    Called automatically on first payment attempt — user never sees this step.
    """
    try:
        result = await svc_register_customer(req, db)
        return result
    except Exception as e:
        logger.error(f"[/customer/register] {e}")
        _err("REGISTRATION_FAILED", str(e))


# ─────────────────────────────────────────────────────────────────────────────
# POST /api/v1/payments/initiate
# Section 2.3
# ─────────────────────────────────────────────────────────────────────────────

@payment_router.post("/initiate", summary="Create a gateway payment order")
async def initiate_payment(req: InitiatePaymentRequest, db: Session = Depends(get_db)):
    """
    Creates a PortOne or Razorpay order.
    Returns orderId — frontend opens the gateway SDK modal using this ID.
    Inserts a 'pending' row into the payments table.
    """
    try:
        return await svc_initiate_payment(req, db)
    except ValueError as e:
        _err("INVALID_REQUEST", str(e))
    except Exception as e:
        logger.error(f"[/initiate] {e}")
        _err("GATEWAY_ERROR", "Could not create payment order. Please retry.", 502)


# ─────────────────────────────────────────────────────────────────────────────
# POST /api/v1/payments/complete
# Section 2.4
# ─────────────────────────────────────────────────────────────────────────────

@payment_router.post("/complete", summary="Verify and finalise payment")
async def complete_payment(req: CompletePaymentRequest, db: Session = Depends(get_db)):
    """
    Called after the gateway SDK fires onSuccess in the browser.
    Server verifies the payment before marking it as paid:
      - Razorpay: HMAC signature check
      - PortOne:  server-to-server status poll
    Returns a receipt on success.
    """
    try:
        return await svc_complete_payment(req, db)
    except ValueError as e:
        msg = str(e)
        code = "SIGNATURE_FAILED" if "signature" in msg.lower() else "PAYMENT_FAILED"
        _err(code, msg)
    except Exception as e:
        logger.error(f"[/complete] {e}")
        _err("GATEWAY_ERROR", "Could not verify payment. Contact support.", 502)


# ─────────────────────────────────────────────────────────────────────────────
# GET /api/v1/payments/status/{paymentId}
# Section 2.1
# ─────────────────────────────────────────────────────────────────────────────

@payment_router.get("/status/{payment_id}", summary="Poll payment status")
async def get_payment_status(payment_id: str, db: Session = Depends(get_db)):
    """Used by the receipt page to confirm final payment status."""
    try:
        return await svc_get_status(payment_id, db)
    except ValueError as e:
        _err("NOT_FOUND", str(e), 404)


# ─────────────────────────────────────────────────────────────────────────────
# GET /api/v1/payments/history/{userId}
# Section 2.1
# ─────────────────────────────────────────────────────────────────────────────

@payment_router.get("/history/{user_id}", summary="Payment history for a user")
async def get_payment_history(user_id: str, db: Session = Depends(get_db)):
    """Returns all payments newest-first. Used by the dashboard."""
    return await svc_get_history(user_id, db)


# ─────────────────────────────────────────────────────────────────────────────
# POST /api/v1/payments/webhook
# Section 2.5 — unified webhook endpoint
# ─────────────────────────────────────────────────────────────────────────────

@payment_router.post("/webhook", include_in_schema=False)
async def payment_webhook(
    request: Request,
    db: Session = Depends(get_db),
    x_razorpay_signature: str = Header(default=""),
    x_portone_signature:  str = Header(default=""),
):
    """
    Single webhook URL for both gateways.
    Configure in both dashboards:
      Razorpay  → Dashboard → Webhooks → URL: /api/v1/payments/webhook
      PortOne   → Console  → Webhooks → URL: /api/v1/payments/webhook

    Gateway is detected from which signature header is present.
    Always returns HTTP 200 with { "received": true } — prevents retries.
    """
    body = await request.body()

    # ── Detect gateway from signature header ────────────────────────────────
    if x_razorpay_signature:
        if not verify_razorpay_webhook(body, x_razorpay_signature):
            logger.warning("[webhook] Razorpay signature invalid — rejected")
            raise HTTPException(status_code=400, detail="Invalid webhook signature")
        try:
            payload    = await request.json()
            event_type = payload.get("event", "")
            result     = await handle_razorpay_webhook(event_type, payload, db)
            logger.info(f"[webhook/razorpay] processed event: {event_type}")
            return result
        except Exception as e:
            logger.error(f"[webhook/razorpay] handler error: {e}")
            return {"received": True}   # must return 200 or Razorpay retries

    elif x_portone_signature:
        if not verify_portone_webhook(body, x_portone_signature):
            logger.warning("[webhook] PortOne signature invalid — rejected")
            raise HTTPException(status_code=400, detail="Invalid webhook signature")
        try:
            payload    = await request.json()
            event_type = payload.get("type", payload.get("status", ""))
            result     = await handle_portone_webhook(event_type, payload, db)
            logger.info(f"[webhook/portone] processed event: {event_type}")
            return result
        except Exception as e:
            logger.error(f"[webhook/portone] handler error: {e}")
            return {"received": True}

    else:
        # No recognised signature header — log and accept
        # (some gateways send test pings without signatures)
        logger.warning("[webhook] No signature header found — ignoring payload")
        return {"received": True}
