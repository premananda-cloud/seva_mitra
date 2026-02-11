# KOISK Developer Guide v2.0
## Implementation of SUVIDHA 2026 Service Transfer Framework

**Complete technical reference for implementing KOISK with the canonical Service Transfer framework.**

---

## Quick Navigation

- [Framework Overview](#framework-overview) - What is SUVIDHA 2026?
- [Core Concepts](#core-concepts) - ServiceRequest, State Machine, Actors
- [Architecture](#architecture) - System design
- [Implementation](#implementation-guide) - Build step by step
- [API Reference](#api-endpoints) - All endpoints
- [Database](#database-schema) - Schema design
- [Setup](#complete-setup) - Deploy everything
- [Code Examples](#code-examples) - Implementation patterns
- [Testing](#testing--validation) - Validation strategy
- [Production](#deployment) - Deploy safely

---

## Framework Overview

### What is SUVIDHA 2026?

SUVIDHA 2026 (Service Transfer Framework) is the canonical approach to managing government utility services. It provides:

✅ **Unified Service Model** - All services (electricity, water, gas) use the same framework  
✅ **State Machine Pattern** - Deterministic, auditable state transitions  
✅ **Actor-Based Responsibility** - Clear ownership at each stage  
✅ **Immutable Audit Trail** - Complete history for accountability  
✅ **Decoupled Integration** - Department systems integrate via contracts  
✅ **Idempotent Operations** - Safe retries without duplicates  

### Core Philosophy

> "Every interaction is a **Service Request** that moves through a **state machine**, is owned by a clear **actor**, and targets a clear **beneficiary**."

---

## Core Concepts

### 1. Service Request (The Fundamental Unit)

A `ServiceRequest` is a single, auditable unit of work:

```python
@dataclass
class ServiceRequest:
    service_request_id: str          # Unique identifier (UUID)
    service_type: ServiceType        # What service? (ELECTRICITY_PAY_BILL, etc.)
    initiator_id: int                # WHO created it? (immutable)
    beneficiary_id: int              # WHO benefits?
    status: ServiceStatus            # Current state (DRAFT, SUBMITTED, etc.)
    current_owner: OwnershipType     # Who's responsible? (USER/SYSTEM/DEPT)
    payload: dict                    # Service-specific data
    status_history: List[dict]       # Immutable state transition log
    correlation_id: str              # Department reference for tracking
    created_at: datetime
    updated_at: datetime
```

**Example: Electricity Bill Payment**
```python
request = ServiceRequest(
    service_request_id="req-abc123xyz",
    service_type="ELECTRICITY_PAY_BILL",
    initiator_id=42,                 # User 42 is paying
    beneficiary_id=42,               # Same user benefits (self-service)
    status="DRAFT",
    current_owner="USER",
    payload={
        "meter_number": "ELEC123456",
        "amount": 1500.00,
        "billing_period": "2026-02",
        "payment_method": "UPI"
    }
)
```

### 2. State Machine (The Canonical Lifecycle)

All services follow this exact state flow:

```
┌─────────────────────────────────────────────────────────────┐
│              SERVICE REQUEST LIFECYCLE                       │
└─────────────────────────────────────────────────────────────┘

DRAFT                    ← User creating/editing
├─ Edit payload          ← Editable state
├─ Change to SUBMITTED   ← User submits
└─ Or CANCELLED          ← User cancels

SUBMITTED                ← Request locked, sent to system
├─ System validates
├─ Change to ACKNOWLEDGED
└─ Or DENIED

ACKNOWLEDGED             ← Department received it, issued tracking ID
├─ Change to PENDING
└─ Or DENIED

PENDING                  ← Waiting for approval/external action
├─ Department reviews
├─ Change to APPROVED
└─ Or DENIED (with reason_code)

APPROVED                 ← Authorized, ready for execution
├─ Change to IN_PROGRESS
└─ Or CANCELLED

IN_PROGRESS              ← Execution in progress
├─ Process payment/action
├─ Change to DELIVERED (success)
├─ Or FAILED (system error)
└─ FAILED can retry → IN_PROGRESS

DELIVERED ✓              ← Complete and successful
DENIED ✗                 ← Rejected with reason
FAILED ⚠️                ← System error, can retry
CANCELLED ⊘              ← Withdrawn by initiator
```

### 3. Actor Roles (Who Does What)

| Actor | Role | Example |
|-------|------|---------|
| **Initiator** | Creates the request (immutable) | End user, department officer, automated system |
| **Beneficiary** | Receives the outcome | Often same as initiator, but can differ (transfers) |
| **Owner** | Currently responsible | USER (draft) → SYSTEM (validation) → DEPARTMENT (approval) |

**Rule: Self-Service Detection**
```python
if request.initiator_id == request.beneficiary_id:
    # Self-service request (user doing it for themselves)
    # Examples: pay bill, report leak
    assert is_self_service = True
else:
    # Transfer request (user doing it for someone else)
    # Examples: transfer service to another person
    assert is_transfer = True
    # Requires authorization from beneficiary
```

### 4. Ownership Model (Responsibility at Each Stage)

At any moment, exactly ONE entity owns the request:

```
DRAFT             → USER          (User can edit)
SUBMITTED         → SYSTEM        (System validates/routes)
ACKNOWLEDGED      → DEPARTMENT    (Dept acknowledges)
PENDING           → DEPARTMENT    (Dept approves/denies)
APPROVED          → SYSTEM        (System executes)
IN_PROGRESS       → SYSTEM        (System processing)
DELIVERED/DENIED  → ARCHIVE       (Immutable history)
```

### 5. Status Visibility (What Users See)

Users see a simplified view:

```python
# User visibility
User sees:
  DRAFT → SUBMITTED → PROCESSING → COMPLETED/REJECTED

# What it maps to internally:
- DRAFT → DRAFT
- SUBMITTED, ACKNOWLEDGED, PENDING, APPROVED → PROCESSING
- DELIVERED → COMPLETED
- DENIED, FAILED, CANCELLED → REJECTED
```

### 6. Service Types (Concrete Implementations)

Each service type defines its own schema and rules:

#### ELECTRICITY_PAY_BILL
```python
RequiredData = {
    "meter_number": str,           # From user's bill
    "billing_period": str,         # "2026-02"
    "amount": float,               # Payment amount
    "payment_method": str,         # UPI, Card, etc.
    "payment_reference": str       # Transaction ID
}

ValidationRules = {
    "meter_must_be_active": True,
    "outstanding_bill_must_exist": True,
    "amount_must_be_non_negative": True
}

ExternalIntegrations = [
    ("payment_gateway", "sync"),   # Synchronous
    ("billing_system", "async")    # Acknowledge
]

TerminalStatuses = ["DELIVERED", "FAILED"]
```

#### ELECTRICITY_SERVICE_TRANSFER
```python
RequiredData = {
    "meter_number": str,
    "old_customer_id": int,
    "new_customer_id": int,
    "identity_proof_ref": str,
    "ownership_proof_ref": str,
    "effective_date": date
}

# Note: initiator_id != beneficiary_id (transfer to someone else)
# Requires authorization from old customer

TerminalStatuses = ["DELIVERED", "DENIED"]
```

---

## Architecture

### System Layers

```
┌─────────────────────────────────────────────────────┐
│         User Interface (React Frontend)             │
│  - Login, Dashboard, Service Cards                  │
│  - Form validation, payment UI                      │
└────────────────────┬────────────────────────────────┘
                     │ HTTPS + OAuth2/JWT
┌────────────────────▼────────────────────────────────┐
│  REST API Layer (FastAPI)                           │
│  - Authentication endpoints (/auth/*)               │
│  - Service endpoints (/electricity/*, /water/*, etc)│
│  - State machine enforcement                        │
│  - Input validation                                 │
└────────────────────┬────────────────────────────────┘
                     │ ORM (SQLAlchemy)
┌────────────────────▼────────────────────────────────┐
│  Business Logic Layer (ServiceManagers)             │
│  - ServiceRequest creation/transitions              │
│  - Validation rules enforcement                     │
│  - Department integration triggers                  │
│  - Audit trail recording                            │
└────────────────────┬────────────────────────────────┘
                     │ SQL
┌────────────────────▼────────────────────────────────┐
│  Data Layer (PostgreSQL)                            │
│  - service_requests (core)                          │
│  - users, meters, consumers                         │
│  - payment_history                                  │
│  - Immutable status_history (JSON)                  │
└─────────────────────────────────────────────────────┘
```

### Data Flow Example: Pay Electricity Bill

```
User Action (React)
    │
    ↓ POST /api/v1/electricity/pay-bill
    │  {meter_number, amount, billing_period, ...}
    │
    ↓ FastAPI receives request
    │
    ↓ Validate user is authenticated (JWT)
    │
    ↓ Create ServiceRequest (DRAFT status)
    │  • Generate service_request_id
    │  • Set initiator_id = current_user
    │  • Set beneficiary_id = current_user (self-service)
    │  • Store payload
    │
    ↓ Transition to SUBMITTED
    │  • Validate state transition (DRAFT → SUBMITTED)
    │  • Append to status_history
    │  • Update current_owner = SYSTEM
    │
    ↓ Validate business rules
    │  • Meter must exist and be active
    │  • Bill must exist
    │  • Amount must be valid
    │
    ↓ Transition to ACKNOWLEDGED
    │  • System acknowledges receipt
    │  • Generate correlation_id
    │  • Append to history
    │
    ↓ Process payment (external integration)
    │  • Call payment gateway (synchronous)
    │  • If success → proceed
    │  • If failure → transition to FAILED
    │
    ↓ Transition to DELIVERED
    │  • Payment successful
    │  • Record in payment_history
    │  • Append final status to history
    │
    ↓ Return to user
    │  {service_request_id, status, confirmation, ...}
    │
    ↓ React displays confirmation
    │  User can view status in history
```

---

## Implementation Guide

### Phase 1: Core Data Model

```python
# models.py - ServiceRequest base

class ServiceRequest(Base):
    __tablename__ = "service_requests"
    
    # Identifiers
    id = Column(Integer, primary_key=True)
    service_request_id = Column(String(50), unique=True, nullable=False)
    
    # Service definition
    service_type = Column(String(50), nullable=False)  # ELECTRICITY_PAY_BILL
    
    # Actors
    initiator_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    beneficiary_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # State machine
    status = Column(String(20), default="DRAFT", nullable=False)
    current_owner = Column(String(20), default="USER", nullable=False)
    
    # Data & tracking
    payload = Column(Text, nullable=False)  # JSON: service-specific data
    status_history = Column(Text, default="[]")  # JSON: [{status, timestamp, reason}]
    correlation_id = Column(String(100), nullable=True)  # Department ref
    
    # Error handling
    error_code = Column(String(50), nullable=True)
    error_message = Column(Text, nullable=True)
    
    # Audit
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
```

### Phase 2: State Machine Implementation

```python
# state_machine.py

class ServiceRequestStateMachine:
    """
    Enforces canonical state transitions.
    Every transition is validated and logged.
    """
    
    VALID_TRANSITIONS = {
        "DRAFT": ["SUBMITTED", "CANCELLED"],
        "SUBMITTED": ["ACKNOWLEDGED", "DENIED"],
        "ACKNOWLEDGED": ["PENDING", "DENIED"],
        "PENDING": ["APPROVED", "DENIED"],
        "APPROVED": ["IN_PROGRESS", "CANCELLED"],
        "IN_PROGRESS": ["DELIVERED", "FAILED"],
        "FAILED": ["IN_PROGRESS"],  # Can retry
        "DELIVERED": [],
        "DENIED": [],
        "CANCELLED": []
    }
    
    def validate_transition(self, from_status: str, to_status: str) -> bool:
        """Check if transition is allowed"""
        allowed = self.VALID_TRANSITIONS.get(from_status, [])
        if to_status not in allowed:
            raise InvalidStateTransition(
                f"Cannot transition from {from_status} to {to_status}"
            )
        return True
    
    def transition(self, request: ServiceRequest, to_status: str, reason: str):
        """Execute state transition with audit trail"""
        
        # 1. Validate
        self.validate_transition(request.status, to_status)
        
        # 2. Update status
        old_status = request.status
        request.status = to_status
        request.updated_at = datetime.utcnow()
        
        # 3. Update ownership based on status
        ownership_map = {
            "DRAFT": "USER",
            "SUBMITTED": "SYSTEM",
            "ACKNOWLEDGED": "DEPARTMENT",
            "PENDING": "DEPARTMENT",
            "APPROVED": "SYSTEM",
            "IN_PROGRESS": "SYSTEM"
        }
        request.current_owner = ownership_map.get(to_status, "SYSTEM")
        
        # 4. Append to immutable history
        history = json.loads(request.status_history or "[]")
        history.append({
            "from_status": old_status,
            "to_status": to_status,
            "timestamp": datetime.utcnow().isoformat(),
            "reason": reason,
            "owner": request.current_owner
        })
        request.status_history = json.dumps(history)
        
        # 5. Persist
        db.add(request)
        db.commit()
        
        # 6. Log for audit
        logger.info(f"Request {request.service_request_id}: "
                   f"{old_status} → {to_status} ({reason})")
        
        return request
```

### Phase 3: Service-Specific Handlers

```python
# services/electricity/pay_bill.py

class ElectricityPayBillService:
    """Handler for ELECTRICITY_PAY_BILL service type"""
    
    def create_request(self, user_id: int, payload: dict) -> ServiceRequest:
        """Create a new pay bill request in DRAFT state"""
        
        # Validate required fields
        required = ["meter_number", "amount", "billing_period", "payment_method"]
        for field in required:
            if field not in payload:
                raise MissingFieldError(f"Missing required field: {field}")
        
        # Create request
        request = ServiceRequest(
            service_request_id=str(uuid4()),
            service_type="ELECTRICITY_PAY_BILL",
            initiator_id=user_id,
            beneficiary_id=user_id,  # Self-service
            status="DRAFT",
            current_owner="USER",
            payload=json.dumps(payload)
        )
        
        db.add(request)
        db.commit()
        
        return request
    
    def validate_request(self, request: ServiceRequest) -> bool:
        """Validate business rules before submission"""
        
        payload = json.loads(request.payload)
        meter_number = payload["meter_number"]
        amount = payload["amount"]
        
        # Rule 1: Meter must be active
        meter = db.query(ElectricityMeter).filter_by(
            meter_number=meter_number
        ).first()
        if not meter or meter.status != "ACTIVE":
            raise ValidationError("Meter is not active")
        
        # Rule 2: Outstanding bill must exist
        if not meter.outstanding_amount or meter.outstanding_amount == 0:
            raise ValidationError("No outstanding bill")
        
        # Rule 3: Amount must be sufficient
        if amount < meter.outstanding_amount:
            raise ValidationError("Amount must cover at least minimum due")
        
        return True
    
    def submit_request(self, request: ServiceRequest):
        """Submit request for processing"""
        
        # Validate
        self.validate_request(request)
        
        # Transition DRAFT → SUBMITTED
        state_machine.transition(
            request,
            "SUBMITTED",
            "User submitted payment request"
        )
        
        # Transition SUBMITTED → ACKNOWLEDGED (system auto-ack)
        state_machine.transition(
            request,
            "ACKNOWLEDGED",
            "System acknowledged receipt"
        )
        
        # Auto-proceed to execution for synchronous payments
        self.process_payment(request)
    
    def process_payment(self, request: ServiceRequest):
        """Process the actual payment"""
        
        payload = json.loads(request.payload)
        
        try:
            # Transition to IN_PROGRESS
            state_machine.transition(
                request,
                "IN_PROGRESS",
                "Payment processing started"
            )
            
            # Call payment gateway
            result = payment_gateway.process_payment(
                amount=payload["amount"],
                method=payload["payment_method"],
                reference=payload["payment_reference"]
            )
            
            if result.success:
                # Success: record payment and deliver
                self._record_payment(request, result)
                
                state_machine.transition(
                    request,
                    "DELIVERED",
                    f"Payment successful: {result.transaction_id}"
                )
            else:
                # Failure: mark as failed
                state_machine.transition(
                    request,
                    "FAILED",
                    f"Payment failed: {result.error}"
                )
                request.error_code = "PAYMENT_FAILED"
                request.error_message = result.error
                db.commit()
                
        except Exception as e:
            # System error: mark as failed, can retry
            state_machine.transition(
                request,
                "FAILED",
                f"System error: {str(e)}"
            )
            request.error_code = "SYSTEM_ERROR"
            request.error_message = str(e)
            db.commit()
    
    def _record_payment(self, request: ServiceRequest, result):
        """Record payment in history"""
        payment = PaymentHistory(
            service_request_id=request.id,
            service_type="ELECTRICITY",
            amount=json.loads(request.payload)["amount"],
            payment_method=json.loads(request.payload)["payment_method"],
            payment_status="SUCCESS",
            transaction_id=result.transaction_id
        )
        db.add(payment)
        
        # Update meter
        payload = json.loads(request.payload)
        meter = db.query(ElectricityMeter).filter_by(
            meter_number=payload["meter_number"]
        ).first()
        meter.outstanding_amount -= payload["amount"]
        meter.outstanding_amount = max(0, meter.outstanding_amount)
        
        db.commit()
```

### Phase 4: API Endpoints

```python
# api/electricity_routes.py

@router.post("/api/v1/electricity/pay-bill")
async def pay_electricity_bill(
    request_data: PayBillRequest,
    current_user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create and process an electricity bill payment request.
    
    Flow:
    1. Create request (DRAFT)
    2. Validate rules
    3. Submit (SUBMITTED → ACKNOWLEDGED)
    4. Process payment (IN_PROGRESS)
    5. Complete (DELIVERED) or fail (FAILED)
    """
    
    try:
        # Create service
        service = ElectricityPayBillService()
        
        # Step 1: Create in DRAFT
        service_request = service.create_request(
            current_user_id,
            request_data.dict()
        )
        
        # Step 2-5: Submit and process
        service.submit_request(service_request)
        
        # Refresh from DB to get updated state
        db.refresh(service_request)
        
        return {
            "success": True,
            "service_request_id": service_request.service_request_id,
            "status": service_request.status,
            "message": f"Payment {service_request.status.lower()}"
        }
        
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error processing payment: {e}")
        raise HTTPException(status_code=500, detail="Internal error")


@router.get("/api/v1/electricity/requests/{request_id}")
async def get_request_status(
    request_id: str,
    current_user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get status and history of a service request"""
    
    request = db.query(ServiceRequest).filter_by(
        service_request_id=request_id
    ).first()
    
    if not request:
        raise HTTPException(status_code=404, detail="Request not found")
    
    # Verify ownership
    if request.initiator_id != current_user_id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    return {
        "service_request_id": request.service_request_id,
        "status": request.status,
        "created_at": request.created_at.isoformat(),
        "updated_at": request.updated_at.isoformat(),
        "history": json.loads(request.status_history)
    }
```

---

## API Endpoints

### Core Authentication
```
POST   /api/v1/auth/register          Register user
POST   /api/v1/auth/token             OAuth2 login
POST   /api/v1/auth/refresh           Refresh token
GET    /api/v1/auth/me                Get current user
```

### Electricity Services
```
POST   /api/v1/electricity/pay-bill               Create bill payment
POST   /api/v1/electricity/transfer-service       Request transfer
POST   /api/v1/electricity/meter-change           Request meter change
POST   /api/v1/electricity/new-connection         Apply for connection
GET    /api/v1/electricity/requests/{id}          Get request status
```

### Water Services
```
POST   /api/v1/water/pay-bill                     Pay bill
POST   /api/v1/water/leak-complaint               Report leak
GET    /api/v1/water/requests/{id}                Get status
```

### Gas Services
```
POST   /api/v1/gas/pay-bill                       Pay bill
GET    /api/v1/gas/requests/{id}                  Get status
```

---

## Database Schema

### Core Table: service_requests

```sql
CREATE TABLE service_requests (
    id SERIAL PRIMARY KEY,
    service_request_id VARCHAR(50) UNIQUE NOT NULL,
    service_type VARCHAR(50) NOT NULL,
    initiator_id INTEGER NOT NULL REFERENCES users(id),
    beneficiary_id INTEGER NOT NULL REFERENCES users(id),
    status VARCHAR(20) DEFAULT 'DRAFT',
    current_owner VARCHAR(20) DEFAULT 'USER',
    payload TEXT NOT NULL,  -- JSON: service-specific data
    status_history TEXT DEFAULT '[]',  -- JSON: [{status, timestamp, reason}]
    correlation_id VARCHAR(100),
    error_code VARCHAR(50),
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_initiator (initiator_id),
    INDEX idx_status (status),
    INDEX idx_created_at (created_at DESC)
);
```

The `payload` is service-specific JSON:
```json
{
    "meter_number": "ELEC123456",
    "amount": 1500.00,
    "billing_period": "2026-02",
    "payment_method": "UPI",
    "payment_reference": "ref123"
}
```

The `status_history` is immutable:
```json
[
    {
        "from_status": "DRAFT",
        "to_status": "SUBMITTED",
        "timestamp": "2026-02-11T10:00:00Z",
        "reason": "User submitted",
        "owner": "SYSTEM"
    },
    {
        "from_status": "SUBMITTED",
        "to_status": "ACKNOWLEDGED",
        "timestamp": "2026-02-11T10:00:01Z",
        "reason": "System acknowledged",
        "owner": "DEPARTMENT"
    }
]
```

---

## Complete Setup

### 1. Database
```bash
sudo systemctl start postgresql
sudo -u postgres psql -c "
  CREATE USER koisk_user WITH PASSWORD 'koisk_password';
  CREATE DATABASE koisk_db OWNER koisk_user;
"
psql -U koisk_user -d koisk_db -f init.sql
```

### 2. Backend
```bash
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env: SECRET_KEY, DATABASE_URL
python koisk_api.py
```

### 3. Frontend
```bash
npm install
cp .env.local.example .env.local
npm run dev
```

### 4. Test
- Visit http://localhost:5173
- Register and login
- Create a service request
- Check status and history

---

## Code Examples

### Example 1: Complete Payment Flow

```python
# Step 1: User submits payment request
user = User(id=42, username="john")
payload = {
    "meter_number": "ELEC999",
    "amount": 1500,
    "billing_period": "2026-02",
    "payment_method": "UPI"
}

# Step 2: Service creates and processes
service = ElectricityPayBillService()
request = service.create_request(user.id, payload)

assert request.status == "DRAFT"
assert request.current_owner == "USER"

# Step 3: User submits
service.submit_request(request)

# Request transitions:
# DRAFT → SUBMITTED (locked)
# SUBMITTED → ACKNOWLEDGED (system processed)
# ACKNOWLEDGED → IN_PROGRESS (payment processing)
# IN_PROGRESS → DELIVERED (success) or FAILED (error)

assert request.status == "DELIVERED"
assert len(json.loads(request.status_history)) >= 4

# Step 4: User can view history
history = json.loads(request.status_history)
for event in history:
    print(f"{event['timestamp']}: {event['from_status']} → {event['to_status']}")
```

### Example 2: Transfer Request (Different Initiator/Beneficiary)

```python
# Service transfer: old_customer → new_customer
payload = {
    "meter_number": "ELEC456",
    "old_customer_id": 10,
    "new_customer_id": 20,
    "effective_date": "2026-03-01"
}

service = ElectricityTransferService()
request = service.create_request(
    initiator_id=10,        # Old customer initiates
    beneficiary_id=20,      # New customer benefits
    payload=payload
)

# Note: initiator_id != beneficiary_id means it's a TRANSFER
assert request.initiator_id != request.beneficiary_id

# Requires approval from both parties
service.get_authorization(old_customer_id=10)
service.get_authorization(new_customer_id=20)

service.submit_request(request)

# Status flow:
# DRAFT → SUBMITTED → ACKNOWLEDGED → PENDING → APPROVED → DELIVERED
```

### Example 3: Error Handling & Retries

```python
# Payment fails
try:
    service.process_payment(request)
except PaymentGatewayError as e:
    # Request is now in FAILED state
    assert request.status == "FAILED"
    assert request.error_code == "PAYMENT_FAILED"
    
    # System can retry (FAILED → IN_PROGRESS)
    state_machine.transition(
        request,
        "IN_PROGRESS",
        "Retrying after initial failure"
    )
    
    # Try again
    service.process_payment(request)
```

---

## Testing & Validation

### Unit Tests
```python
def test_state_machine_transitions():
    """Verify state transitions"""
    assert "SUBMITTED" in machine.VALID_TRANSITIONS["DRAFT"]
    assert "IN_PROGRESS" in machine.VALID_TRANSITIONS["APPROVED"]
    assert "DRAFT" not in machine.VALID_TRANSITIONS["DELIVERED"]

def test_service_request_creation():
    """Verify request is created in DRAFT"""
    request = create_service_request(...)
    assert request.status == "DRAFT"
    assert request.current_owner == "USER"

def test_immutable_history():
    """Verify history is append-only"""
    request = ServiceRequest(...)
    original = request.status_history
    
    transition(request, "SUBMITTED", "user action")
    updated = request.status_history
    
    assert len(updated) > len(original)
    assert original in updated  # History preserved
```

### Integration Tests
```python
def test_full_payment_flow():
    """Test complete electricity bill payment"""
    
    # Create
    request = service.create_request(user_id, payload)
    assert request.status == "DRAFT"
    
    # Submit and validate
    service.submit_request(request)
    assert request.status == "DELIVERED" or request.status == "FAILED"
    
    # Verify history
    history = json.loads(request.status_history)
    assert len(history) >= 3
    assert history[-1]["to_status"] in ["DELIVERED", "FAILED"]
```

---

## Deployment

### Security Checklist
- [ ] Generate strong SECRET_KEY
- [ ] Use production database (PostgreSQL)
- [ ] Enable HTTPS (SSL certificates)
- [ ] Configure CORS to specific domains
- [ ] Implement rate limiting
- [ ] Set up monitoring and alerting
- [ ] Configure database backups
- [ ] Test all state transitions
- [ ] Load test API
- [ ] Security audit

### Production Setup
```bash
# Install Gunicorn
pip install gunicorn

# Run with 4 workers
gunicorn koisk_api:app -w 4 -b 0.0.0.0:8000 \
  -k uvicorn.workers.UvicornWorker

# Or use Docker
docker-compose up -d
```

---

## Key Takeaways

✅ **ServiceRequest is fundamental** - All services use same model  
✅ **State machine is canonical** - Fixed transitions, immutable history  
✅ **Ownership is explicit** - Clear who's responsible at each stage  
✅ **Audit trail is complete** - Every change is logged  
✅ **Integration is decoupled** - Department systems via contracts  
✅ **Operations are idempotent** - Safe to retry  

---

**Version**: 2.0  
**Status**: Production Ready ✅  
**Last Updated**: February 11, 2026
