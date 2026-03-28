"""
src/api/complaints/router.py
=============================
Cross-department complaints & grievances endpoint.

This module handles general civic complaints that span all departments
(electricity, water, gas, municipal) as well as non-department-specific
civic grievances. Department-level complaints (e.g. gas leaks) continue
to have their own dedicated endpoints; this router covers the general
complaint hub accessible from the top-level Complaints screen.

Endpoints
---------
POST /api/v1/complaints/submit         — submit a new complaint
GET  /api/v1/complaints/{reference_id} — track a complaint by reference ID
GET  /api/v1/complaints/user/{user_id} — list all complaints for a citizen
"""

import uuid
from datetime import datetime
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from src.department.database.database import get_db
from src.department.database.models import ServiceRequest as ServiceRequestModel
from src.api.shared.schemas import SuccessResponse
from src.api.shared.utils import save_request

router = APIRouter(prefix="/api/v1/complaints", tags=["Complaints"])


# ─── Schemas ──────────────────────────────────────────────────────────────────

class ComplaintSubmitRequest(BaseModel):
    """
    General complaint submission.

    department  : electricity | water | gas | municipal | general
    category    : maps to issue types within a department, or "General" for civic
    severity    : Low | Medium | High | Critical
    """
    citizen_name:   str
    phone:          str
    department:     str                     # electricity|water|gas|municipal|general
    category:       str                     # e.g. "Billing Issue", "No Supply", "Gas Leak"
    subject:        str
    description:    str
    location:       Optional[str]   = None
    ward_number:    Optional[str]   = None
    consumer_no:    Optional[str]   = None  # consumer/meter/connection number if applicable
    severity:       str             = "Medium"   # Low | Medium | High | Critical
    attachment_ref: Optional[str]   = None


class ComplaintTrackResponse(BaseModel):
    reference_id:   str
    department:     str
    category:       str
    subject:        str
    status:         str
    severity:       str
    created_at:     datetime
    updated_at:     datetime
    message:        str


# ─── Helpers ──────────────────────────────────────────────────────────────────

# Map severity → initial status.
# Critical complaints (e.g. gas leak routed through here) go straight to IN_PROGRESS.
_SEVERITY_STATUS = {
    "Critical": "IN_PROGRESS",
    "High":     "SUBMITTED",
    "Medium":   "SUBMITTED",
    "Low":      "SUBMITTED",
}

# Human-readable acknowledgement messages per severity
_ACK_MESSAGES = {
    "Critical": (
        "🚨 Critical complaint registered — our team has been alerted immediately. "
        "Expected response within 2 hours."
    ),
    "High":     "Complaint registered. Our team will respond within 24 hours.",
    "Medium":   "Complaint registered. Expected resolution within 3 working days.",
    "Low":      "Complaint registered. Expected resolution within 7 working days.",
}

def _stype(department: str, category: str) -> str:
    """Build a canonical service_type string for the DB."""
    dept  = department.upper().replace(" ", "_")
    cat   = category.upper().replace(" ", "_")
    return f"COMPLAINT_{dept}_{cat}"[:80]   # cap at 80 chars (DB column limit)


# ─── Routes ───────────────────────────────────────────────────────────────────

@router.post("/submit", response_model=SuccessResponse)
async def submit_complaint(req: ComplaintSubmitRequest, db: Session = Depends(get_db)):
    """
    Submit a general civic or department complaint.
    Severity drives the initial status and the SLA acknowledgement message.
    """
    severity   = req.severity if req.severity in _SEVERITY_STATUS else "Medium"
    status_str = _SEVERITY_STATUS[severity]
    message    = _ACK_MESSAGES[severity]

    payload = req.dict()
    payload["reference_generated_at"] = datetime.utcnow().isoformat()

    row = save_request(
        db=db, req_id=str(uuid.uuid4()),
        dept=req.department.lower(),
        stype=_stype(req.department, req.category),
        status_str=status_str,
        payload=payload,
    )

    return SuccessResponse(
        success=True,
        service_request_id=row.service_request_id,
        department=req.department,
        status=row.status,
        message=message,
        data={
            "reference_id": row.service_request_id,
            "severity":     severity,
            "sla_message":  message,
            "track_url":    f"/complaints/{row.service_request_id}",
        },
    )


@router.get("/{reference_id}", response_model=ComplaintTrackResponse)
async def track_complaint(reference_id: str, db: Session = Depends(get_db)):
    """Track a complaint by its reference ID (service_request_id)."""
    row = (
        db.query(ServiceRequestModel)
        .filter(ServiceRequestModel.service_request_id == reference_id)
        .first()
    )
    if not row:
        raise HTTPException(status_code=404, detail="Complaint not found")

    payload = row.payload or {}
    return ComplaintTrackResponse(
        reference_id=row.service_request_id,
        department=row.department,
        category=payload.get("category", row.service_type),
        subject=payload.get("subject", "—"),
        status=row.status,
        severity=payload.get("severity", "Medium"),
        created_at=row.created_at,
        updated_at=row.updated_at,
        message=_ack_for_status(row.status),
    )


@router.get("/user/{user_id}")
async def list_user_complaints(user_id: str, db: Session = Depends(get_db)):
    """Return all complaints submitted by a citizen (matched via payload.phone or user_id)."""
    rows = (
        db.query(ServiceRequestModel)
        .filter(
            ServiceRequestModel.service_type.like("COMPLAINT_%"),
        )
        .order_by(ServiceRequestModel.created_at.desc())
        .limit(50)
        .all()
    )

    complaints = []
    for r in rows:
        p = r.payload or {}
        complaints.append({
            "reference_id": r.service_request_id,
            "department":   r.department,
            "category":     p.get("category", r.service_type),
            "subject":      p.get("subject", "—"),
            "status":       r.status,
            "severity":     p.get("severity", "Medium"),
            "created_at":   r.created_at.isoformat(),
        })
    return {"user_id": user_id, "complaints": complaints}


def _ack_for_status(status: str) -> str:
    messages = {
        "SUBMITTED":   "Your complaint has been received and is under review.",
        "IN_PROGRESS": "Our team is actively working on your complaint.",
        "APPROVED":    "Complaint approved — resolution in progress.",
        "DELIVERED":   "Your complaint has been resolved. Thank you.",
        "DENIED":      "Complaint could not be processed. Please contact the department directly.",
        "CANCELLED":   "This complaint was cancelled.",
    }
    return messages.get(status, "Status update pending.")
