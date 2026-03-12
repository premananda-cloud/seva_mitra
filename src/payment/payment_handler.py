"""
project/payment/payment_handler.py
====================================
Razorpay + PortOne backend integration.

Implements every endpoint in Section 2 of KOISK_Payment_Requirements.md.
Reads/writes to PostgreSQL via SQLAlchemy (the same DB session used by koisk_api.py).
All gateway secret keys are loaded from environment — never hardcoded.

ENV vars required (see .env.payment):
  RAZORPAY_KEY_ID
  RAZORPAY_KEY_SECRET
  PORTONE_API_SECRET
  PORTONE_STORE_ID
  PORTONE_CHANNEL_KEY
  PAYMENT_WEBHOOK_SECRET   ← same value set in both gateway dashboards
"""

import hashlib
import hmac
import logging
import os
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import httpx
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

# ─── Gateway config ───────────────────────────────────────────────────────────

RAZORPAY_KEY_ID     = os.getenv("RAZORPAY_KEY_ID",     "")
RAZORPAY_KEY_SECRET = os.getenv("RAZORPAY_KEY_SECRET", "")
PORTONE_API_SECRET  = os.getenv("PORTONE_API_SECRET",  "")
PORTONE_STORE_ID    = os.getenv("PORTONE_STORE_ID",    "")
PORTONE_CHANNEL_KEY = os.getenv("PORTONE_CHANNEL_KEY", "")
WEBHOOK_SECRET      = os.getenv("PAYMENT_WEBHOOK_SECRET", "")

PORTONE_BASE  = "https://api.portone.io"
RAZORPAY_BASE = "https://api.razorpay.com/v1"

# Auto mock-mode when no gateway keys are configured (safe for local dev)
MOCK_MODE = not RAZORPAY_KEY_SECRET and not PORTONE_API_SECRET

# ─── Reference number sequence (in-process counter; use DB sequence in prod) ──

_ref_counter: Dict[str, int] = {}

def _make_reference(dept: str) -> str:
    prefix = {"electricity": "ELEC", "gas": "GAS", "water": "WAT"}.get(dept, "PAY")
    today  = datetime.utcnow().strftime("%Y%m%d")
    key    = f"{prefix}{today}"
    _ref_counter[key] = _ref_counter.get(key, 0) + 1
    return f"PAY-{prefix}-{today}-{_ref_counter[key]:04d}"

def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


# ─── Pydantic request / response models ──────────────────────────────────────
# Field names match the contract in Section 4 of the requirements exactly.

class CustomerRegisterRequest(BaseModel):
    userId:  str
    name:    str
    contact: str                          # must be E.164: +91XXXXXXXXXX
    email:   str
    notes:   Optional[Dict[str, str]] = None


class CustomerRegisterResponse(BaseModel):
    success:            bool = True
    portoneCustomerId:  Optional[str] = None
    razorpayCustomerId: Optional[str] = None
    message:            str = "Customer registered successfully"
    timestamp:          str = Field(default_factory=_now)


class InitiatePaymentRequest(BaseModel):
    userId:         str
    billId:         str
    dept:           str                       # electricity | gas | water
    amount:         float                     # rupees (not paise)
    currency:       str = "INR"
    gateway:        str = "mock"              # portone | razorpay | mock
    method:         str = "upi"              # upi | card | netbanking
    customerId:     Optional[str] = None      # portone_customer_id
    consumerNumber: Optional[str] = None      # meter / consumer number
    billingPeriod:  Optional[str] = None      # YYYY-MM


class InitiatePaymentResponse(BaseModel):
    success:     bool = True
    orderId:     str
    gateway:     str
    gatewayData: Dict[str, Any] = {}
    expiresAt:   Optional[str]  = None
    message:     str = "Payment order created"
    timestamp:   str = Field(default_factory=_now)


class CompletePaymentRequest(BaseModel):
    paymentId:         str               # our internal UUID (payments.id)
    orderId:           str               # gateway order id
    gateway:           str
    gatewayPaymentId:  str
    razorpaySignature: Optional[str] = None   # required for Razorpay


