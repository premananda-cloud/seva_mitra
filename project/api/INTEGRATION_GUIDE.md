"""
KOISK FastAPI - Service Integration Guide
==========================================

This guide shows how to integrate the FastAPI backend with the actual
SUVIDHA 2026 service classes (Electricity, Water, Gas).
"""

# ============================================================================
# STEP 1: Import Service Managers
# ============================================================================

"""
Instead of using MockServiceManager, import the actual service classes:

from department.electricity.Electricity_Services import (
    ElectricityServiceManager,
    ElectricityPayBillService,
    ServiceStatus,
    ServiceType,
    ErrorCode
)

from department.water.Water_Services_Complete import (
    WaterServiceManager,
    WaterPayBillService,
    ServiceStatus as WaterServiceStatus,
)

from department.gas.Gas_services import (
    GasServiceManager,
    GasPayBillService,
)
"""

# ============================================================================
# STEP 2: Initialize Service Managers (Production Version)
# ============================================================================

"""
# In your koisk_api.py, replace MockServiceManager with:

import sys
import os
from decimal import Decimal

# Add project path to sys.path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'KOISK_UI-main', 'project'))

# Import actual service classes
from department.electricity.Electricity_Services import ElectricityServiceManager
from department.water.Water_Services_Complete import WaterServiceManager
from department.gas.Gas_services import GasServiceManager

# Initialize service managers
electricity_manager = ElectricityServiceManager(
    db_service=None,  # Pass your database service
    payment_gateway=None  # Pass your payment gateway
)

water_manager = WaterServiceManager(
    db_service=None,
    payment_gateway=None
)

gas_manager = GasServiceManager(
    db_service=None,
    payment_gateway=None
)
"""

# ============================================================================
# STEP 3: Update Electricity Endpoints
# ============================================================================

"""
@app.post("/api/v1/electricity/pay-bill", 
          response_model=SuccessResponse,
          tags=["Electricity"],
          summary="Pay Electricity Bill")
async def electricity_pay_bill(request: ElectricityPayBillRequest):
    \"\"\"
    Production implementation using actual service manager
    \"\"\"
    try:
        # Create payment request
        bill_request = electricity_manager.pay_bill_service.create_pay_bill_request(
            meter_number=request.meter_number,
            customer_id=request.user_id,
            billing_period=request.billing_period,
            amount=Decimal(request.amount),
            payment_method=request.payment_method
        )
        
        # Submit the request
        bill_request = electricity_manager.pay_bill_service.submit_payment(bill_request)
        
        # Process payment
        bill_request = electricity_manager.pay_bill_service.process_payment(bill_request)
        
        # Check if payment was successful
        if bill_request.status == ServiceStatus.DELIVERED:
            receipt = electricity_manager.pay_bill_service.generate_receipt(bill_request)
            return SuccessResponse(
                success=True,
                service_request_id=bill_request.service_request_id,
                status=bill_request.status.value,
                message="Payment processed successfully",
                data={
                    "receipt": receipt,
                    "amount_paid": request.amount
                }
            )
        else:
            return SuccessResponse(
                success=False,
                service_request_id=bill_request.service_request_id,
                status=bill_request.status.value,
                message=bill_request.error_message,
                data={"error_code": bill_request.error_code.value}
            )
    
    except Exception as e:
        logger.error(f"Error in electricity bill payment: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@app.post("/api/v1/electricity/transfer-service",
          response_model=SuccessResponse,
          tags=["Electricity"],
          summary="Request Service Transfer")
async def electricity_transfer_service(request: ElectricityTransferRequest):
    \"\"\"
    Production implementation for service transfer
    \"\"\"
    try:
        from datetime import datetime
        
        effective_dt = datetime.fromisoformat(request.effective_date)
        
        # Create transfer request
        transfer_request = electricity_manager.transfer_service.create_transfer_request(
            meter_number=request.meter_number,
            old_customer_id=request.old_customer_id,
            new_customer_id=request.new_customer_id,
            identity_proof_ref=request.identity_proof,
            ownership_proof_ref=request.ownership_proof,
            consent_ref=request.consent_doc,
            effective_date=effective_dt
        )
        
        # Submit transfer
        transfer_request = electricity_manager.transfer_service.submit_transfer(transfer_request)
        
        return SuccessResponse(
            success=True,
            service_request_id=transfer_request.service_request_id,
            status=transfer_request.status.value,
            message="Service transfer request submitted. Awaiting department approval."
        )
    
    except Exception as e:
        logger.error(f"Error in service transfer: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@app.get("/api/v1/electricity/requests/{request_id}",
         response_model=ServiceStatusResponse,
         tags=["Electricity"],
         summary="Get Request Status")
async def electricity_get_request_status(request_id: str, user_id: str = None):
    \"\"\"
    Get detailed status with history
    \"\"\"
    try:
        # In production, this would query your database
        # For now, assuming requests are stored in service manager
        request_data = electricity_manager.get_service_request_status(request_id)
        
        if not request_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Request {request_id} not found"
            )
        
        return ServiceStatusResponse(
            service_request_id=request_data.service_request_id,
            status=request_data.status.value,
            created_at=request_data.created_at,
            updated_at=request_data.updated_at,
            message=f"Request status: {request_data.status.value}",
            error_code=request_data.error_code.value if request_data.error_code else None,
            error_message=request_data.error_message
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving request status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
"""

# ============================================================================
# STEP 4: Update Water Endpoints
# ============================================================================

