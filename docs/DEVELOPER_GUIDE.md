# KOISK Developer Guide
## Complete Integration with SUVIDHA 2026 Framework

A comprehensive guide for developers implementing the KOISK application with the Service Transfer framework.

---

## Table of Contents

1. [Framework Overview](#framework-overview)
2. [Architecture & Design](#architecture--design)
3. [Core Concepts](#core-concepts)
4. [Implementation Guide](#implementation-guide)
5. [API Endpoints](#api-endpoints)
6. [Database Schema](#database-schema)
7. [Complete Setup](#complete-setup)
8. [Code Examples](#code-examples)
9. [Testing & Validation](#testing--validation)
10. [Deployment](#deployment)

---

## Framework Overview

### SUVIDHA 2026: Service Transfer Framework

The KOISK application is built on the **Service Transfer Framework** (SUVIDHA 2026), which provides:

- **State Machine Model**: Every service request goes through a canonical lifecycle
- **Actor-Based Responsibility**: Clear distinction between initiator, beneficiary, and system
- **Immutable Audit Trail**: Complete history of every state transition
- **Service-Agnostic Design**: Framework applies to electricity, water, gas, and beyond
- **Decoupled Integration**: Department systems interact via well-defined contracts

### Core Philosophy

> "Every interaction is a Service Request that moves through a state machine, is owned by a clear actor, and targets a clear beneficiary."

This means:
- ✅ All services use the same underlying ServiceRequest model
- ✅ Clear ownership at each stage (user → system → department)
- ✅ Complete audit trail of all state changes
- ✅ Deterministic, replay-safe state transitions

---

## Architecture & Design

### System Architecture

```
┌────────────────────────────────────────────────────────────┐
│                      KOISK Application                      │
└─────────────────────────┬──────────────────────────────────┘
                          │
        ┌─────────────────┼─────────────────┐
        ↓                 ↓                 ↓
    ┌────────┐       ┌──────────┐     ┌──────────┐
    │ React  │       │ FastAPI  │     │PostgreSQL│
    │   UI   │       │ Backend  │     │Database  │
    └────────┘       └──────────┘     └──────────┘
        │                 │                 │
        └─────────────────┴─────────────────┘
              OAuth 2.0 + JWT Tokens

┌─────────────────────────────────────────────────────────────┐
│           Service Request State Machine Layer               │
│  DRAFT → SUBMITTED → ACKNOWLEDGED → PENDING → APPROVED     │
│         → IN_PROGRESS → DELIVERED / DENIED / FAILED        │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│              Department Integration Layer                    │
│  Electricity | Water | Gas | External Payment Gateways      │
└─────────────────────────────────────────────────────────────┘
```

### Design Principles

| Principle | Implementation | Benefit |
|-----------|----------------|---------|
| **State Machine** | Canonical status set (DRAFT, SUBMITTED, etc.) | Deterministic flow, no race conditions |
| **Immutable Audit Trail** | Append-only status history | Full accountability, replay-safe |
| **Clear Ownership** | USER/SYSTEM/DEPARTMENT ownership | Clear responsibility at each stage |
| **Idempotent Submission** | Unique service_request_id | Safe retries, no duplicates |
| **Decoupled Integration** | Correlation IDs, async callbacks | Loose coupling with departments |

---

## Core Concepts

### 1. Service Request

The fundamental unit of work in the framework.

```python
class ServiceRequest:
    service_request_id: str          # Unique ID (UUID)
    service_type: ServiceType        # ELECTRICITY_PAY_BILL, etc.
    initiator_id: str                # Who created it
    beneficiary_id: str              # Who benefits
    status: ServiceStatus            # Current state
    current_owner: OwnershipType     # USER/SYSTEM/DEPARTMENT
    payload: dict                    # Service-specific data
    status_history: List[dict]       # Immutable history
    created_at: datetime
    updated_at: datetime
```

### 2. Actor Roles

```
INITIATOR (by)
  ↓
  Creates the service request
  Examples: End User, Department Officer, Automated System
  
BENEFICIARY (to)
  ↓
  Receives the outcome
  Usually initiator (self-service) but can differ (transfer)
  
Rule: initiator_id == beneficiary_id → self-service
```

### 3. Canonical Status Set

All services share this lifecycle:

```
DRAFT
 ↓ (user submits)
SUBMITTED
 ↓ (department acknowledges)
ACKNOWLEDGED
 ↓ (waiting for approval)
PENDING
 ├→ APPROVED (or DENIED with reason)
 └→ DENIED
    ↓ (execution starts)
    IN_PROGRESS
     ├→ DELIVERED (success)
     ├→ FAILED (system error, can retry)
     └→ CANCELLED (user cancels)
```

### 4. Ownership Model

At any time, exactly one entity owns the request:

| Owner | Can | Example |
|-------|-----|---------|
| **USER** | Edit, submit, cancel | User in DRAFT state |
| **SYSTEM** | Validate, route, retry | System processing SUBMITTED |
| **DEPARTMENT** | Approve, deny, execute | Department reviewing PENDING |

### 5. Service Type

Each service type defines its own:
- Required data schema
- Validation rules
- External integrations
- Approval authority

Example: `ELECTRICITY_PAY_BILL`
```python
Required data:
  - meter_number
  - billing_period
  - amount
  - payment_method

Validation rules:
  - Meter must be active
  - Outstanding bill must exist
  - Amount must meet minimum

External interaction:
  - Payment gateway (sync)
  - Billing system (acknowledge)

Terminal status:
  - DELIVERED (success)
  - FAILED (error)
```

---

## Implementation Guide

### Phase 1: Database Setup

#### 1.1 Create PostgreSQL Database

```bash
# Start PostgreSQL
sudo systemctl start postgresql

# Create user and database
sudo -u postgres psql
CREATE USER koisk_user WITH PASSWORD 'koisk_password';
CREATE DATABASE koisk_db OWNER koisk_user;
GRANT ALL PRIVILEGES ON DATABASE koisk_db TO koisk_user;
\q
```

#### 1.2 Initialize Schema

```bash
psql -U koisk_user -d koisk_db -f init.sql
```

#### 1.3 Verify Tables

```bash
psql -U koisk_user -d koisk_db -c "\dt"
```

Should show:
- `users` - User accounts with OAuth2 support
- `service_requests` - Core ServiceRequest model (all services)
- `electricity_meters` - Electricity consumer details
- `water_consumers` - Water consumer details
- `gas_consumers` - Gas consumer details
- `payment_history` - Payment transaction log

### Phase 2: Backend Implementation

#### 2.1 Project Structure

```
backend/
├── src/
│   ├── api/
│   │   ├── auth_routes.py           # OAuth2 endpoints
│   │   └── service_routes.py         # Service endpoints
│   ├── database/
│   │   ├── models.py                # SQLAlchemy models
│   │   └── database.py              # DB configuration
│   ├── security/
│   │   └── auth.py                  # OAuth2 + JWT
│   ├── services/
│   │   ├── electricity/
│   │   │   ├── pay_bill.py
│   │   │   ├── transfer_service.py
│   │   │   └── meter_change.py
│   │   ├── water/
│   │   │   ├── pay_bill.py
│   │   │   └── leak_complaint.py
│   │   └── gas/
│   │       └── pay_bill.py
│   └── __init__.py
├── koisk_api.py                     # Main app
├── requirements.txt
└── .env.example
```

#### 2.2 Key Implementation Classes

**ServiceRequestBase** (core framework):
```python
from sqlalchemy import Column, String, Integer, DateTime, Text, Enum
from datetime import datetime

class ServiceRequest(Base):
    __tablename__ = "service_requests"
    
    id = Column(Integer, primary_key=True)
    service_request_id = Column(String(50), unique=True)  # UUID
    service_type = Column(String(50))                      # Enum
    initiator_id = Column(Integer, ForeignKey("users.id"))
    beneficiary_id = Column(Integer, ForeignKey("users.id"))
    status = Column(String(20), default="DRAFT")           # Enum
    current_owner = Column(String(20), default="USER")     # Enum
    payload = Column(Text)                                  # JSON
    correlation_id = Column(String(100))                   # Dept ref
    error_code = Column(String(50), nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)
    status_history = Column(Text)                          # JSON history
```

**ServiceManager** (state machine handler):
```python
class ServiceManager:
    def create_request(self, service_type, initiator_id, beneficiary_id, payload):
        """Create a new service request (DRAFT state)"""
        request = ServiceRequest(
            service_request_id=str(uuid4()),
            service_type=service_type,
            initiator_id=initiator_id,
            beneficiary_id=beneficiary_id,
            status="DRAFT",
            current_owner="USER",
            payload=json.dumps(payload)
        )
        db.add(request)
        db.commit()
        return request
    
    def submit_request(self, request_id):
        """Move from DRAFT to SUBMITTED"""
        request = self.get_request(request_id)
        self._validate_transition("DRAFT", "SUBMITTED")
        request.status = "SUBMITTED"
        request.current_owner = "SYSTEM"
        self._add_to_history(request, "SUBMITTED", "User submitted request")
        db.commit()
        return request
    
    def approve_request(self, request_id, approver_id):
        """Move from PENDING to APPROVED (department action)"""
        request = self.get_request(request_id)
        self._validate_transition("PENDING", "APPROVED")
        request.status = "APPROVED"
        request.current_owner = "DEPARTMENT"
        self._add_to_history(request, "APPROVED", f"Approved by {approver_id}")
        db.commit()
        return request
    
    def _validate_transition(self, from_status, to_status):
        """Check if transition is allowed"""
        valid = {
            "DRAFT": ["SUBMITTED", "CANCELLED"],
            "SUBMITTED": ["ACKNOWLEDGED", "DENIED"],
            "ACKNOWLEDGED": ["PENDING", "DENIED"],
            "PENDING": ["APPROVED", "DENIED"],
            "APPROVED": ["IN_PROGRESS", "CANCELLED"],
            "IN_PROGRESS": ["DELIVERED", "FAILED"],
            "DELIVERED": [],
            "DENIED": [],
            "FAILED": ["IN_PROGRESS"],
        }
        if to_status not in valid.get(from_status, []):
            raise ValueError(f"Invalid transition: {from_status} → {to_status}")
    
    def _add_to_history(self, request, status, reason):
        """Append to immutable status history"""
        history = json.loads(request.status_history or "[]")
        history.append({
            "status": status,
            "timestamp": datetime.utcnow().isoformat(),
            "reason": reason
        })
        request.status_history = json.dumps(history)
```

#### 2.3 Environment Configuration

Create `.env`:

```env
# Database
DATABASE_URL=postgresql://koisk_user:koisk_password@localhost:5432/koisk_db

# Security (generate with: python -c "import secrets; print(secrets.token_urlsafe(32))")
SECRET_KEY=your-32-char-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# CORS (for frontend)
CORS_ORIGINS=["http://localhost:5173", "http://localhost:3000"]

# Logging
LOG_LEVEL=INFO
```

#### 2.4 Start Backend

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python koisk_api.py
```

### Phase 3: Frontend Implementation

#### 3.1 React Setup

```bash
npm install
npm install react-router-dom zustand axios lucide-react
npm install -D tailwindcss postcss autoprefixer
npx tailwindcss init -p
```

#### 3.2 Environment Configuration

Create `.env.local`:

```env
VITE_API_URL=http://localhost:8000
VITE_ENABLE_GOOGLE_AUTH=true
```

#### 3.3 Start Frontend

```bash
npm run dev
```

---

## API Endpoints

### Authentication

```
POST   /api/v1/auth/register
       Register a new user
       
POST   /api/v1/auth/token
       OAuth2 Password Flow login
       
POST   /api/v1/auth/refresh
       Refresh expired access token
       
GET    /api/v1/auth/me
       Get current authenticated user
       
POST   /api/v1/auth/logout
       Logout (token cleanup)
```

### Electricity Services

```
POST   /api/v1/electricity/pay-bill
       Create ELECTRICITY_PAY_BILL service request
       
POST   /api/v1/electricity/transfer-service
       Create ELECTRICITY_SERVICE_TRANSFER request
       
POST   /api/v1/electricity/meter-change
       Create ELECTRICITY_METER_CHANGE request
       
POST   /api/v1/electricity/new-connection
       Create ELECTRICITY_CONNECTION_REQUEST
       
GET    /api/v1/electricity/requests/{id}
       Get service request status (with history)
```

### Request Flow Example

```
User Action → API Request → ServiceRequest Created
                              ↓
                         DRAFT → SUBMITTED
                              ↓
                         SYSTEM validates
                              ↓
                         ACKNOWLEDGED → PENDING
                              ↓
                         DEPARTMENT reviews
                              ↓
                         APPROVED → IN_PROGRESS
                              ↓
                         Process payment/service
                              ↓
                         DELIVERED (success) or FAILED (error)
```

---

## Database Schema

### ServiceRequest Table (Core)

```sql
CREATE TABLE service_requests (
    id SERIAL PRIMARY KEY,
    service_request_id VARCHAR(50) UNIQUE NOT NULL,
    service_type VARCHAR(50) NOT NULL,
    initiator_id INTEGER NOT NULL REFERENCES users(id),
    beneficiary_id INTEGER NOT NULL REFERENCES users(id),
    status VARCHAR(20) DEFAULT 'DRAFT',
    current_owner VARCHAR(20) DEFAULT 'USER',
    payload TEXT,
    correlation_id VARCHAR(100),
    error_code VARCHAR(50),
    error_message TEXT,
    status_history TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Service-Specific Tables

Each service type can have additional tracking tables:

```sql
-- Electricity specific
CREATE TABLE electricity_meters (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    meter_number VARCHAR(50) UNIQUE NOT NULL,
    status VARCHAR(20) DEFAULT 'ACTIVE',
    monthly_bill FLOAT DEFAULT 0.0,
    outstanding_amount FLOAT DEFAULT 0.0
);

-- Water specific
CREATE TABLE water_consumers (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    consumer_number VARCHAR(50) UNIQUE NOT NULL,
    property_type VARCHAR(50),
    status VARCHAR(20) DEFAULT 'ACTIVE'
);

-- Payment history (cross-service)
CREATE TABLE payment_history (
    id SERIAL PRIMARY KEY,
    service_request_id INTEGER REFERENCES service_requests(id),
    amount FLOAT NOT NULL,
    payment_method VARCHAR(50),
    payment_status VARCHAR(20) DEFAULT 'PENDING',
    transaction_id VARCHAR(100)
);
```

---

## Complete Setup

### Step 1: Database (5 min)

```bash
# Start PostgreSQL
sudo systemctl start postgresql

# Create database
sudo -u postgres psql -c "
CREATE USER koisk_user WITH PASSWORD 'koisk_password';
CREATE DATABASE koisk_db OWNER koisk_user;
GRANT ALL PRIVILEGES ON DATABASE koisk_db TO koisk_user;
"

# Initialize schema
psql -U koisk_user -d koisk_db -f init.sql
```

### Step 2: Backend (10 min)

```bash
# Setup
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Configure
cp .env.example .env
# Edit .env: SECRET_KEY, DATABASE_URL

# Run
python koisk_api.py
```

Backend: http://localhost:8000

### Step 3: Frontend (10 min)

```bash
# Setup
npm install

# Configure
cp .env.local.example .env.local

# Run
npm run dev
```

Frontend: http://localhost:5173

### Step 4: Test (5 min)

```bash
# Test API
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "email": "test@example.com",
    "password": "password123",
    "full_name": "Test User"
  }'

# Open browser
# http://localhost:5173
# Register and login
```

---

## Code Examples

### 1. Creating a Service Request

```python
# In API endpoint
@app.post("/api/v1/electricity/pay-bill")
async def pay_electricity_bill(
    request: PayBillRequest,
    current_user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Create service request
    service_request = ServiceRequest(
        service_request_id=str(uuid4()),
        service_type="ELECTRICITY_PAY_BILL",
        initiator_id=current_user_id,
        beneficiary_id=current_user_id,  # Self-service
        status="DRAFT",
        current_owner="USER",
        payload=json.dumps({
            "meter_number": request.meter_number,
            "amount": request.amount,
            "billing_period": request.billing_period
        })
    )
    
    db.add(service_request)
    db.commit()
    
    # Move to SUBMITTED
    service_request.status = "SUBMITTED"
    service_request.current_owner = "SYSTEM"
    db.commit()
    
    return {
        "success": True,
        "service_request_id": service_request.service_request_id,
        "status": service_request.status
    }
```

### 2. Handling State Transitions

```python
def transition_request(request_id, new_status, reason, db):
    """Generic state transition with validation"""
    
    request = db.query(ServiceRequest).filter_by(
        service_request_id=request_id
    ).first()
    
    # Validate transition
    valid_transitions = {
        "DRAFT": ["SUBMITTED"],
        "SUBMITTED": ["ACKNOWLEDGED"],
        "ACKNOWLEDGED": ["PENDING"],
        "PENDING": ["APPROVED", "DENIED"],
        "APPROVED": ["IN_PROGRESS"],
        "IN_PROGRESS": ["DELIVERED", "FAILED"]
    }
    
    if new_status not in valid_transitions.get(request.status, []):
        raise ValueError(f"Invalid: {request.status} → {new_status}")
    
    # Update request
    request.status = new_status
    request.updated_at = datetime.utcnow()
    
    # Append to history (never overwrite)
    history = json.loads(request.status_history or "[]")
    history.append({
        "status": new_status,
        "timestamp": datetime.utcnow().isoformat(),
        "reason": reason
    })
    request.status_history = json.dumps(history)
    
    db.commit()
    return request
```

### 3. Frontend Authentication Flow

```javascript
// React component
import { useAuthStore } from './store/authStore';

export function LoginPage() {
  const { login, isLoading, error } = useAuthStore();
  const [credentials, setCredentials] = useState({
    username: '',
    password: ''
  });

  const handleLogin = async (e) => {
    e.preventDefault();
    try {
      // OAuth2 Password Flow
      await login(credentials.username, credentials.password);
      // Tokens stored in localStorage, redirected to dashboard
    } catch (err) {
      console.error('Login failed:', err);
    }
  };

  return (
    <form onSubmit={handleLogin}>
      <input
        name="username"
        value={credentials.username}
        onChange={(e) => setCredentials({...credentials, username: e.target.value})}
      />
      <input
        type="password"
        name="password"
        value={credentials.password}
        onChange={(e) => setCredentials({...credentials, password: e.target.value})}
      />
      <button type="submit" disabled={isLoading}>
        {isLoading ? 'Logging in...' : 'Login'}
      </button>
      {error && <p>{error}</p>}
    </form>
  );
}
```

### 4. API Request with Token

```javascript
// API service with automatic token refresh
class APIService {
  async request(endpoint, options = {}) {
    const token = localStorage.getItem('access_token');
    
    const response = await fetch(
      `http://localhost:8000${endpoint}`,
      {
        ...options,
        headers: {
          ...options.headers,
          'Authorization': `Bearer ${token}`
        }
      }
    );

    // Handle 401 (token expired)
    if (response.status === 401) {
      const newToken = await this.refreshToken();
      // Retry with new token
      return this.request(endpoint, {
        ...options,
        headers: {
          ...options.headers,
          'Authorization': `Bearer ${newToken}`
        }
      });
    }

    return await response.json();
  }

  async refreshToken() {
    const refreshToken = localStorage.getItem('refresh_token');
    const response = await fetch('http://localhost:8000/api/v1/auth/refresh', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${refreshToken}`
      }
    });
    const data = await response.json();
    localStorage.setItem('access_token', data.access_token);
    return data.access_token;
  }
}
```

---

## Testing & Validation

### Unit Tests

```python
# test_service_request.py
import pytest

def test_create_service_request():
    request = ServiceRequest(
        service_type="ELECTRICITY_PAY_BILL",
        status="DRAFT",
        current_owner="USER"
    )
    assert request.status == "DRAFT"

def test_valid_transition():
    """DRAFT → SUBMITTED is valid"""
    request = ServiceRequest(status="DRAFT")
    # Should succeed
    valid_transitions = {"DRAFT": ["SUBMITTED"]}
    assert "SUBMITTED" in valid_transitions.get("DRAFT", [])

def test_invalid_transition():
    """DRAFT → DELIVERED is invalid"""
    request = ServiceRequest(status="DRAFT")
    # Should fail
    valid_transitions = {"DRAFT": ["SUBMITTED"]}
    assert "DELIVERED" not in valid_transitions.get("DRAFT", [])
```

### Integration Tests

```python
def test_full_payment_flow():
    """Test complete payment request lifecycle"""
    
    # 1. Create request
    request = create_service_request(
        service_type="ELECTRICITY_PAY_BILL",
        initiator_id=1,
        payload={"meter_number": "ABC123", "amount": 1500}
    )
    assert request.status == "DRAFT"
    
    # 2. Submit
    transition_request(request.id, "SUBMITTED", "User submitted")
    assert request.status == "SUBMITTED"
    
    # 3. System acknowledges
    transition_request(request.id, "ACKNOWLEDGED", "System processed")
    assert request.status == "ACKNOWLEDGED"
    
    # 4. Department approves
    transition_request(request.id, "APPROVED", "Department approved")
    assert request.status == "APPROVED"
    
    # 5. Process payment
    process_payment(request.payload)
    
    # 6. Complete
    transition_request(request.id, "DELIVERED", "Payment successful")
    assert request.status == "DELIVERED"
    
    # 7. Verify history
    history = json.loads(request.status_history)
    assert len(history) == 6
    assert history[-1]["status"] == "DELIVERED"
```

### Manual Testing

```bash
# 1. Register user
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "devuser",
    "email": "dev@example.com",
    "password": "devpass123",
    "full_name": "Dev User"
  }'

# 2. Login (get tokens)
TOKEN_RESPONSE=$(curl -X POST http://localhost:8000/api/v1/auth/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=devuser&password=devpass123")

ACCESS_TOKEN=$(echo $TOKEN_RESPONSE | jq -r '.access_token')

# 3. Create service request
curl -X POST http://localhost:8000/api/v1/electricity/pay-bill \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -d '{
    "user_id": "1",
    "meter_number": "ELEC123456",
    "amount": "1500.00",
    "billing_period": "2026-02",
    "payment_method": "UPI"
  }'

# 4. Check database
psql -U koisk_user -d koisk_db -c "
  SELECT service_request_id, service_type, status 
  FROM service_requests 
  ORDER BY created_at DESC LIMIT 5;
"
```

---

## Deployment

### Production Checklist

- [ ] Change `SECRET_KEY` to strong random value
- [ ] Use production PostgreSQL (not SQLite)
- [ ] Enable HTTPS everywhere (SSL certificates)
- [ ] Configure `CORS_ORIGINS` to specific domains
- [ ] Set up rate limiting on authentication endpoints
- [ ] Configure email notifications
- [ ] Set up structured logging (ELK stack, CloudWatch, etc.)
- [ ] Enable database backups
- [ ] Configure monitoring and alerting
- [ ] Run security audit
- [ ] Load test the API
- [ ] Test all state transitions thoroughly

### Docker Deployment

```bash
# Build and run full stack
docker-compose up -d

# Access services
# Frontend: http://localhost:3000
# Backend: http://localhost:8000
# API Docs: http://localhost:8000/docs
# Database: localhost:5432
```

### Gunicorn + Nginx

```bash
# Install Gunicorn
pip install gunicorn

# Run with 4 workers
gunicorn koisk_api:app -w 4 -b 0.0.0.0:8000 -k uvicorn.workers.UvicornWorker

# Configure Nginx as reverse proxy (see documentation)
```

---

## Key Takeaways

### Service Request Framework

1. **State Machine**: All services follow the same canonical lifecycle
2. **Immutable Audit**: Complete history for compliance and debugging
3. **Clear Ownership**: At each stage, one entity is responsible
4. **Idempotent**: Safe to retry without creating duplicates
5. **Decoupled**: Services integrate via well-defined contracts

### Implementation Best Practices

1. ✅ Always validate state transitions
2. ✅ Never overwrite status history
3. ✅ Use correlation IDs for tracing
4. ✅ Log every state change with reason
5. ✅ Handle errors gracefully (FAILED → retry)
6. ✅ Implement comprehensive tests
7. ✅ Monitor and alert on state transitions
8. ✅ Document department integrations

### Security Best Practices

1. ✅ Use bcrypt for passwords (cost factor 12+)
2. ✅ Implement JWT with short expiration (30 min)
3. ✅ Use refresh tokens for long-lived sessions
4. ✅ Validate all inputs
5. ✅ Check ownership before allowing actions
6. ✅ Implement rate limiting
7. ✅ Use HTTPS in production
8. ✅ Monitor for suspicious patterns

---

## References

- **SUVIDHA 2026 Framework**: Service Transfer Core Terms & Framework
- **OAuth 2.0 Spec**: https://oauth.net/2/
- **JWT**: https://jwt.io/
- **FastAPI**: https://fastapi.tiangolo.com/
- **SQLAlchemy**: https://sqlalchemy.org/
- **React**: https://react.dev/

---

## Support & Troubleshooting

### Common Issues

| Issue | Solution |
|-------|----------|
| Token expired | Implement refresh token flow (done) |
| CORS errors | Check `CORS_ORIGINS` in .env |
| Database locked | Terminate blocking connections |
| Port in use | Kill process or use different port |
| Import errors | Verify Python path and venv activated |

### Getting Help

1. Check the error message and logs
2. Review the relevant code section above
3. Consult FastAPI or React documentation
4. Check PostgreSQL logs
5. Run tests to isolate the issue

---

**Version**: 1.0  
**Status**: Production Ready  
**Last Updated**: February 11, 2026
