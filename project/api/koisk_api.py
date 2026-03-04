"""
KOISK FastAPI Backend
=====================
FastAPI application connecting to SUVIDHA 2026 service framework
Supports Electricity, Water, and Gas utility services

Author: KOISK Team
Version: 1.0
"""

from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from decimal import Decimal
import logging
import os

# Import the existing service modules (adjust paths as needed)
# from department.electricity.Electricity_Services import (
#     ElectricityServiceManager, ServiceStatus, ServiceType, ErrorCode
# )

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================================================================
# 1. FASTAPI APPLICATION SETUP
# ============================================================================

app = FastAPI(
    title="KOISK Utility Services API",
    description="FastAPI backend for SUVIDHA 2026 Utility Services (Electricity, Water, Gas)",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# ============================================================================
# 2. CORS CONFIGURATION
# ============================================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your UI domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================================
# 3. PYDANTIC MODELS - COMMON
# ============================================================================

class ServiceStatusResponse(BaseModel):
    """Generic service status response"""
    service_request_id: str
    status: str
    message: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    
    class Config:
        schema_extra = {
            "example": {
                "service_request_id": "uuid-12345",
                "status": "SUBMITTED",
                "message": "Request submitted successfully",
                "created_at": "2026-02-10T10:30:00",
                "updated_at": "2026-02-10T10:30:00",
                "error_code": None,
                "error_message": None
            }
        }


class SuccessResponse(BaseModel):
    """Generic success response"""
    success: bool
    service_request_id: str
    status: str
    message: Optional[str] = None
    data: Optional[Dict[str, Any]] = None


class ErrorResponse(BaseModel):
    """Generic error response"""
    success: bool = False
    error_code: str
    error_message: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# ============================================================================
# 4. PYDANTIC MODELS - ELECTRICITY
# ============================================================================

class ElectricityPayBillRequest(BaseModel):
    """Request model for electricity bill payment"""
    user_id: str = Field(..., description="Customer ID")
    meter_number: str = Field(..., description="Electricity meter number")
    billing_period: str = Field(..., description="Billing period (YYYY-MM)")
    amount: str = Field(..., description="Payment amount")
    payment_method: str = Field(..., description="UPI, Card, NetBanking, etc")
    
    class Config:
        schema_extra = {
            "example": {
                "user_id": "CUST123456",
                "meter_number": "ELEC123456",
                "billing_period": "2026-01",
                "amount": "1500.00",
                "payment_method": "UPI"
            }
        }


class ElectricityTransferRequest(BaseModel):
    """Request model for electricity service transfer"""
    old_customer_id: str = Field(..., description="Current customer ID")
    new_customer_id: str = Field(..., description="New customer ID")
    meter_number: str = Field(..., description="Meter number")
    identity_proof: str = Field(..., description="Identity proof reference")
    ownership_proof: str = Field(..., description="Ownership proof reference")
    consent_doc: str = Field(..., description="Consent document reference")
    effective_date: str = Field(..., description="Transfer effective date (YYYY-MM-DD)")
    
    class Config:
        schema_extra = {
            "example": {
                "old_customer_id": "OLD_CUST123",
                "new_customer_id": "NEW_CUST456",
                "meter_number": "ELEC123456",
                "identity_proof": "ID_REF_001",
                "ownership_proof": "OWN_REF_001",
                "consent_doc": "CONS_REF_001",
                "effective_date": "2026-03-01"
            }
        }


class ElectricityMeterChangeRequest(BaseModel):
    """Request model for meter change"""
    user_id: str = Field(..., description="Customer ID")
    meter_number: str = Field(..., description="Current meter number")
    reason: str = Field(..., description="Reason for meter change")
    new_meter_number: Optional[str] = Field(None, description="New meter number if available")
    
    class Config:
        schema_extra = {
            "example": {
                "user_id": "CUST123456",
                "meter_number": "ELEC123456",
                "reason": "Meter malfunction",
                "new_meter_number": None
            }
        }


class ElectricityConnectionRequest(BaseModel):
    """Request model for new electricity connection"""
    customer_name: str = Field(..., description="Customer name")
    customer_id: str = Field(..., description="Customer ID")
    address: str = Field(..., description="Service address")
    load_requirement: str = Field(..., description="Load requirement in kW")
    identity_proof: str = Field(..., description="Identity proof reference")
    address_proof: str = Field(..., description="Address proof reference")
    
    class Config:
        schema_extra = {
            "example": {
                "customer_name": "John Doe",
                "customer_id": "CUST123456",
                "address": "123 Main Street, City",
                "load_requirement": "5",
                "identity_proof": "AADHAR_12345",
                "address_proof": "RENT_AGREEMENT_001"
            }
        }


# ============================================================================
# 5. PYDANTIC MODELS - WATER
# ============================================================================

class WaterPayBillRequest(BaseModel):
    """Request model for water bill payment"""
    user_id: str = Field(..., description="Consumer ID")
    consumer_number: str = Field(..., description="Water consumer number")
    billing_period: str = Field(..., description="Billing period (YYYY-MM)")
    amount: str = Field(..., description="Payment amount")
    payment_method: str = Field(..., description="UPI, Card, NetBanking, etc")
    
    class Config:
        schema_extra = {
            "example": {
                "user_id": "CONS123456",
                "consumer_number": "WATER123456",
                "billing_period": "2026-01",
                "amount": "800.00",
                "payment_method": "UPI"
            }
        }


class WaterConnectionRequest(BaseModel):
    """Request model for water connection"""
    applicant_name: str = Field(..., description="Applicant name")
    applicant_id: str = Field(..., description="Applicant ID")
    address: str = Field(..., description="Property address")
    property_type: str = Field(..., description="Residential/Commercial")
    identity_proof: str = Field(..., description="Identity proof reference")
    address_proof: str = Field(..., description="Address proof reference")
    
    class Config:
        schema_extra = {
            "example": {
                "applicant_name": "Jane Smith",
                "applicant_id": "APPL123456",
                "address": "456 Oak Avenue, City",
                "property_type": "Residential",
                "identity_proof": "AADHAR_67890",
                "address_proof": "OWNERSHIP_PROOF_002"
            }
        }


class WaterLeakComplaintRequest(BaseModel):
    """Request model for water leak complaint"""
    consumer_id: str = Field(..., description="Consumer ID")
    consumer_number: str = Field(..., description="Water consumer number")
    complaint_type: str = Field(..., description="Leak type")
    location: str = Field(..., description="Location of leak")
    severity: str = Field(..., description="Low/Medium/High")
    description: Optional[str] = Field(None, description="Detailed description")
    
    class Config:
        schema_extra = {
            "example": {
                "consumer_id": "CONS123456",
                "consumer_number": "WATER123456",
                "complaint_type": "Pipeline leak",
                "location": "Main meter area",
                "severity": "High",
                "description": "Water leaking from main pipeline near meter"
            }
        }


# ============================================================================
# 6. PYDANTIC MODELS - GAS
# ============================================================================

class GasPayBillRequest(BaseModel):
    """Request model for gas bill payment"""
    user_id: str = Field(..., description="Customer ID")
    consumer_number: str = Field(..., description="Gas consumer number")
    billing_period: str = Field(..., description="Billing period (YYYY-MM)")
    amount: str = Field(..., description="Payment amount")
    payment_method: str = Field(..., description="UPI, Card, NetBanking, etc")
    
    class Config:
        schema_extra = {
            "example": {
                "user_id": "CUST123456",
                "consumer_number": "GAS123456",
                "billing_period": "2026-01",
                "amount": "1200.00",
                "payment_method": "UPI"
            }
        }


class GasConnectionRequest(BaseModel):
    """Request model for gas connection"""
    applicant_name: str = Field(..., description="Applicant name")
    applicant_id: str = Field(..., description="Applicant ID")
    address: str = Field(..., description="Property address")
    identity_proof: str = Field(..., description="Identity proof reference")
    address_proof: str = Field(..., description="Address proof reference")
    
    class Config:
        schema_extra = {
            "example": {
                "applicant_name": "Robert Johnson",
                "applicant_id": "APPL789012",
                "address": "789 Pine Road, City",
                "identity_proof": "AADHAR_11111",
                "address_proof": "OWNERSHIP_PROOF_003"
            }
        }


# ============================================================================
# 7. SERVICE MANAGER (Mock Implementation)
# ============================================================================

class MockServiceManager:
    """
    Mock service manager - Replace with actual implementation
    In production, integrate with ElectricityServiceManager, etc.
    """
    
    def __init__(self):
        self.requests_store: Dict[str, Dict[str, Any]] = {}
    
    def create_request(self, service_type: str, **kwargs) -> Dict[str, Any]:
        """Create a new service request"""
        from uuid import uuid4
        request_id = str(uuid4())
        
        request_data = {
            "service_request_id": request_id,
            "service_type": service_type,
            "status": "SUBMITTED",
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
            "payload": kwargs,
            "error_code": None,
            "error_message": None
        }
        
        self.requests_store[request_id] = request_data
        logger.info(f"Created request: {request_id} for service: {service_type}")
        
        return request_data
    
    def get_request_status(self, request_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a service request"""
        return self.requests_store.get(request_id)
    
    def list_user_requests(self, user_id: str, service_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """List requests for a user"""
        requests = [
            req for req in self.requests_store.values()
            if req["payload"].get("user_id") == user_id or 
               req["payload"].get("customer_id") == user_id or
               req["payload"].get("applicant_id") == user_id or
               req["payload"].get("consumer_id") == user_id
        ]
        
        if service_type:
            requests = [r for r in requests if r["service_type"] == service_type]
        
        return requests


# Global service manager instance
service_manager = MockServiceManager()

# ============================================================================
# 8. HEALTH CHECK ENDPOINT
# ============================================================================

@app.get("/", tags=["Health"])
async def root():
    """Root endpoint - API status"""
    return {
        "message": "KOISK Utility Services API",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "docs": "/docs",
            "health": "/health",
            "electricity": "/api/v1/electricity",
            "water": "/api/v1/water",
            "gas": "/api/v1/gas"
        }
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "services": {
            "electricity": "operational",
            "water": "operational",
            "gas": "operational"
        }
    }


# ============================================================================
# 9. ELECTRICITY ENDPOINTS
# ============================================================================

@app.post("/api/v1/electricity/pay-bill", 
          response_model=SuccessResponse,
          tags=["Electricity"],
          summary="Pay Electricity Bill")
async def electricity_pay_bill(request: ElectricityPayBillRequest):
    """
    Submit an electricity bill payment request
    
    - **user_id**: Customer ID
    - **meter_number**: Electricity meter number
    - **billing_period**: Billing period (YYYY-MM format)
    - **amount**: Payment amount
    - **payment_method**: UPI, Card, NetBanking, etc
    """
    try:
        result = service_manager.create_request(
            "ELECTRICITY_PAY_BILL",
            user_id=request.user_id,
            meter_number=request.meter_number,
            billing_period=request.billing_period,
            amount=request.amount,
            payment_method=request.payment_method
        )
        
        return SuccessResponse(
            success=True,
            service_request_id=result["service_request_id"],
            status=result["status"],
            message="Bill payment request submitted successfully",
            data={"payment_method": request.payment_method}
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
    """
    Request electricity service transfer from old customer to new customer
    
    - **old_customer_id**: Current customer ID
    - **new_customer_id**: New customer ID
    - **meter_number**: Electricity meter number
    - **identity_proof**: Identity proof reference
    - **ownership_proof**: Ownership proof reference
    - **consent_doc**: Consent document reference
    - **effective_date**: Transfer effective date
    """
    try:
        result = service_manager.create_request(
            "ELECTRICITY_SERVICE_TRANSFER",
            old_customer_id=request.old_customer_id,
            new_customer_id=request.new_customer_id,
            meter_number=request.meter_number,
            identity_proof=request.identity_proof,
            ownership_proof=request.ownership_proof,
            consent_doc=request.consent_doc,
            effective_date=request.effective_date
        )
        
        return SuccessResponse(
            success=True,
            service_request_id=result["service_request_id"],
            status=result["status"],
            message="Service transfer request submitted. Awaiting department approval."
        )
    except Exception as e:
        logger.error(f"Error in service transfer: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@app.post("/api/v1/electricity/meter-change",
          response_model=SuccessResponse,
          tags=["Electricity"],
          summary="Request Meter Change")
async def electricity_meter_change(request: ElectricityMeterChangeRequest):
    """
    Request electricity meter replacement/change
    
    - **user_id**: Customer ID
    - **meter_number**: Current meter number
    - **reason**: Reason for meter change
    - **new_meter_number**: New meter number (optional)
    """
    try:
        result = service_manager.create_request(
            "ELECTRICITY_METER_CHANGE",
            user_id=request.user_id,
            meter_number=request.meter_number,
            reason=request.reason,
            new_meter_number=request.new_meter_number
        )
        
        return SuccessResponse(
            success=True,
            service_request_id=result["service_request_id"],
            status=result["status"],
            message="Meter change request submitted"
        )
    except Exception as e:
        logger.error(f"Error in meter change: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@app.post("/api/v1/electricity/new-connection",
          response_model=SuccessResponse,
          tags=["Electricity"],
          summary="Request New Connection")
async def electricity_new_connection(request: ElectricityConnectionRequest):
    """
    Request a new electricity connection
    
    - **customer_name**: Customer name
    - **customer_id**: Customer ID
    - **address**: Service address
    - **load_requirement**: Load requirement in kW
    - **identity_proof**: Identity proof reference
    - **address_proof**: Address proof reference
    """
    try:
        result = service_manager.create_request(
            "ELECTRICITY_CONNECTION_REQUEST",
            customer_name=request.customer_name,
            customer_id=request.customer_id,
            address=request.address,
            load_requirement=request.load_requirement,
            identity_proof=request.identity_proof,
            address_proof=request.address_proof
        )
        
        return SuccessResponse(
            success=True,
            service_request_id=result["service_request_id"],
            status=result["status"],
            message="Connection request submitted"
        )
    except Exception as e:
        logger.error(f"Error in connection request: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@app.get("/api/v1/electricity/requests/{request_id}",
         response_model=ServiceStatusResponse,
         tags=["Electricity"],
         summary="Get Request Status")
async def electricity_get_request_status(request_id: str):
    """Get status of an electricity service request"""
    try:
        request_data = service_manager.get_request_status(request_id)
        
        if not request_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Request {request_id} not found"
            )
        
        return ServiceStatusResponse(
            service_request_id=request_data["service_request_id"],
            status=request_data["status"],
            created_at=datetime.fromisoformat(request_data["created_at"]),
            updated_at=datetime.fromisoformat(request_data["updated_at"]),
            error_code=request_data.get("error_code"),
            error_message=request_data.get("error_message")
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving request status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@app.get("/api/v1/electricity/user/{user_id}/requests",
         tags=["Electricity"],
         summary="List User Requests")
async def electricity_list_user_requests(user_id: str):
    """Get all electricity service requests for a user"""
    try:
        requests = service_manager.list_user_requests(user_id, "ELECTRICITY_PAY_BILL")
        return {
            "user_id": user_id,
            "request_count": len(requests),
            "requests": requests
        }
    except Exception as e:
        logger.error(f"Error listing user requests: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


# ============================================================================
# 10. WATER ENDPOINTS
# ============================================================================

@app.post("/api/v1/water/pay-bill",
          response_model=SuccessResponse,
          tags=["Water"],
          summary="Pay Water Bill")
async def water_pay_bill(request: WaterPayBillRequest):
    """
    Submit a water bill payment request
    
    - **user_id**: Consumer ID
    - **consumer_number**: Water consumer number
    - **billing_period**: Billing period (YYYY-MM format)
    - **amount**: Payment amount
    - **payment_method**: UPI, Card, NetBanking, etc
    """
    try:
        result = service_manager.create_request(
            "WATER_PAY_BILL",
            user_id=request.user_id,
            consumer_number=request.consumer_number,
            billing_period=request.billing_period,
            amount=request.amount,
            payment_method=request.payment_method
        )
        
        return SuccessResponse(
            success=True,
            service_request_id=result["service_request_id"],
            status=result["status"],
            message="Water bill payment request submitted successfully"
        )
    except Exception as e:
        logger.error(f"Error in water bill payment: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@app.post("/api/v1/water/new-connection",
          response_model=SuccessResponse,
          tags=["Water"],
          summary="Request New Connection")
async def water_new_connection(request: WaterConnectionRequest):
    """
    Request a new water connection
    
    - **applicant_name**: Applicant name
    - **applicant_id**: Applicant ID
    - **address**: Property address
    - **property_type**: Residential/Commercial
    - **identity_proof**: Identity proof reference
    - **address_proof**: Address proof reference
    """
    try:
        result = service_manager.create_request(
            "WATER_CONNECTION_REQUEST",
            applicant_name=request.applicant_name,
            applicant_id=request.applicant_id,
            address=request.address,
            property_type=request.property_type,
            identity_proof=request.identity_proof,
            address_proof=request.address_proof
        )
        
        return SuccessResponse(
            success=True,
            service_request_id=result["service_request_id"],
            status=result["status"],
            message="Water connection request submitted"
        )
    except Exception as e:
        logger.error(f"Error in water connection request: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@app.post("/api/v1/water/leak-complaint",
          response_model=SuccessResponse,
          tags=["Water"],
          summary="Report Water Leak")
async def water_leak_complaint(request: WaterLeakComplaintRequest):
    """
    Report a water leak or pipe break
    
    - **consumer_id**: Consumer ID
    - **consumer_number**: Water consumer number
    - **complaint_type**: Type of leak
    - **location**: Location of leak
    - **severity**: Low/Medium/High
    - **description**: Detailed description (optional)
    """
    try:
        result = service_manager.create_request(
            "WATER_LEAK_COMPLAINT",
            consumer_id=request.consumer_id,
            consumer_number=request.consumer_number,
            complaint_type=request.complaint_type,
            location=request.location,
            severity=request.severity,
            description=request.description
        )
        
        return SuccessResponse(
            success=True,
            service_request_id=result["service_request_id"],
            status=result["status"],
            message="Water leak complaint submitted. Our team will attend shortly."
        )
    except Exception as e:
        logger.error(f"Error in water leak complaint: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@app.get("/api/v1/water/requests/{request_id}",
         response_model=ServiceStatusResponse,
         tags=["Water"],
         summary="Get Request Status")
async def water_get_request_status(request_id: str):
    """Get status of a water service request"""
    try:
        request_data = service_manager.get_request_status(request_id)
        
        if not request_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Request {request_id} not found"
            )
        
        return ServiceStatusResponse(
            service_request_id=request_data["service_request_id"],
            status=request_data["status"],
            created_at=datetime.fromisoformat(request_data["created_at"]),
            updated_at=datetime.fromisoformat(request_data["updated_at"]),
            error_code=request_data.get("error_code"),
            error_message=request_data.get("error_message")
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving request status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


# ============================================================================
# 11. GAS ENDPOINTS
# ============================================================================

@app.post("/api/v1/gas/pay-bill",
          response_model=SuccessResponse,
          tags=["Gas"],
          summary="Pay Gas Bill")
async def gas_pay_bill(request: GasPayBillRequest):
    """
    Submit a gas bill payment request
    
    - **user_id**: Customer ID
    - **consumer_number**: Gas consumer number
    - **billing_period**: Billing period (YYYY-MM format)
    - **amount**: Payment amount
    - **payment_method**: UPI, Card, NetBanking, etc
    """
    try:
        result = service_manager.create_request(
            "GAS_PAY_BILL",
            user_id=request.user_id,
            consumer_number=request.consumer_number,
            billing_period=request.billing_period,
            amount=request.amount,
            payment_method=request.payment_method
        )
        
        return SuccessResponse(
            success=True,
            service_request_id=result["service_request_id"],
            status=result["status"],
            message="Gas bill payment request submitted successfully"
        )
    except Exception as e:
        logger.error(f"Error in gas bill payment: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@app.post("/api/v1/gas/new-connection",
          response_model=SuccessResponse,
          tags=["Gas"],
          summary="Request New Connection")
async def gas_new_connection(request: GasConnectionRequest):
    """
    Request a new gas connection
    
    - **applicant_name**: Applicant name
    - **applicant_id**: Applicant ID
    - **address**: Property address
    - **identity_proof**: Identity proof reference
    - **address_proof**: Address proof reference
    """
    try:
        result = service_manager.create_request(
            "GAS_CONNECTION_REQUEST",
            applicant_name=request.applicant_name,
            applicant_id=request.applicant_id,
            address=request.address,
            identity_proof=request.identity_proof,
            address_proof=request.address_proof
        )
        
        return SuccessResponse(
            success=True,
            service_request_id=result["service_request_id"],
            status=result["status"],
            message="Gas connection request submitted"
        )
    except Exception as e:
        logger.error(f"Error in gas connection request: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@app.get("/api/v1/gas/requests/{request_id}",
         response_model=ServiceStatusResponse,
         tags=["Gas"],
         summary="Get Request Status")
async def gas_get_request_status(request_id: str):
    """Get status of a gas service request"""
    try:
        request_data = service_manager.get_request_status(request_id)
        
        if not request_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Request {request_id} not found"
            )
        
        return ServiceStatusResponse(
            service_request_id=request_data["service_request_id"],
            status=request_data["status"],
            created_at=datetime.fromisoformat(request_data["created_at"]),
            updated_at=datetime.fromisoformat(request_data["updated_at"]),
            error_code=request_data.get("error_code"),
            error_message=request_data.get("error_message")
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving request status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


# ============================================================================
# 12. ERROR HANDLERS
# ============================================================================

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Handle all exceptions"""
    logger.error(f"Unhandled exception: {str(exc)}")
    return ErrorResponse(
        success=False,
        error_code="INTERNAL_ERROR",
        error_message="An internal server error occurred"
    )


# ============================================================================
# 13. RUN APPLICATION
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )
