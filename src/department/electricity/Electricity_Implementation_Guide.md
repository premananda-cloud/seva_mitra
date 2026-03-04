# SUVIDHA 2026 - Electricity Services Implementation Guide

## Overview

This guide shows how to integrate the Electricity Services module into your SUVIDHA KIOSK application following the Service Transfer Framework.

---

## 1. Project Structure

```
suvidha-kiosk/
├── backend/
│   ├── services/
│   │   ├── electricity/
│   │   │   ├── __init__.py
│   │   │   ├── models.py              # ServiceRequest, Bill, Payment, Meter models
│   │   │   ├── services.py            # All electricity services
│   │   │   ├── validators.py          # Validation logic
│   │   │   ├── routes.py              # API endpoints
│   │   │   └── exceptions.py          # Custom exceptions
│   │   ├── gas/
│   │   ├── water/
│   │   └── auth/
│   ├── database/
│   │   ├── migrations/
│   │   └── schema.sql                 # Database schema
│   ├── payment_gateway/
│   │   ├── razorpay.py
│   │   ├── payu.py
│   │   └── gateway_interface.py
│   ├── config.py
│   ├── app.py                         # Main Flask/FastAPI app
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── pages/
│   │   │   ├── ElectricityHome.jsx
│   │   │   ├── PayBill.jsx
│   │   │   ├── ServiceTransfer.jsx
│   │   │   ├── ComplaintForm.jsx
│   │   │   └── StatusTracker.jsx
│   │   ├── components/
│   │   │   ├── ServiceRequestCard.jsx
│   │   │   ├── PaymentForm.jsx
│   │   │   └── DocumentUpload.jsx
│   │   └── services/
│   │       └── electricityAPI.js
│   └── package.json
└── docker-compose.yml
```

---

## 2. Installation & Setup

### Backend Setup (Python/Node.js)

#### A. Python (FastAPI)

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install fastapi uvicorn sqlalchemy psycopg2-binary pydantic python-jose

# Create project structure
mkdir -p backend/services/electricity
```

#### B. Node.js (Express)

```bash
# Initialize Node project
npm init -y

# Install dependencies
npm install express pg jsonwebtoken bcryptjs joi

# Create project structure
mkdir -p src/services/electricity
```

### Database Setup

```bash
# Connect to PostgreSQL
psql -U postgres

# Create database
CREATE DATABASE suvidha_electricity;

# Run schema
\c suvidha_electricity
\i Electricity_Database_Schema.sql

# Verify tables
\dt
```

### Environment Configuration

Create `.env` file:

```env
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/suvidha_electricity
DB_HOST=localhost
DB_PORT=5432
DB_USER=electricity_user
DB_PASSWORD=secure_password
DB_NAME=suvidha_electricity

# JWT
JWT_SECRET_KEY=your-secret-key-min-32-chars
JWT_ALGORITHM=HS256
JWT_EXPIRATION=900  # 15 minutes

# Payment Gateway
PAYMENT_GATEWAY=RAZORPAY
RAZORPAY_KEY_ID=your_razorpay_key
RAZORPAY_KEY_SECRET=your_razorpay_secret

# OTP Service
OTP_PROVIDER=TWILIO
TWILIO_ACCOUNT_SID=your_twilio_sid
TWILIO_AUTH_TOKEN=your_twilio_token

# Server
HOST=0.0.0.0
PORT=8000
DEBUG=False
LOG_LEVEL=INFO
```

---

## 3. Implementation Steps

### Step 1: Model Implementation

**File: `services/electricity/models.py`**

```python
from electricity_services import (
    ServiceRequest,
    ServiceStatus,
    ServiceType,
    ActorRole,
    OwnershipType,
    ErrorCode,
    PaymentDetails,
    BillInfo,
    MeterInfo
)
from datetime import datetime
from typing import List, Dict, Any

# Import models from database layer
from database.models import (
    DBServiceRequest,
    DBCustomer,
    DBMeter,
    DBBill,
    DBPayment
)

class ElectricityModels:
    """Wrapper for all electricity-related models"""
    
    @staticmethod
    def create_service_request(**kwargs):
        """Create ServiceRequest instance"""
        return ServiceRequest(**kwargs)
    
    @staticmethod
    def create_bill_info(**kwargs):
        """Create BillInfo instance"""
        return BillInfo(**kwargs)
