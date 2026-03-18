"""
tests/integration/test_departments.py
========================================
Integration tests for Electricity, Water, and Municipal endpoints.

Each department test class is self-contained.
Payment calls use gateway="mock" so no real Razorpay/PortOne calls are made.

Tests prove:
    - Bill retrieval
    - Payment flow (initiate + complete via mock gateway)
    - New connection requests
    - Complaint / grievance submission
    - Service request IDs are returned
    - Statuses are correct for mock vs real flows
"""

import pytest


# ─────────────────────────────────────────────────────────────────────────────
#  Electricity
# ─────────────────────────────────────────────────────────────────────────────

class TestElectricityBills:

    def test_bills_endpoint_returns_200(self, client):
        r = client.get("/api/v1/electricity/bills/any_user")
        assert r.status_code == 200

    def test_bills_response_has_bills_key(self, client):
        r = client.get("/api/v1/electricity/bills/any_user")
        assert "bills" in r.json()

    def test_bills_is_a_list(self, client):
        r = client.get("/api/v1/electricity/bills/any_user")
        assert isinstance(r.json()["bills"], list)


class TestElectricityPayBill:

    PAYLOAD = {
        "user_id":        "integ_user_elec",
        "meter_number":   "MTR-INTEG-0001",
        "billing_period": "2026-02",
        "amount":         1475.50,
        "payment_method": "upi",
        "gateway":        "mock",
    }

    def test_pay_bill_returns_200(self, client):
        r = client.post("/api/v1/electricity/pay-bill", json=self.PAYLOAD)
        assert r.status_code == 200

    def test_pay_bill_success_flag(self, client):
        r = client.post("/api/v1/electricity/pay-bill", json=self.PAYLOAD)
        assert r.json().get("success") is True

    def test_pay_bill_department_is_electricity(self, client):
        r = client.post("/api/v1/electricity/pay-bill", json=self.PAYLOAD)
        assert r.json().get("department") == "electricity"

    def test_pay_bill_returns_service_request_id(self, client):
        r = client.post("/api/v1/electricity/pay-bill", json=self.PAYLOAD)
        assert r.json().get("service_request_id")

    def test_mock_payment_status_is_delivered(self, client):
        r = client.post("/api/v1/electricity/pay-bill", json=self.PAYLOAD)
        assert r.json().get("status") == "DELIVERED"

    def test_pay_bill_receipt_present(self, client):
        r = client.post("/api/v1/electricity/pay-bill", json=self.PAYLOAD)
        assert r.json().get("data")  # receipt data

    def test_receipt_has_reference_number(self, client):
        r = client.post("/api/v1/electricity/pay-bill", json=self.PAYLOAD)
        receipt = r.json().get("data", {})
        ref = receipt.get("reference_no") or receipt.get("referenceNo")
        assert ref, "Receipt must have a reference number"

    def test_missing_amount_returns_422(self, client):
        bad = {k: v for k, v in self.PAYLOAD.items() if k != "amount"}
        r = client.post("/api/v1/electricity/pay-bill", json=bad)
        assert r.status_code == 422

    def test_missing_user_id_returns_422(self, client):
        bad = {k: v for k, v in self.PAYLOAD.items() if k != "user_id"}
        r = client.post("/api/v1/electricity/pay-bill", json=bad)
        assert r.status_code == 422


class TestElectricityNewConnection:

    PAYLOAD = {
        "customer_name":    "Konsam Ibochouba",
        "customer_id":      "CUST-TEST-ELEC-0001",
        "address":          "Keishamthong, Imphal West, Manipur",
        "load_requirement": "3kW",
        "identity_proof":   "AADHAAR-1234567890",
        "address_proof":    "RATION-001",
    }

    def test_new_connection_returns_200(self, client):
        r = client.post("/api/v1/electricity/new-connection", json=self.PAYLOAD)
        assert r.status_code == 200

    def test_new_connection_status_submitted(self, client):
        r = client.post("/api/v1/electricity/new-connection", json=self.PAYLOAD)
        assert r.json().get("status") == "SUBMITTED"

    def test_new_connection_returns_request_id(self, client):
        r = client.post("/api/v1/electricity/new-connection", json=self.PAYLOAD)
        assert r.json().get("service_request_id")