"""
@app.post("/api/v1/water/pay-bill",
          response_model=SuccessResponse,
          tags=["Water"],
          summary="Pay Water Bill")
async def water_pay_bill(request: WaterPayBillRequest):
    \"\"\"
    Production implementation for water bill payment
    \"\"\"
    try:
        bill_request = water_manager.pay_bill_service.create_pay_bill_request(
            consumer_number=request.consumer_number,
            customer_id=request.user_id,
            billing_period=request.billing_period,
            amount=Decimal(request.amount),
            payment_method=request.payment_method
        )
        
        bill_request = water_manager.pay_bill_service.submit_payment(bill_request)
        bill_request = water_manager.pay_bill_service.process_payment(bill_request)
        
        return SuccessResponse(
            success=bill_request.status == WaterServiceStatus.DELIVERED,
            service_request_id=bill_request.service_request_id,
            status=bill_request.status.value,
            message="Water bill payment processed successfully"
        )
    
    except Exception as e:
        logger.error(f"Error in water bill payment: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@app.post("/api/v1/water/leak-complaint",
          response_model=SuccessResponse,
          tags=["Water"],
          summary="Report Water Leak")
async def water_leak_complaint(request: WaterLeakComplaintRequest):
    \"\"\"
    Production implementation for water leak complaints
    \"\"\"
    try:
        complaint_request = water_manager.leak_complaint_service.create_complaint(
            consumer_number=request.consumer_number,
            consumer_id=request.consumer_id,
            complaint_type=request.complaint_type,
            location=request.location,
            severity=request.severity,
            description=request.description
        )
        
        complaint_request = water_manager.leak_complaint_service.submit_complaint(complaint_request)
        
        return SuccessResponse(
            success=True,
            service_request_id=complaint_request.service_request_id,
            status=complaint_request.status.value,
            message="Water leak complaint submitted. Our team will attend shortly."
        )
    
    except Exception as e:
        logger.error(f"Error in water leak complaint: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
"""

# ============================================================================
# STEP 5: Database Integration
# ============================================================================

"""
If your service classes need database integration:

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./test.db")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create tables
from department.database.models import Base
Base.metadata.create_all(bind=engine)

# Pass database session to service managers
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# In endpoints:
@app.post("/api/v1/electricity/pay-bill")
async def electricity_pay_bill(request: ElectricityPayBillRequest, db: Session = Depends(get_db)):
    # Now you can pass db to service manager
    bill_request = electricity_manager.pay_bill_service.create_pay_bill_request(
        meter_number=request.meter_number,
        customer_id=request.user_id,
        billing_period=request.billing_period,
        amount=Decimal(request.amount),
        payment_method=request.payment_method,
        db=db  # Pass database session
    )
    ...
"""

# ============================================================================
# STEP 6: Payment Gateway Integration
# ============================================================================

"""
If your service classes need payment gateway integration:

class PaymentGateway:
    def __init__(self, api_key: str, base_url: str):
        self.api_key = api_key
        self.base_url = base_url
        self.timeout = 30
    
    async def process_payment(self, amount: Decimal, payment_method: str, 
                             reference_id: str) -> Dict[str, Any]:
        # Call actual payment gateway API
        import httpx
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/process",
                json={
                    "amount": float(amount),
                    "method": payment_method,
                    "reference": reference_id
                },
                headers={"Authorization": f"Bearer {self.api_key}"},
                timeout=self.timeout
            )
            
            return response.json()
    
    async def verify_payment(self, transaction_id: str) -> Dict[str, Any]:
        # Verify payment status
        import httpx
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/verify/{transaction_id}",
                headers={"Authorization": f"Bearer {self.api_key}"}
            )
            
            return response.json()

# Initialize payment gateway
payment_gateway = PaymentGateway(
    api_key=os.getenv("PAYMENT_GATEWAY_API_KEY"),
    base_url=os.getenv("PAYMENT_GATEWAY_URL")
)

# Pass to service managers
electricity_manager = ElectricityServiceManager(
    db_service=db,
    payment_gateway=payment_gateway
)
"""

# ============================================================================
# STEP 7: Error Handling & Validation
# ============================================================================

"""
Handle service-specific errors:

from fastapi import HTTPException, status

@app.exception_handler(ValueError)
async def value_error_exception_handler(request, exc):
    return ErrorResponse(
        success=False,
        error_code="INVALID_DATA",
        error_message=str(exc)
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    logger.error(f"Unhandled exception: {str(exc)}")
    return ErrorResponse(
        success=False,
        error_code="INTERNAL_ERROR",
        error_message="An internal server error occurred"
    )
"""

# ============================================================================
# STEP 8: Testing with Actual Services
# ============================================================================

"""
Test your integration:

import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_electricity_pay_bill():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.post(
            "/api/v1/electricity/pay-bill",
            json={
                "user_id": "CUST123456",
                "meter_number": "ELEC123456",
                "billing_period": "2026-01",
                "amount": "1500.00",
                "payment_method": "UPI"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        assert "service_request_id" in data

Run tests:
    pytest tests/
"""

# ============================================================================
# Summary
# ============================================================================

"""
To integrate with actual services:

1. Import the service classes from department modules
2. Initialize service managers with database and payment gateway
3. Replace mock implementations with actual service calls
4. Add proper error handling for service-specific exceptions
5. Implement database session management
6. Configure payment gateway integration
7. Test all endpoints thoroughly

Key Files to Modify:
- koisk_api.py: Replace MockServiceManager with actual service managers
- requirements.txt: Add any additional dependencies
- .env: Configure database and payment gateway URLs
"""