```

### Step 2: Service Layer Implementation

**File: `services/electricity/services.py`**

```python
from electricity_services import (
    ElectricityServiceManager,
    ElectricityPayBillService,
    ElectricityServiceTransferService,
    ServiceType
)

# Initialize manager (singleton pattern)
_service_manager = None

def get_service_manager(db_service, payment_gateway):
    """Get or create singleton service manager"""
    global _service_manager
    if _service_manager is None:
        _service_manager = ElectricityServiceManager(db_service, payment_gateway)
    return _service_manager

class ElectricityServiceWrapper:
    """Wrapper for electricity services with business logic"""
    
    def __init__(self, db_service, payment_gateway):
        self.manager = get_service_manager(db_service, payment_gateway)
    
    def pay_bill(self, customer_id: str, meter_number: str, 
                 billing_period: str, amount: str, payment_method: str):
        """Handle bill payment"""
        return self.manager.pay_bill_service.create_pay_bill_request(
            meter_number, customer_id, billing_period, 
            Decimal(amount), payment_method
        )
    
    def transfer_service(self, old_customer_id: str, new_customer_id: str,
                        meter_number: str, docs: Dict, effective_date):
        """Handle service transfer"""
        return self.manager.transfer_service.create_transfer_request(
            meter_number, old_customer_id, new_customer_id,
            docs['identity'], docs['ownership'], docs['consent'],
            effective_date
        )
    
    def get_status(self, service_request_id: str):
        """Get service request status"""
        # Query from database
        pass
```

### Step 3: API Routes Implementation

**File: `services/electricity/routes.py`**

```python
from fastapi import APIRouter, Depends, HTTPException, Header
from fastapi.responses import JSONResponse
from typing import Optional
from datetime import datetime
from decimal import Decimal

from electricity_services import ServiceType, ErrorCode
from .services import ElectricityServiceWrapper
from .validators import validate_jwt_token, validate_meter_number

router = APIRouter(prefix="/api/v1/electricity", tags=["electricity"])

# Dependency injection
def get_service(db: DatabaseSession = Depends(get_db)):
    return ElectricityServiceWrapper(db, payment_gateway)

@router.post("/pay-bill")
async def pay_bill(
    request: PayBillRequest,
    authorization: str = Header(None),
    service: ElectricityServiceWrapper = Depends(get_service)
):
    """
    POST /api/v1/electricity/pay-bill
    Create and process bill payment
    """
    try:
        # Validate JWT token
        user_id = validate_jwt_token(authorization)
        
        # Validate input
        if not validate_meter_number(request.meter_number):
            return JSONResponse(
                status_code=400,
                content={
                    "success": False,
                    "error_code": ErrorCode.INVALID_DATA.value,
                    "error_message": "Invalid meter number format"
                }
            )
        
        # Create payment request
        service_request = service.pay_bill(
            customer_id=user_id,
            meter_number=request.meter_number,
            billing_period=request.billing_period,
            amount=request.amount,
            payment_method=request.payment_method
        )
        
        # Submit payment
        service_request = service.manager.pay_bill_service.submit_payment(
            service_request
        )
        
        # Process payment
        service_request = service.manager.pay_bill_service.process_payment(
            service_request
        )
        
        # Return response
        return JSONResponse(
            status_code=200 if service_request.status.value == "DELIVERED" else 400,
            content={
                "success": service_request.status.value == "DELIVERED",
                "service_request_id": service_request.service_request_id,
                "status": service_request.status.value,
                "error_code": service_request.error_code.value if service_request.error_code else None,
                "error_message": service_request.error_message,
                "receipt": service.manager.pay_bill_service.generate_receipt(
                    service_request
                ) if service_request.status.value == "DELIVERED" else None
            }
        )
    
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error_code": ErrorCode.INTERNAL_ERROR.value,
                "error_message": str(e)
            }
        )