class TestElectricityMeterChange:

    def test_meter_change_returns_200(self, client):
        r = client.post("/api/v1/electricity/meter-change", json={
            "user_id": "integ_user_elec", "meter_number": "MTR-OLD-001",
            "reason": "Burnt meter",
        })
        assert r.status_code == 200


class TestElectricityServiceTransfer:

    def test_service_transfer_returns_200(self, client):
        r = client.post("/api/v1/electricity/transfer-service", json={
            "old_customer_id": "CUST-OLD", "new_customer_id": "CUST-NEW",
            "meter_number": "MTR-001", "identity_proof": "AADHAAR-001",
            "ownership_proof": "SALE-DEED-001", "consent_doc": "NOC-001",
            "effective_date": "2026-04-01",
        })
        assert r.status_code == 200


# ─────────────────────────────────────────────────────────────────────────────
#  Water
# ─────────────────────────────────────────────────────────────────────────────

class TestWaterBills:

    def test_bills_endpoint_returns_200(self, client):
        r = client.get("/api/v1/water/bills/any_user")
        assert r.status_code == 200

    def test_bills_response_has_bills_key(self, client):
        assert "bills" in client.get("/api/v1/water/bills/any_user").json()


class TestWaterPayBill:

    PAYLOAD = {
        "user_id":         "integ_user_water",
        "consumer_number": "WAT-INTEG-0001",
        "billing_period":  "2026-02",
        "amount":          380.00,
        "payment_method":  "card",
        "gateway":         "mock",
    }

    def test_pay_bill_returns_200(self, client):
        assert client.post("/api/v1/water/pay-bill", json=self.PAYLOAD).status_code == 200

    def test_pay_bill_success_flag(self, client):
        assert client.post("/api/v1/water/pay-bill", json=self.PAYLOAD).json()["success"] is True

    def test_pay_bill_department_is_water(self, client):
        r = client.post("/api/v1/water/pay-bill", json=self.PAYLOAD)
        assert r.json()["department"] == "water"

    def test_pay_bill_receipt_present(self, client):
        r = client.post("/api/v1/water/pay-bill", json=self.PAYLOAD)
        assert r.json().get("data")

    def test_mock_status_is_delivered(self, client):
        r = client.post("/api/v1/water/pay-bill", json=self.PAYLOAD)
        assert r.json()["status"] == "DELIVERED"


class TestWaterNewConnection:

    def test_new_connection_returns_200(self, client):
        r = client.post("/api/v1/water/new-connection", json={
            "applicant_name": "Tomba Singh", "applicant_id": "CUST-WAT-001",
            "address": "Singjamei, Imphal", "property_type": "Residential",
            "identity_proof": "AADHAAR-001", "address_proof": "RATION-001",
        })
        assert r.status_code == 200

    def test_new_connection_status_submitted(self, client):
        r = client.post("/api/v1/water/new-connection", json={
            "applicant_name": "Tomba Singh", "applicant_id": "CUST-WAT-001",
            "address": "Singjamei, Imphal", "property_type": "Residential",
            "identity_proof": "AADHAAR-001", "address_proof": "RATION-001",
        })
        assert r.json()["status"] == "SUBMITTED"


class TestWaterLeakComplaint:

    def test_leak_complaint_returns_200(self, client):
        r = client.post("/api/v1/water/leak-complaint", json={
            "consumer_id": "CUST-WAT-001", "consumer_number": "WAT-001",
            "complaint_type": "Pipe burst", "location": "Ward 12",
            "severity": "High", "description": "Main pipe burst",
        })
        assert r.status_code == 200


# ─────────────────────────────────────────────────────────────────────────────
#  Municipal
# ─────────────────────────────────────────────────────────────────────────────

class TestMunicipalBills:

    def test_bills_endpoint_returns_200(self, client):
        r = client.get("/api/v1/municipal/bills/any_user")
        assert r.status_code == 200

    def test_bills_has_bills_key(self, client):
        assert "bills" in client.get("/api/v1/municipal/bills/any_user").json()