class ReceiptData(BaseModel):
    referenceNo: str
    amount:      float
    dept:        str
    method:      str
    paidAt:      str
    consumerNo:  Optional[str] = None


class CompletePaymentResponse(BaseModel):
    success:   bool = True
    status:    str  = "SUCCESS"
    receipt:   ReceiptData
    message:   str  = "Payment verified successfully"
    timestamp: str  = Field(default_factory=_now)


class PaymentStatusResponse(BaseModel):
    success:       bool = True
    paymentId:     str
    status:        str
    amount:        Optional[float] = None
    paidAt:        Optional[str]   = None
    referenceNo:   Optional[str]   = None
    timestamp:     str = Field(default_factory=_now)


class ErrorResponse(BaseModel):
    success:    bool = False
    error_code: str
    message:    str
    timestamp:  str = Field(default_factory=_now)


# ─── PortOne API helpers ──────────────────────────────────────────────────────

def _po_headers() -> Dict[str, str]:
    return {
        "Authorization": f"PortOne {PORTONE_API_SECRET}",
        "Content-Type":  "application/json",
    }


async def portone_register_customer(name: str, contact: str, email: str,
                                    notes: Optional[Dict] = None) -> str:
    """POST /customers → returns portone customer_id."""
    if MOCK_MODE:
        cid = f"cust_portone_{uuid.uuid4().hex[:10]}"
        logger.info(f"[PortOne MOCK] customer created: {cid}")
        return cid

    payload: Dict[str, Any] = {
        "customer_name":  name,
        "customer_phone": contact,
        "customer_email": email,
    }
    if notes:
        payload["metadata"] = notes

    async with httpx.AsyncClient(timeout=15) as c:
        r = await c.post(f"{PORTONE_BASE}/customers", json=payload, headers=_po_headers())
        r.raise_for_status()
        data = r.json()
        logger.info(f"[PortOne] customer registered: {data['customer_id']}")
        return data["customer_id"]


async def portone_create_payment(internal_id: str, amount: float, currency: str,
                                  customer_id: str, dept: str) -> Dict[str, Any]:
    """POST /payments → returns payment_id used as orderId."""
    if MOCK_MODE:
        oid = f"portone_order_{uuid.uuid4().hex[:10]}"
        logger.info(f"[PortOne MOCK] order: {oid}")
        return {"payment_id": oid, "status": "INITIATED"}

    payload = {
        "payment_id":     internal_id,           # we set our own ID
        "order_amount":   round(amount * 100),    # paise
        "order_currency": currency,
        "channel_key":    PORTONE_CHANNEL_KEY,
        "customer_id":    customer_id,
        "order_name":     f"KOISK {dept.capitalize()} Bill",
    }
    async with httpx.AsyncClient(timeout=15) as c:
        r = await c.post(f"{PORTONE_BASE}/payments", json=payload, headers=_po_headers())
        r.raise_for_status()
        return r.json()


async def portone_get_payment(portone_payment_id: str) -> Dict[str, Any]:
    """GET /payments/:id — server-to-server status check."""
    if MOCK_MODE:
        return {"status": "paid"}

    async with httpx.AsyncClient(timeout=15) as c:
        r = await c.get(f"{PORTONE_BASE}/payments/{portone_payment_id}", headers=_po_headers())
        r.raise_for_status()
        return r.json()


# ─── Razorpay API helpers ─────────────────────────────────────────────────────

def _rz_auth():
    return (RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET)


