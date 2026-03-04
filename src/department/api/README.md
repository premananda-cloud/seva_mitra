# KOISK FastAPI Backend

A comprehensive FastAPI backend for the KOISK UI (SUVIDHA 2026), providing RESTful APIs for utility services including Electricity, Water, and Gas.

## 📋 Table of Contents

- [Features](#features)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Running the API](#running-the-api)
- [API Endpoints](#api-endpoints)
- [Request/Response Examples](#requestresponse-examples)
- [Database Integration](#database-integration)
- [CORS Configuration](#cors-configuration)
- [Deployment](#deployment)
- [Troubleshooting](#troubleshooting)

## ✨ Features

- **Multi-Service Support**: Electricity, Water, and Gas utilities
- **RESTful API Design**: Clean and intuitive endpoints
- **Comprehensive Documentation**: Auto-generated API docs with Swagger UI
- **Type Safety**: Full Pydantic model validation
- **Error Handling**: Proper HTTP error codes and messages
- **CORS Enabled**: Ready for frontend integration
- **Request Tracking**: Service request IDs for tracking status
- **Service State Management**: Track requests through their lifecycle
- **Async Support**: Built with FastAPI's async capabilities

## 📦 Prerequisites

- Python 3.8+
- pip (Python package manager)
- Virtual environment (recommended)

## 🚀 Installation

### 1. Clone or Copy the Project

```bash
cd your_project_directory
```

### 2. Create Virtual Environment

```bash
python -m venv venv

# On Windows
venv\Scripts\activate

# On macOS/Linux
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Verify Installation

```bash
pip list
```

## ⚙️ Configuration

### Environment Variables

Create a `.env` file in the project root:

```env
# FastAPI Configuration
API_HOST=0.0.0.0
API_PORT=8000
API_DEBUG=True

# CORS Configuration
CORS_ORIGINS=["http://localhost:3000", "http://localhost:5173"]

# Database Configuration
DATABASE_URL=postgresql://user:password@localhost:5432/koisk_db

# Payment Gateway
PAYMENT_GATEWAY_API_KEY=your_api_key
PAYMENT_GATEWAY_URL=https://payment-gateway.example.com

# Logging
LOG_LEVEL=INFO
```

### Load Environment Variables

Update `koisk_api.py` to load environment variables:

```python
from dotenv import load_dotenv
import os

load_dotenv()

API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", 8000))
```

## 🏃 Running the API

### Development Mode

```bash
python koisk_api.py
```

Or using uvicorn directly:

```bash
uvicorn koisk_api:app --reload --host 0.0.0.0 --port 8000
```

### Production Mode

```bash
uvicorn koisk_api:app --host 0.0.0.0 --port 8000 --workers 4
```

### Access the API

- **API Documentation**: http://localhost:8000/docs
- **Alternative Docs**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

## 📚 API Endpoints

### Health & Status

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | API status and available endpoints |
| GET | `/health` | Health check of all services |

### Electricity Service

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/electricity/pay-bill` | Submit bill payment |
| POST | `/api/v1/electricity/transfer-service` | Request service transfer |
| POST | `/api/v1/electricity/meter-change` | Request meter change |
| POST | `/api/v1/electricity/new-connection` | Request new connection |
| GET | `/api/v1/electricity/requests/{request_id}` | Get request status |
| GET | `/api/v1/electricity/user/{user_id}/requests` | List user requests |

### Water Service

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/water/pay-bill` | Submit bill payment |
| POST | `/api/v1/water/new-connection` | Request new connection |
| POST | `/api/v1/water/leak-complaint` | Report water leak |
| GET | `/api/v1/water/requests/{request_id}` | Get request status |

### Gas Service

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/gas/pay-bill` | Submit bill payment |
| POST | `/api/v1/gas/new-connection` | Request new connection |
| GET | `/api/v1/gas/requests/{request_id}` | Get request status |

## 📝 Request/Response Examples

### Electricity - Pay Bill

**Request:**
```bash
curl -X POST "http://localhost:8000/api/v1/electricity/pay-bill" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "CUST123456",
    "meter_number": "ELEC123456",
    "billing_period": "2026-01",
    "amount": "1500.00",
    "payment_method": "UPI"
  }'
```

**Response:**
```json
{
  "success": true,
  "service_request_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "SUBMITTED",
  "message": "Bill payment request submitted successfully",
  "data": {
    "payment_method": "UPI"
  }
}
```

### Electricity - Transfer Service

**Request:**
```bash
curl -X POST "http://localhost:8000/api/v1/electricity/transfer-service" \
  -H "Content-Type: application/json" \
  -d '{
    "old_customer_id": "OLD_CUST123",
    "new_customer_id": "NEW_CUST456",
    "meter_number": "ELEC123456",
    "identity_proof": "ID_REF_001",
    "ownership_proof": "OWN_REF_001",
    "consent_doc": "CONS_REF_001",
    "effective_date": "2026-03-01"
  }'
```

**Response:**
```json
{
  "success": true,
  "service_request_id": "550e8400-e29b-41d4-a716-446655440001",
  "status": "SUBMITTED",
  "message": "Service transfer request submitted. Awaiting department approval."
}
```

### Water - Pay Bill

**Request:**
```bash
curl -X POST "http://localhost:8000/api/v1/water/pay-bill" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "CONS123456",
    "consumer_number": "WATER123456",
    "billing_period": "2026-01",
    "amount": "800.00",
    "payment_method": "UPI"
  }'
```

**Response:**
```json
{
  "success": true,
  "service_request_id": "550e8400-e29b-41d4-a716-446655440002",
  "status": "SUBMITTED",
  "message": "Water bill payment request submitted successfully"
}
```

### Water - Report Leak

**Request:**
```bash
curl -X POST "http://localhost:8000/api/v1/water/leak-complaint" \
  -H "Content-Type: application/json" \
  -d '{
    "consumer_id": "CONS123456",
    "consumer_number": "WATER123456",
    "complaint_type": "Pipeline leak",
    "location": "Main meter area",
    "severity": "High",
    "description": "Water leaking from main pipeline near meter"
  }'
```

**Response:**
```json
{
  "success": true,
  "service_request_id": "550e8400-e29b-41d4-a716-446655440003",
  "status": "SUBMITTED",
  "message": "Water leak complaint submitted. Our team will attend shortly."
}
```

### Get Request Status

**Request:**
```bash
curl -X GET "http://localhost:8000/api/v1/electricity/requests/550e8400-e29b-41d4-a716-446655440000"
```

**Response:**
```json
{
  "service_request_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "SUBMITTED",
  "message": null,
  "created_at": "2026-02-10T10:30:00",
  "updated_at": "2026-02-10T10:30:00",
  "error_code": null,
  "error_message": null
}
```

## 🗄️ Database Integration

### Integrating with Actual Service Classes

Update `koisk_api.py` to use the actual service managers:

```python
# Instead of MockServiceManager, use:
from sys import path
path.append('path/to/project')

from department.electricity.Electricity_Services import ElectricityServiceManager
from department.water.Water_Services_Complete import WaterServiceManager
from department.gas.Gas_services import GasServiceManager

# Initialize actual service managers
electricity_manager = ElectricityServiceManager()
water_manager = WaterServiceManager()
gas_manager = GasServiceManager()
```

### Example Implementation

```python
@app.post("/api/v1/electricity/pay-bill")
async def electricity_pay_bill(request: ElectricityPayBillRequest):
    try:
        # Use actual service manager
        bill_request = electricity_manager.pay_bill_service.create_pay_bill_request(
            meter_number=request.meter_number,
            customer_id=request.user_id,
            billing_period=request.billing_period,
            amount=Decimal(request.amount),
            payment_method=request.payment_method
        )
        
        bill_request = electricity_manager.pay_bill_service.submit_payment(bill_request)
        bill_request = electricity_manager.pay_bill_service.process_payment(bill_request)
        
        return SuccessResponse(
            success=bill_request.status == ServiceStatus.DELIVERED,
            service_request_id=bill_request.service_request_id,
            status=bill_request.status.value,
            message="Payment processed successfully"
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
```

## 🌐 CORS Configuration

### Update CORS Origins

Edit the CORS middleware in `koisk_api.py`:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",      # React dev server
        "http://localhost:5173",      # Vite dev server
        "http://localhost:5174",      # Alternative
        "https://yourdomain.com",     # Production domain
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### For Development (Allow All Origins)

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # ⚠️ Only for development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## 🚀 Deployment

### Using Gunicorn (Production)

```bash
pip install gunicorn

gunicorn koisk_api:app -w 4 -b 0.0.0.0:8000 -k uvicorn.workers.UvicornWorker
```

### Using Docker

Create `Dockerfile`:

```dockerfile
FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "koisk_api:app", "--host", "0.0.0.0", "--port", "8000"]
```

Build and run:

```bash
docker build -t koisk-api .
docker run -p 8000:8000 koisk-api
```

### Using Docker Compose

Create `docker-compose.yml`:

```yaml
version: '3.8'

services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - API_HOST=0.0.0.0
      - API_PORT=8000
      - API_DEBUG=False
    volumes:
      - ./:/app
```

Run:

```bash
docker-compose up
```

## 🐛 Troubleshooting

### Port Already in Use

```bash
# Find process using port 8000
lsof -i :8000

# Kill the process
kill -9 <PID>

# Or use a different port
uvicorn koisk_api:app --port 8001
```

### CORS Errors

Check your CORS configuration matches your frontend URL exactly:

```python
# Enable all origins temporarily for debugging
allow_origins=["*"]
```

### Import Errors

Ensure your PYTHONPATH includes the project directory:

```bash
export PYTHONPATH="${PYTHONPATH}:/path/to/project"
python koisk_api.py
```

### Database Connection Errors

Verify database credentials in `.env`:

```bash
# Test connection
python -c "from sqlalchemy import create_engine; engine = create_engine(os.getenv('DATABASE_URL')); print(engine.execute('SELECT 1'))"
```

## 📖 Frontend Integration

### React Example

```javascript
// Example using fetch API
async function payBill() {
  const response = await fetch('http://localhost:8000/api/v1/electricity/pay-bill', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      user_id: 'CUST123456',
      meter_number: 'ELEC123456',
      billing_period: '2026-01',
      amount: '1500.00',
      payment_method: 'UPI'
    })
  });
  
  const data = await response.json();
  console.log('Request ID:', data.service_request_id);
  console.log('Status:', data.status);
}
```

### Using Axios

```javascript
import axios from 'axios';

const API_BASE = 'http://localhost:8000';

const payBill = async (billData) => {
  try {
    const response = await axios.post(
      `${API_BASE}/api/v1/electricity/pay-bill`,
      billData
    );
    return response.data;
  } catch (error) {
    console.error('Payment failed:', error.response.data);
  }
};
```

## 📞 Support

For issues or questions:
1. Check the troubleshooting section
2. Review API documentation at `/docs`
3. Check application logs
4. Verify configuration in `.env`

## 📄 License

This project is part of SUVIDHA 2026 framework.

---

**Happy API development!** 🚀