class TestMunicipalPropertyTax:

    PAYLOAD = {
        "user_id":         "integ_user_muni",
        "consumer_number": "MUNI-INTEG-0001",
        "property_id":     "PROP-INTEG-001",
        "tax_year":        "2025-2026",
        "amount":          6200.00,
        "payment_method":  "netbanking",
        "gateway":         "mock",
    }

    def test_property_tax_returns_200(self, client):
        assert client.post("/api/v1/municipal/property-tax", json=self.PAYLOAD).status_code == 200

    def test_property_tax_success_flag(self, client):
        r = client.post("/api/v1/municipal/property-tax", json=self.PAYLOAD)
        assert r.json()["success"] is True

    def test_property_tax_department_is_municipal(self, client):
        r = client.post("/api/v1/municipal/property-tax", json=self.PAYLOAD)
        assert r.json()["department"] == "municipal"

    def test_mock_status_is_delivered(self, client):
        r = client.post("/api/v1/municipal/property-tax", json=self.PAYLOAD)
        assert r.json()["status"] == "DELIVERED"


class TestMunicipalTradeLicense:

    BASE = {
        "applicant_id": "CUST-MUNI-001", "applicant_name": "Ranjit Sharma",
        "business_name": "Test Store", "business_type": "Retail",
        "address": "Paona Bazar, Imphal", "ward_number": "WARD-12",
        "identity_proof": "AADHAAR-001", "address_proof": "RATION-001",
    }

    def test_new_license_returns_200(self, client):
        r = client.post("/api/v1/municipal/trade-license", json={**self.BASE, "is_renewal": False})
        assert r.status_code == 200

    def test_new_license_status_submitted(self, client):
        r = client.post("/api/v1/municipal/trade-license", json={**self.BASE, "is_renewal": False})
        assert r.json()["status"] == "SUBMITTED"

    def test_renewal_returns_200(self, client):
        r = client.post("/api/v1/municipal/trade-license", json={
            **self.BASE, "is_renewal": True, "existing_license_no": "TL-2025-001",
        })
        assert r.status_code == 200


class TestMunicipalCertificates:

    def test_birth_certificate_returns_200(self, client):
        r = client.post("/api/v1/municipal/birth-certificate", json={
            "applicant_id": "CUST-001", "child_name": "Sanatomba",
            "dob": "2026-01-20", "place_of_birth": "RIMS Hospital, Imphal",
            "father_name": "Tomba Singh", "mother_name": "Bimola Devi",
            "hospital_name": "RIMS Hospital", "identity_proof": "AADHAAR-001",
        })
        assert r.status_code == 200

    def test_death_certificate_returns_200(self, client):
        r = client.post("/api/v1/municipal/death-certificate", json={
            "applicant_id": "CUST-001", "deceased_name": "Dhanabir Meitei",
            "date_of_death": "2026-02-14", "place_of_death": "Shija Hospital, Imphal",
            "cause_of_death": "Cardiac arrest", "informant_name": "Ibomcha",
            "identity_proof": "AADHAAR-001", "medical_certificate": "CERT-001",
        })
        assert r.status_code == 200

    def test_building_plan_returns_200(self, client):
        r = client.post("/api/v1/municipal/building-plan", json={
            "applicant_id": "CUST-001", "applicant_name": "Konsam Ibochouba",
            "property_id": "PROP-001", "plot_area": 312.5, "built_up_area": 220.0,
            "floors": 2, "building_type": "Residential",
            "architect_name": "Ar. Premchand", "identity_proof": "AADHAAR-001",
            "land_ownership_proof": "PATTA-001", "blueprint_ref": "BP-001",
        })
        assert r.status_code == 200


class TestMunicipalComplaints:

    def test_complaint_returns_200(self, client):
        r = client.post("/api/v1/municipal/complaint", json={
            "consumer_id": "CUST-001", "complaint_category": "Garbage collection",
            "location": "Thangmeiband", "ward_number": "WARD-08",
            "description": "Garbage not collected for 6 days", "severity": "High",
        })
        assert r.status_code == 200

    def test_grievance_returns_200(self, client):
        r = client.post("/api/v1/municipal/grievance", json={
            "citizen_id": "CUST-001", "subject": "Delay in certificate",
            "description": "45 days no response", "dept_ref": "BIRTH-CERT",
        })
        assert r.status_code == 200