async def create_razorpay_customer_with_key(
    name:       str,
    contact:    str,
    email:      str,
    key_id:     str,
    key_secret: str,
    notes:      Optional[Dict[str, str]] = None,
) -> str:
    """
    Create a Razorpay customer using a specific department's API key pair.

    Called during kiosk OTP verification (first-time users only).
    Returns the Razorpay customer ID string (e.g. "cust_XXXXXXXXXXXXXX").

    In mock mode (no real keys supplied) returns a deterministic fake ID
    so the rest of the flow works without a live Razorpay account.

    Raises ValueError on API errors so the caller can decide whether to
    fail hard or continue without a customer ID.
    """
    if not key_id or not key_secret:
        # Mock / dev mode — generate a stable-looking fake customer ID
        fake_id = "cust_mock_" + uuid.uuid5(uuid.NAMESPACE_DNS, contact).hex[:14]
        logger.info(f"[Razorpay] mock mode — returning fake customer id {fake_id}")
        return fake_id

    payload: Dict[str, Any] = {
        "name":    name,
        "contact": contact,
        "email":   email or "",
        "notes":   notes or {"source": "koisk_kiosk"},
    }

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.post(
                f"{RAZORPAY_BASE}/customers",
                json=payload,
                auth=(key_id, key_secret),
            )
            response.raise_for_status()
            data        = response.json()
            customer_id = data["id"]
            logger.info(f"[Razorpay] customer created: {customer_id} for contact={contact}")
            return customer_id

    except httpx.HTTPStatusError as exc:
        body = exc.response.text
        logger.error(f"[Razorpay] customer creation HTTP error {exc.response.status_code}: {body}")
        raise ValueError(f"Razorpay API error {exc.response.status_code}: {body}") from exc

    except httpx.RequestError as exc:
        logger.error(f"[Razorpay] network error during customer creation: {exc}")
        raise ValueError(f"Razorpay network error: {exc}") from exc


async def razorpay_create_order(amount: float, currency: str,
                                 receipt: str, notes: Optional[Dict] = None) -> Dict[str, Any]:
    """POST /orders → returns order object."""
    if MOCK_MODE:
        oid = f"order_{uuid.uuid4().hex[:10]}"
        logger.info(f"[Razorpay MOCK] order: {oid}")
        return {"id": oid, "status": "created"}

    payload: Dict[str, Any] = {
        "amount":   round(amount * 100),          # paise
        "currency": currency,
        "receipt":  receipt,
    }
    if notes:
        payload["notes"] = notes

    async with httpx.AsyncClient(timeout=15) as c:
        r = await c.post(f"{RAZORPAY_BASE}/orders", json=payload, auth=_rz_auth())
        r.raise_for_status()
        return r.json()


async def razorpay_get_payment(payment_id: str) -> Dict[str, Any]:
    """GET /payments/:id — server-to-server status check."""
    if MOCK_MODE:
        return {"status": "captured"}

    async with httpx.AsyncClient(timeout=15) as c:
        r = await c.get(f"{RAZORPAY_BASE}/payments/{payment_id}", auth=_rz_auth())
        r.raise_for_status()
        return r.json()