@router.get("/meters/{meter_number}/bill-summary")
async def get_bill_summary(
    meter_number: str,
    authorization: str = Header(None),
    service: ElectricityServiceWrapper = Depends(get_service)
):
    """GET /api/v1/electricity/meters/{meter_number}/bill-summary"""
    try:
        user_id = validate_jwt_token(authorization)
        
        # Query bills from database
        bills = service.get_bills_for_meter(meter_number, user_id)
        
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "meter_number": meter_number,
                "customer_id": user_id,
                "bills": [bill.to_dict() for bill in bills],
                "total_outstanding": sum(b.outstanding_amount for b in bills)
            }
        )
    
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "error_message": str(e)}
        )

@router.post("/transfer-service")
async def transfer_service(
    request: TransferServiceRequest,
    authorization: str = Header(None),
    service: ElectricityServiceWrapper = Depends(get_service)
):
    """POST /api/v1/electricity/transfer-service"""
    try:
        user_id = validate_jwt_token(authorization)
        
        service_request = service.transfer_service(
            old_customer_id=user_id,
            new_customer_id=request.new_customer_id,
            meter_number=request.meter_number,
            docs={
                "identity": request.identity_proof,
                "ownership": request.ownership_proof,
                "consent": request.consent_document
            },
            effective_date=datetime.fromisoformat(request.effective_date)
        )
        
        return JSONResponse(
            status_code=201,
            content={
                "success": True,
                "service_request_id": service_request.service_request_id,
                "status": service_request.status.value,
                "message": "Transfer request submitted"
            }
        )
    
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "error_message": str(e)}
        )
```

### Step 4: Frontend Integration (React)

**File: `frontend/src/services/electricityAPI.js`**

```javascript
import axios from 'axios';

const API_BASE = '/api/v1/electricity';

class ElectricityAPI {
  constructor(token) {
    this.token = token;
    this.axios = axios.create({
      baseURL: API_BASE,
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      }
    });
  }

  async payBill(meterNumber, billingPeriod, amount, paymentMethod) {
    try {
      const response = await this.axios.post('/pay-bill', {
        meter_number: meterNumber,
        billing_period: billingPeriod,
        amount: amount,
        payment_method: paymentMethod
      });
      return response.data;
    } catch (error) {
      throw error.response?.data || error;
    }
  }

  async getBillSummary(meterNumber) {
    try {
      const response = await this.axios.get(
        `/meters/${meterNumber}/bill-summary`
      );
      return response.data;
    } catch (error) {
      throw error.response?.data || error;
    }
  }

  async transferService(newCustomerId, meterNumber, docs, effectiveDate) {
    try {
      const response = await this.axios.post('/transfer-service', {
        new_customer_id: newCustomerId,
        meter_number: meterNumber,
        identity_proof: docs.identity,
        ownership_proof: docs.ownership,
        consent_document: docs.consent,
        effective_date: effectiveDate
      });
      return response.data;
    } catch (error) {
      throw error.response?.data || error;
    }
  }

  async getRequestStatus(serviceRequestId) {
    try {
      const response = await this.axios.get(
        `/requests/${serviceRequestId}/status`
      );
      return response.data;
    } catch (error) {
      throw error.response?.data || error;
    }
  }
}

export default ElectricityAPI;
```

**File: `frontend/src/pages/PayBill.jsx`**

```jsx
import React, { useState, useEffect } from 'react';
import ElectricityAPI from '../services/electricityAPI';
import PaymentForm from '../components/PaymentForm';
import Receipt from '../components/Receipt';

