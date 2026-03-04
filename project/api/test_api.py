"""
KOISK FastAPI - Test Examples
=============================

Example requests for testing the API endpoints.
Can be run with pytest or used with curl/Postman.
"""

import pytest
import json
from httpx import AsyncClient
from koisk_api import app

# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
async def client():
    """Create async test client"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client


# ============================================================================
# Health Check Tests
# ============================================================================

@pytest.mark.asyncio
async def test_health_check(client: AsyncClient):
    """Test health check endpoint"""
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "services" in data


@pytest.mark.asyncio
async def test_root_endpoint(client: AsyncClient):
    """Test root endpoint"""
    response = await client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "version" in data
    assert "endpoints" in data


# ============================================================================
# Electricity Tests
# ============================================================================

@pytest.mark.asyncio
async def test_electricity_pay_bill(client: AsyncClient):
    """Test electricity bill payment"""
    payload = {
        "user_id": "CUST123456",
        "meter_number": "ELEC123456",
        "billing_period": "2026-01",
        "amount": "1500.00",
        "payment_method": "UPI"
    }
    
    response = await client.post("/api/v1/electricity/pay-bill", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] == True
    assert "service_request_id" in data
    assert data["status"] == "SUBMITTED"
    assert data["message"] == "Bill payment request submitted successfully"
    
    return data["service_request_id"]


@pytest.mark.asyncio
async def test_electricity_transfer_service(client: AsyncClient):
    """Test electricity service transfer"""
    payload = {
        "old_customer_id": "OLD_CUST123",
        "new_customer_id": "NEW_CUST456",
        "meter_number": "ELEC123456",
        "identity_proof": "ID_REF_001",
        "ownership_proof": "OWN_REF_001",
        "consent_doc": "CONS_REF_001",
        "effective_date": "2026-03-01"
    }
    
    response = await client.post("/api/v1/electricity/transfer-service", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] == True
    assert "service_request_id" in data
    assert "transfer" in data["message"].lower() or "submitted" in data["message"].lower()


@pytest.mark.asyncio
async def test_electricity_meter_change(client: AsyncClient):
    """Test electricity meter change"""
    payload = {
        "user_id": "CUST123456",
        "meter_number": "ELEC123456",
        "reason": "Meter malfunction",
        "new_meter_number": None
    }
    
    response = await client.post("/api/v1/electricity/meter-change", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] == True
    assert "service_request_id" in data


@pytest.mark.asyncio
async def test_electricity_new_connection(client: AsyncClient):
    """Test new electricity connection request"""
    payload = {
        "customer_name": "John Doe",
        "customer_id": "CUST789012",
        "address": "123 Main Street, City",
        "load_requirement": "5",
        "identity_proof": "AADHAR_12345",
        "address_proof": "RENT_AGREEMENT_001"
    }
    
    response = await client.post("/api/v1/electricity/new-connection", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] == True
    assert "service_request_id" in data


@pytest.mark.asyncio
async def test_electricity_get_request_status(client: AsyncClient):
    """Test get electricity request status"""
    # First create a request
    create_payload = {
        "user_id": "CUST123456",
        "meter_number": "ELEC123456",
        "billing_period": "2026-01",
        "amount": "1500.00",
        "payment_method": "UPI"
    }
    
    create_response = await client.post("/api/v1/electricity/pay-bill", json=create_payload)
    request_id = create_response.json()["service_request_id"]
    
    # Now get the status
    response = await client.get(f"/api/v1/electricity/requests/{request_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["service_request_id"] == request_id
    assert "status" in data


@pytest.mark.asyncio
async def test_electricity_list_user_requests(client: AsyncClient):
    """Test list user electricity requests"""
    user_id = "CUST123456"
    
    response = await client.get(f"/api/v1/electricity/user/{user_id}/requests")
    assert response.status_code == 200
    data = response.json()
    assert data["user_id"] == user_id
    assert "request_count" in data
    assert "requests" in data


# ============================================================================
# Water Tests
# ============================================================================

@pytest.mark.asyncio
async def test_water_pay_bill(client: AsyncClient):
    """Test water bill payment"""
    payload = {
        "user_id": "CONS123456",
        "consumer_number": "WATER123456",
        "billing_period": "2026-01",
        "amount": "800.00",
        "payment_method": "UPI"
    }
    
    response = await client.post("/api/v1/water/pay-bill", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] == True
    assert "service_request_id" in data
    assert data["status"] == "SUBMITTED"


@pytest.mark.asyncio
async def test_water_new_connection(client: AsyncClient):
    """Test new water connection request"""
    payload = {
        "applicant_name": "Jane Smith",
        "applicant_id": "APPL123456",
        "address": "456 Oak Avenue, City",
        "property_type": "Residential",
        "identity_proof": "AADHAR_67890",
        "address_proof": "OWNERSHIP_PROOF_002"
    }
    
    response = await client.post("/api/v1/water/new-connection", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] == True
    assert "service_request_id" in data


@pytest.mark.asyncio
async def test_water_leak_complaint(client: AsyncClient):
    """Test water leak complaint"""
    payload = {
        "consumer_id": "CONS123456",
        "consumer_number": "WATER123456",
        "complaint_type": "Pipeline leak",
        "location": "Main meter area",
        "severity": "High",
        "description": "Water leaking from main pipeline near meter"
    }
    
    response = await client.post("/api/v1/water/leak-complaint", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] == True
    assert "service_request_id" in data
    assert "leak" in data["message"].lower() or "complaint" in data["message"].lower()


@pytest.mark.asyncio
async def test_water_get_request_status(client: AsyncClient):
    """Test get water request status"""
    # First create a request
    create_payload = {
        "user_id": "CONS123456",
        "consumer_number": "WATER123456",
        "billing_period": "2026-01",
        "amount": "800.00",
        "payment_method": "UPI"
    }
    
    create_response = await client.post("/api/v1/water/pay-bill", json=create_payload)
    request_id = create_response.json()["service_request_id"]
    
    # Now get the status
    response = await client.get(f"/api/v1/water/requests/{request_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["service_request_id"] == request_id


# ============================================================================
# Gas Tests
# ============================================================================

@pytest.mark.asyncio
async def test_gas_pay_bill(client: AsyncClient):
    """Test gas bill payment"""
    payload = {
        "user_id": "CUST123456",
        "consumer_number": "GAS123456",
        "billing_period": "2026-01",
        "amount": "1200.00",
        "payment_method": "UPI"
    }
    
    response = await client.post("/api/v1/gas/pay-bill", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] == True
    assert "service_request_id" in data


@pytest.mark.asyncio
async def test_gas_new_connection(client: AsyncClient):
    """Test new gas connection request"""
    payload = {
        "applicant_name": "Robert Johnson",
        "applicant_id": "APPL789012",
        "address": "789 Pine Road, City",
        "identity_proof": "AADHAR_11111",
        "address_proof": "OWNERSHIP_PROOF_003"
    }
    
    response = await client.post("/api/v1/gas/new-connection", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] == True
    assert "service_request_id" in data


@pytest.mark.asyncio
async def test_gas_get_request_status(client: AsyncClient):
    """Test get gas request status"""
    # First create a request
    create_payload = {
        "user_id": "CUST123456",
        "consumer_number": "GAS123456",
        "billing_period": "2026-01",
        "amount": "1200.00",
        "payment_method": "UPI"
    }
    
    create_response = await client.post("/api/v1/gas/pay-bill", json=create_payload)
    request_id = create_response.json()["service_request_id"]
    
    # Now get the status
    response = await client.get(f"/api/v1/gas/requests/{request_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["service_request_id"] == request_id


# ============================================================================
# Error Handling Tests
# ============================================================================

@pytest.mark.asyncio
async def test_invalid_request_data(client: AsyncClient):
    """Test with invalid request data"""
    payload = {
        "user_id": "CUST123456",
        # Missing required fields
    }
    
    response = await client.post("/api/v1/electricity/pay-bill", json=payload)
    assert response.status_code == 422  # Validation error


@pytest.mark.asyncio
async def test_nonexistent_request_status(client: AsyncClient):
    """Test getting status of non-existent request"""
    response = await client.get("/api/v1/electricity/requests/nonexistent-id")
    assert response.status_code == 404


# ============================================================================
# Run tests
# ============================================================================

if __name__ == "__main__":
    # Run with: pytest tests/test_api.py -v
    # Or: python -m pytest tests/test_api.py -v --asyncio-mode=auto
    pytest.main([__file__, "-v", "--tb=short"])