def razorpay_verify_signature(order_id: str, payment_id: str, signature: str) -> bool:
    """HMAC-SHA256 verification. Must pass before marking payment as paid."""
    if MOCK_MODE:
        return True
    if not RAZORPAY_KEY_SECRET:
        logger.error("[Razorpay] KEY_SECRET not set — cannot verify signature")
        return False
    expected = hmac.new(
        RAZORPAY_KEY_SECRET.encode(),
        f"{order_id}|{payment_id}".encode(),
        hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(expected, signature)


# ─── Webhook signature verification ──────────────────────────────────────────

def verify_razorpay_webhook(body: bytes, signature: str) -> bool:
    if not WEBHOOK_SECRET:
        logger.warning("[webhook] PAYMENT_WEBHOOK_SECRET not set — skipping verify")
        return True
    expected = hmac.new(WEBHOOK_SECRET.encode(), body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature)


def verify_portone_webhook(body: bytes, signature: str) -> bool:
    if not PORTONE_API_SECRET:
        return True
    expected = hmac.new(PORTONE_API_SECRET.encode(), body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature)


# ─── Service functions — called by koisk_api.py route handlers ────────────────

async def svc_register_customer(req: CustomerRegisterRequest,
                                 db: Session) -> CustomerRegisterResponse:
    """
    Idempotent. Checks payment_profiles table first.
    Creates PortOne customer, stores ID in payment_profiles.
    Also attempts Razorpay customer (non-blocking if it fails).
    """
    from src.database.models import PaymentProfile, User  # local import avoids circular dep

    # 1. Already registered? Return existing IDs.
    existing = db.query(PaymentProfile).filter(PaymentProfile.user_id == req.userId).first()
    if existing:
        logger.info(f"[register_customer] existing profile for {req.userId}")
        return CustomerRegisterResponse(
            portoneCustomerId=existing.portone_customer_id,
            razorpayCustomerId=existing.razorpay_customer_id,
            message="Customer already registered",
        )

    notes = req.notes or {"koisk_user_id": req.userId}

    # 2. Register on PortOne
    portone_id  = None
    razorpay_id = None

    try:
        portone_id = await portone_register_customer(req.name, req.contact, req.email, notes)
    except Exception as e:
        logger.error(f"[PortOne] registration failed for {req.userId}: {e}")

    # 3. Razorpay customer (optional — only needed for Razorpay payments)
    try:
        if not MOCK_MODE:
            async with httpx.AsyncClient(timeout=15) as c:
                r = await c.post(
                    f"{RAZORPAY_BASE}/customers",
                    json={"name": req.name, "contact": req.contact, "email": req.email, "notes": notes},
                    auth=_rz_auth(),
                )
                r.raise_for_status()
                razorpay_id = r.json()["id"]
                logger.info(f"[Razorpay] customer created: {razorpay_id}")
        else:
            razorpay_id = None   # mock: no Razorpay customer needed
    except Exception as e:
        logger.error(f"[Razorpay] registration failed for {req.userId}: {e}")

    # 4. Persist to payment_profiles
    profile = PaymentProfile(
        id=req.userId,                          # same as user.id
        user_id=req.userId,
        portone_customer_id=portone_id,
        razorpay_customer_id=razorpay_id,
        name=req.name,
        contact=req.contact,
        email=req.email,
        preferred_gateway="portone",
    )
    db.add(profile)
    db.commit()

    return CustomerRegisterResponse(
        portoneCustomerId=portone_id,
        razorpayCustomerId=razorpay_id,
    )


async def svc_initiate_payment(req: InitiatePaymentRequest,
                                db: Session) -> InitiatePaymentResponse:
    """
    Creates a gateway order. Inserts payments row with status='pending'.
    Returns orderId for the frontend SDK modal.
    """
    from src.database.models import Payment, PaymentProfile  # local import

    internal_id = str(uuid.uuid4())
    gateway_order_id: str
    gateway_data: Dict[str, Any] = {}

    if req.gateway == "portone":
        # Resolve portone customer ID
        customer_id = req.customerId
        if not customer_id:
            profile = db.query(PaymentProfile).filter(
                PaymentProfile.user_id == req.userId
            ).first()
            customer_id = profile.portone_customer_id if profile else f"auto_{req.userId[:8]}"

        result = await portone_create_payment(
            internal_id=internal_id,
            amount=req.amount,
            currency=req.currency,
            customer_id=customer_id,
            dept=req.dept,
        )
        gateway_order_id = result.get("payment_id", result.get("id", internal_id))
        gateway_data     = result

    elif req.gateway == "razorpay":
        result = await razorpay_create_order(
            amount=req.amount,
            currency=req.currency,
            receipt=f"koisk_{req.dept}_{internal_id[:8]}",
            notes={"koisk_payment_id": internal_id, "dept": req.dept, "user_id": req.userId},
        )
        gateway_order_id = result["id"]
        gateway_data     = result

    else:
        raise ValueError(f"Unknown gateway: {req.gateway!r}. Use 'portone' or 'razorpay'.")

    # Insert pending payment row
    payment = Payment(
        id=internal_id,
        user_id=req.userId,
        bill_id=req.billId,
        department=req.dept,
        amount=req.amount,
        currency=req.currency,
        gateway=req.gateway,
        gateway_order_id=gateway_order_id,
        payment_method=req.method,
        status="pending",
    )
    db.add(payment)
    db.commit()

    logger.info(f"[initiate_payment] {req.gateway} order={gateway_order_id} internal={internal_id}")

    expires_at = None
    if "expires_at" in gateway_data:
        expires_at = gateway_data["expires_at"]

    return InitiatePaymentResponse(
        orderId=gateway_order_id,
        gateway=req.gateway,
        gatewayData=gateway_data,
        expiresAt=expires_at,
    )


async def svc_complete_payment(req: CompletePaymentRequest,
                                db: Session) -> CompletePaymentResponse:
    """
    Server-side payment verification before marking as paid.
    Razorpay: HMAC signature check.
    PortOne:  server-to-server status check.
    Updates payments row, returns receipt.
    """
    from src.database.models import Payment  # local import

    payment = db.query(Payment).filter(Payment.id == req.paymentId).first()
    if not payment:
        raise ValueError(f"Payment {req.paymentId} not found")

    if payment.status == "paid":
        # Idempotent — already completed, return existing receipt
        return CompletePaymentResponse(
            receipt=ReceiptData(
                referenceNo=payment.reference_no or _make_reference(payment.department),
                amount=payment.amount,
                dept=payment.department,
                method=payment.payment_method,
                paidAt=payment.paid_at.isoformat() if payment.paid_at else _now(),
                consumerNo=payment.consumer_number,
            ),
            message="Payment already completed",
        )

    # ── Razorpay: verify HMAC signature ──────────────────────────────────────
    if req.gateway == "razorpay":
        if not req.razorpaySignature:
            raise ValueError("razorpaySignature is required for Razorpay payments")

        if not razorpay_verify_signature(req.orderId, req.gatewayPaymentId, req.razorpaySignature):
            payment.status        = "failed"
            payment.error_message = "Signature verification failed"
            db.commit()
            raise ValueError("Razorpay signature verification failed — payment rejected")

        # Double-check with Razorpay server
        try:
            rz = await razorpay_get_payment(req.gatewayPaymentId)
            if rz.get("status") != "captured":
                raise ValueError(f"Razorpay payment status is '{rz.get('status')}', expected 'captured'")
        except httpx.HTTPError as e:
            logger.warning(f"[Razorpay] Could not fetch payment for double-check: {e} — trusting signature")

    # ── PortOne: server-to-server status check ────────────────────────────────
    elif req.gateway == "portone":
        try:
            po = await portone_get_payment(req.gatewayPaymentId)
            status = po.get("status", "").lower()
            if status not in ("paid", "virtual_account_issued", "partial_paid"):
                raise ValueError(f"PortOne payment status is '{status}', expected 'paid'")
        except httpx.HTTPError as e:
            logger.warning(f"[PortOne] Status check failed: {e} — proceeding with caution")

    # ── Mark SUCCESS ──────────────────────────────────────────────────────────
    paid_at   = datetime.utcnow()
    reference = _make_reference(payment.department)

    payment.status             = "paid"
    payment.gateway_payment_id = req.gatewayPaymentId
    payment.reference_no       = reference
    payment.paid_at            = paid_at
    db.commit()

    logger.info(f"[complete_payment] {req.paymentId} → paid  ref={reference}")

    return CompletePaymentResponse(
        receipt=ReceiptData(
            referenceNo=reference,
            amount=payment.amount,
            dept=payment.department,
            method=payment.payment_method,
            paidAt=paid_at.isoformat(),
            consumerNo=payment.consumer_number,
        ),
    )


async def svc_get_status(payment_id: str, db: Session) -> PaymentStatusResponse:
    from src.database.models import Payment
    payment = db.query(Payment).filter(Payment.id == payment_id).first()
    if not payment:
        raise ValueError(f"Payment {payment_id} not found")
    return PaymentStatusResponse(
        paymentId=payment_id,
        status=payment.status,
        amount=payment.amount,
        paidAt=payment.paid_at.isoformat() if payment.paid_at else None,
        referenceNo=payment.reference_no,
    )


async def svc_get_history(user_id: str, db: Session) -> List[Dict]:
    from src.database.models import Payment
    rows = (
        db.query(Payment)
        .filter(Payment.user_id == user_id)
        .order_by(Payment.created_at.desc())
        .all()
    )
    return [
        {
            "id":                row.id,
            "userId":            row.user_id,
            "billId":            row.bill_id,
            "dept":              row.department,
            "amount":            row.amount,
            "currency":          row.currency,
            "gateway":           row.gateway,
            "method":            row.payment_method,
            "status":            row.status,
            "referenceNo":       row.reference_no,
            "gatewayPaymentId":  row.gateway_payment_id,
            "consumerNo":        row.consumer_number,
            "paidAt":            row.paid_at.isoformat() if row.paid_at else None,
            "createdAt":         row.created_at.isoformat(),
        }
        for row in rows
    ]


# ─── Webhook handlers ─────────────────────────────────────────────────────────

async def handle_razorpay_webhook(event: str, payload: Dict, db: Session) -> Dict:
    """
    Handles cases where /complete was never called (browser closed mid-payment).
    Razorpay sends payment.captured / payment.failed events.
    """
    from src.database.models import Payment

    entity    = payload.get("payload", {}).get("payment", {}).get("entity", {})
    rz_order  = entity.get("order_id")
    rz_pay_id = entity.get("id")

    if not rz_order:
        return {"received": True, "note": "no order_id in payload"}

    payment = db.query(Payment).filter(Payment.gateway_order_id == rz_order).first()
    if not payment:
        logger.warning(f"[webhook/razorpay] no payment found for order {rz_order}")
        return {"received": True}

    if event == "payment.captured" and payment.status != "paid":
        payment.status             = "paid"
        payment.gateway_payment_id = rz_pay_id
        payment.reference_no       = _make_reference(payment.department)
        payment.paid_at            = datetime.utcnow()
        db.commit()
        logger.info(f"[webhook/razorpay] payment.captured → {payment.id} marked paid")

    elif event == "payment.failed" and payment.status == "pending":
        payment.status        = "failed"
        payment.error_message = entity.get("error_description", "Payment failed")
        db.commit()
        logger.info(f"[webhook/razorpay] payment.failed → {payment.id} marked failed")

    return {"received": True}


async def handle_portone_webhook(event: str, payload: Dict, db: Session) -> Dict:
    """
    PortOne sends Transaction.Paid / Transaction.Failed events.
    """
    from src.database.models import Payment

    po_id = (payload.get("payment") or {}).get("paymentId") or payload.get("paymentId")
    if not po_id:
        return {"received": True, "note": "no paymentId in payload"}

    # PortOne payment_id == our internal payment id (we set it on create)
    payment = db.query(Payment).filter(
        (Payment.id == po_id) | (Payment.gateway_order_id == po_id)
    ).first()

    if not payment:
        logger.warning(f"[webhook/portone] no payment found for id {po_id}")
        return {"received": True}

    if event in ("Transaction.Paid", "Transaction.PartiallyPaid") and payment.status != "paid":
        payment.status             = "paid"
        payment.gateway_payment_id = po_id
        payment.reference_no       = _make_reference(payment.department)
        payment.paid_at            = datetime.utcnow()
        db.commit()
        logger.info(f"[webhook/portone] {event} → {payment.id} marked paid")

    elif event == "Transaction.Failed" and payment.status == "pending":
        payment.status        = "failed"
        payment.error_message = payload.get("failure", {}).get("message", "Payment failed")
        db.commit()
        logger.info(f"[webhook/portone] Transaction.Failed → {payment.id} marked failed")

    return {"received": True}
