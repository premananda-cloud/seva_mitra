"""
src/payment/mock_payment_engine.py
====================================
Mock payment engine for local development / kiosk demo mode.

Imported by main.py:
    from src.payment.mock_payment_engine import svc_complete, svc_initiate

Both functions mimic the interface of the real PortOne/Razorpay service
functions in payment_handler.py but never call any external gateway.

In mock mode payments are instantly "captured" — no real money moves.
The receipt returned is structurally identical to the real one so the
frontend / orchestrator code path is identical in both modes.
"""

import logging
import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Dict, Optional

from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

# ─── Reference number counter (in-process; use DB sequence in production) ─────

_ref_counter: Dict[str, int] = {}


def _make_reference(dept: str) -> str:
    prefix = {
        "electricity": "ELEC",
        "water":       "WAT",
        "municipal":   "MUNI",
        "gas":         "GAS",
    }.get(dept, "PAY")
    today = datetime.utcnow().strftime("%Y%m%d")
    key   = f"{prefix}{today}"
    _ref_counter[key] = _ref_counter.get(key, 0) + 1
    return f"PAY-{prefix}-{today}-{_ref_counter[key]:04d}"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


# ─── svc_initiate ─────────────────────────────────────────────────────────────

async def svc_initiate(
    *,
    internal_id:     str,
    user_id:         str,
    bill_id:         str,
    department:      str,
    amount:          float,
    method:          str          = "upi",
    gateway:         str          = "mock",
    currency:        str          = "INR",
    db:              Session,
    consumer_number: Optional[str] = None,
    billing_period:  Optional[str] = None,
) -> Dict[str, Any]:
    """
    Create a mock payment order.

    Returns a dict that mirrors the shape returned by real gateway helpers
    (portone_create_payment / razorpay_create_order) with an extra
    `isMock=True` flag so the caller knows to immediately call svc_complete.
    """
    from src.department.database.models import Payment  # local to avoid circular

    order_id = f"order_mock_{uuid.uuid4().hex[:12]}"

    # Persist a pending payment row
    payment = Payment(
        id=internal_id,
        user_id=user_id,
        bill_id=bill_id,
        department=department,
        amount=Decimal(str(amount)),
        currency=currency,
        gateway="mock",
        gateway_order_id=order_id,
        payment_method=method,
        consumer_number=consumer_number,
        billing_period=billing_period,
        status="pending",
    )
    db.add(payment)
    db.commit()

    logger.info(
        f"[MockPayment] order created  id={internal_id}  order={order_id}  "
        f"dept={department}  amount={amount}"
    )

    return {
        "isMock":    True,
        "gateway":   "mock",
        "orderId":   order_id,
        "paymentId": internal_id,
        "amount":    amount,
        "currency":  currency,
        "status":    "created",
        "expiresAt": None,
        "message":   "Mock payment order created",
        "timestamp": _now_iso(),
    }


# ─── svc_complete ─────────────────────────────────────────────────────────────

async def svc_complete(
    *,
    payment_id:         str,
    order_id:           str,
    gateway:            str          = "mock",
    gateway_payment_id: str,
    razorpay_signature: Optional[str] = None,
    db:                 Session,
) -> Dict[str, Any]:
    """
    Instantly "capture" the mock payment and mark it as paid.

    Returns a receipt dict with the same shape as CompletePaymentResponse
    from payment_handler.py, so callers treat mock and real identically.
    """
    from src.department.database.models import Payment  # local to avoid circular

    payment = db.query(Payment).filter(Payment.id == payment_id).first()

    if not payment:
        logger.error(f"[MockPayment] payment not found: {payment_id}")
        return {
            "success":   False,
            "status":    "FAILED",
            "error":     f"Payment {payment_id} not found",
            "timestamp": _now_iso(),
        }

    if payment.status == "paid":
        # Idempotent — return existing receipt
        logger.info(f"[MockPayment] already paid: {payment_id}")
    else:
        paid_at   = datetime.utcnow()
        reference = _make_reference(payment.department)

        payment.status             = "paid"
        payment.gateway_payment_id = gateway_payment_id
        payment.reference_no       = reference
        payment.paid_at            = paid_at
        db.commit()

        logger.info(
            f"[MockPayment] captured  id={payment_id}  ref={reference}  "
            f"dept={payment.department}  amount={payment.amount}"
        )

    return {
        "success": True,
        "status":  "SUCCESS",
        "receipt": {
            "referenceNo": payment.reference_no,
            "amount":      float(payment.amount),
            "dept":        payment.department,
            "method":      payment.payment_method or "mock",
            "paidAt":      payment.paid_at.isoformat() if payment.paid_at else _now_iso(),
            "consumerNo":  payment.consumer_number,
            "billId":      payment.bill_id,
            "gateway":     "mock",
        },
        "message":   "Mock payment captured successfully",
        "timestamp": _now_iso(),
    }