function PayBill() {
  const [meters, setMeters] = useState([]);
  const [selectedMeter, setSelectedMeter] = useState(null);
  const [bills, setBills] = useState([]);
  const [loading, setLoading] = useState(false);
  const [paymentStatus, setPaymentStatus] = useState(null);
  const [receipt, setReceipt] = useState(null);

  const api = new ElectricityAPI(localStorage.getItem('jwt_token'));

  useEffect(() => {
    // Fetch customer meters
    fetchMeters();
  }, []);

  const fetchMeters = async () => {
    try {
      setLoading(true);
      const response = await api.axios.get('/account');
      setMeters(response.data.meters);
    } catch (error) {
      console.error('Error fetching meters:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchBills = async (meterNumber) => {
    try {
      setLoading(true);
      const response = await api.getBillSummary(meterNumber);
      setBills(response.bills);
      setSelectedMeter(meterNumber);
    } catch (error) {
      console.error('Error fetching bills:', error);
    } finally {
      setLoading(false);
    }
  };

  const handlePayment = async (amount, paymentMethod) => {
    try {
      setLoading(true);
      setPaymentStatus('processing');
      
      const response = await api.payBill(
        selectedMeter,
        new Date().toISOString().split('T')[0],
        amount,
        paymentMethod
      );

      if (response.success) {
        setPaymentStatus('success');
        setReceipt(response.receipt);
      } else {
        setPaymentStatus('failed');
        console.error('Payment failed:', response.error_message);
      }
    } catch (error) {
      setPaymentStatus('error');
      console.error('Payment error:', error);
    } finally {
      setLoading(false);
    }
  };

  if (paymentStatus === 'success' && receipt) {
    return <Receipt data={receipt} onClose={() => setReceipt(null)} />;
  }

  return (
    <div className="pay-bill-container">
      <h2>Pay Electricity Bill</h2>
      
      {/* Meter Selection */}
      <div className="meter-selection">
        <label>Select Meter:</label>
        <select onChange={(e) => fetchBills(e.target.value)}>
          <option value="">Choose a meter...</option>
          {meters.map((meter) => (
            <option key={meter.meter_id} value={meter.meter_number}>
              {meter.meter_number}
            </option>
          ))}
        </select>
      </div>

      {/* Bills List */}
      {bills.length > 0 && (
        <div className="bills-list">
          {bills.map((bill) => (
            <div key={bill.bill_id} className="bill-card">
              <p>Period: {bill.billing_period}</p>
              <p>Amount: ₹{bill.bill_amount}</p>
              <p>Status: {bill.status}</p>
            </div>
          ))}
        </div>
      )}

      {/* Payment Form */}
      {selectedMeter && (
        <PaymentForm 
          onSubmit={handlePayment}
          loading={loading}
          totalOutstanding={bills.reduce((sum, b) => sum + b.outstanding_amount, 0)}
        />
      )}
    </div>
  );
}

export default PayBill;
```

---

## 4. Database Integration

### Query Examples

```python
from sqlalchemy import create_engine, Session
from sqlalchemy.orm import sessionmaker

# Create engine
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Query customers
def get_customer(customer_id: str, db: Session):
    return db.query(DBCustomer).filter(
        DBCustomer.customer_id == customer_id
    ).first()

# Query bills
def get_bills(meter_id: str, db: Session):
    return db.query(DBBill).filter(
        DBBill.meter_id == meter_id,
        DBBill.bill_status.in_(['PENDING', 'OVERDUE'])
    ).all()

# Insert service request
def create_service_request(request: ServiceRequest, db: Session):
    db_request = DBServiceRequest(
        service_request_id=request.service_request_id,
        service_type=request.service_type.value,
        initiator_id=request.initiator_id,
        beneficiary_id=request.beneficiary_id,
        status=request.status.value,
        payload=request.payload
    )
    db.add(db_request)
    db.commit()
    return db_request
```

---

## 5. Testing

### Unit Tests

```python
# tests/test_electricity_services.py
import pytest
from decimal import Decimal
from datetime import datetime, timedelta
from electricity_services import (
    ElectricityPayBillService,
    ServiceRequest,
    ServiceStatus,
    ServiceType
)

class TestPayBillService:
    
    @pytest.fixture
    def service(self):
        return ElectricityPayBillService()
    
    def test_create_payment_request(self, service):
        request = service.create_pay_bill_request(
            meter_number="ELEC123456",
            customer_id="123456789012",
            billing_period="2026-01",
            amount=Decimal("1500.00"),
            payment_method="UPI"
        )
        
        assert request.service_type == ServiceType.ELECTRICITY_PAY_BILL
        assert request.status == ServiceStatus.DRAFT
        assert request.initiator_id == "123456789012"
        assert request.beneficiary_id == "123456789012"
    
    def test_submit_payment(self, service):
        request = service.create_pay_bill_request(
            meter_number="ELEC123456",
            customer_id="123456789012",
            billing_period="2026-01",
            amount=Decimal("1500.00"),
            payment_method="UPI"
        )
        
        request = service.submit_payment(request)
        assert request.status == ServiceStatus.SUBMITTED
    
    def test_process_payment(self, service):
        request = service.create_pay_bill_request(
            meter_number="ELEC123456",
            customer_id="123456789012",
            billing_period="2026-01",
            amount=Decimal("1500.00"),
            payment_method="UPI"
        )
        request = service.submit_payment(request)
        request = service.process_payment(request)
        
        assert request.status in [
            ServiceStatus.DELIVERED,
            ServiceStatus.FAILED
        ]

class TestServiceTransfer:
    
    @pytest.fixture
    def service(self):
        from electricity_services import ElectricityServiceTransferService
        return ElectricityServiceTransferService()
    
    def test_create_transfer_request(self, service):
        request = service.create_transfer_request(
            meter_number="ELEC123456",
            old_customer_id="123456789012",
            new_customer_id="987654321098",
            identity_proof_ref="ID_001",
            ownership_proof_ref="OWN_001",
            consent_ref="CONS_001",
            effective_date=datetime.now() + timedelta(days=30)
        )
        
        assert request.service_type == ServiceType.ELECTRICITY_SERVICE_TRANSFER
        assert request.initiator_id == "123456789012"
        assert request.beneficiary_id == "987654321098"
```

---

## 6. Deployment

### Docker Setup

**File: `docker-compose.yml`**

```yaml
version: '3.8'

services:
  postgresql:
    image: postgres:14
    environment:
      POSTGRES_USER: electricity_user
      POSTGRES_PASSWORD: secure_password
      POSTGRES_DB: suvidha_electricity
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./Electricity_Database_Schema.sql:/docker-entrypoint-initdb.d/init.sql

  backend:
    build:
      context: .
      dockerfile: Dockerfile
    environment:
      DATABASE_URL: postgresql://electricity_user:secure_password@postgresql:5432/suvidha_electricity
      JWT_SECRET_KEY: ${JWT_SECRET_KEY}
      RAZORPAY_KEY_ID: ${RAZORPAY_KEY_ID}
      RAZORPAY_KEY_SECRET: ${RAZORPAY_KEY_SECRET}
    ports:
      - "8000:8000"
    depends_on:
      - postgresql
    command: uvicorn app:app --host 0.0.0.0 --port 8000

  frontend:
    build:
      context: ./frontend
    ports:
      - "3000:3000"
    depends_on:
      - backend

volumes:
  postgres_data:
```

**File: `Dockerfile`**

```dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Deployment Commands

```bash
# Build and start
docker-compose up -d

# Run migrations
docker-compose exec backend python -m alembic upgrade head

# View logs
docker-compose logs -f backend

# Stop services
docker-compose down
```

---

## 7. Security Checklist

- [ ] All passwords encrypted in database
- [ ] JWT tokens with short expiry (15 min)
- [ ] HTTPS/TLS enforced
- [ ] CORS properly configured
- [ ] Input validation on all endpoints
- [ ] SQL injection prevention (parameterized queries)
- [ ] XSS prevention (output encoding)
- [ ] Rate limiting implemented
- [ ] Audit logs maintained
- [ ] Payment data encrypted

---

## 8. Common Issues & Troubleshooting

### Issue: Token Expired
**Solution**: Implement token refresh mechanism

### Issue: Payment Gateway Timeout
**Solution**: Implement retry logic with exponential backoff

### Issue: Slow Database Queries
**Solution**: Add indexes on frequently queried columns

### Issue: Session Not Persisting
**Solution**: Use secure httpOnly cookies with same-site attribute

---

## 9. Next Steps

1. ✅ Implement Gas Services following same pattern
2. ✅ Implement Water/Municipal Services
3. ✅ Create Admin Dashboard
4. ✅ Implement notification system
5. ✅ Add real-time status updates (WebSocket)
6. ✅ Complete KIOSK frontend
7. ✅ Performance testing & optimization
8. ✅ Security audit
9. ✅ Documentation & deployment

---

## 10. Support & Questions

For questions or issues:
- Email: smartcities.challenges@cdac.in
- Reference Framework: Service Transfer – Core Terms & Framework
- Code Repository: [Your GitHub Repo]

**Version**: 1.0  
**Last Updated**: February 4, 2026

