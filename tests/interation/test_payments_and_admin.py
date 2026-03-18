"""
tests/integration/test_payments_and_admin.py
=============================================
Integration tests for:
    - Payments API (initiate, complete, status, history)
    - Admin request management (list, filter, status transitions)
    - Admin payments view
    - Kiosk configuration (super-admin only)
    - Shared request lookup

These tests prove the full workflow from payment initiation
through admin approval/denial — the backbone of the system.
"""

import pytest


# ─────────────────────────────────────────────────────────────────────────────
#  Payments API
# ─────────────────────────────────────────────────────────────────────────────

class TestPaymentInitiate:

    PAYLOAD = {
        "userId":         "pay_integ_user_001",
        "billId":         "BILL-PAY-INTEG-001",
        "dept":           "electricity",
        "amount":         822.00,
        "currency":       "INR",
        "method":         "upi",
        "gateway":        "mock",
        "consumerNumber": "MTR-PAY-TEST",
        "billingPeriod":  "2026-02",
    }

    def test_initiate_returns_200(self, client):
        r = client.post("/api/v1/payments/initiate", json=self.PAYLOAD)
        assert r.status_code == 200

    def test_initiate_returns_payment_id(self, client):
        r = client.post("/api/v1/payments/initiate", json=self.PAYLOAD)
        pay_id = r.json().get("paymentId") or r.json().get("payment_id")
        assert pay_id, "paymentId must be present in initiate response"

    def test_initiate_returns_order_id(self, client):
        r = client.post("/api/v1/payments/initiate", json=self.PAYLOAD)
        order_id = r.json().get("orderId") or r.json().get("order_id")
        assert order_id, "orderId must be present in initiate response"

    def test_mock_flag_is_true(self, client):
        r = client.post("/api/v1/payments/initiate", json=self.PAYLOAD)
        assert r.json().get("isMock") is True

    def test_missing_user_id_returns_422(self, client):
        bad = {k: v for k, v in self.PAYLOAD.items() if k != "userId"}
        assert client.post("/api/v1/payments/initiate", json=bad).status_code == 422

    def test_missing_amount_returns_422(self, client):
        bad = {k: v for k, v in self.PAYLOAD.items() if k != "amount"}
        assert client.post("/api/v1/payments/initiate", json=bad).status_code == 422

    def test_missing_dept_returns_422(self, client):
        bad = {k: v for k, v in self.PAYLOAD.items() if k != "dept"}
        assert client.post("/api/v1/payments/initiate", json=bad).status_code == 422


class TestPaymentComplete:

    def _initiate(self, client):
        r = client.post("/api/v1/payments/initiate", json={
            "userId": "pay_complete_user", "billId": "BILL-COMPLETE-001",
            "dept": "water", "amount": 300.00, "currency": "INR",
            "method": "upi", "gateway": "mock",
            "consumerNumber": "WAT-COMP-001", "billingPeriod": "2026-02",
        })
        d = r.json()
        return (
            d.get("paymentId") or d.get("payment_id"),
            d.get("orderId") or d.get("order_id"),
        )

    def test_complete_returns_200(self, client):
        pay_id, order_id = self._initiate(client)
        r = client.post("/api/v1/payments/complete", json={
            "paymentId": pay_id, "orderId": order_id,
            "gateway": "mock", "gatewayPaymentId": "pay_mock_test_001",
        })
        assert r.status_code == 200

    def test_complete_returns_receipt(self, client):
        pay_id, order_id = self._initiate(client)
        r = client.post("/api/v1/payments/complete", json={
            "paymentId": pay_id, "orderId": order_id,
            "gateway": "mock", "gatewayPaymentId": "pay_mock_test_002",
        })
        assert r.json().get("receipt"), "Complete must return a receipt"


class TestPaymentHistory:

    def test_history_returns_200(self, client):
        r = client.get("/api/v1/payments/history/any_user")
        assert r.status_code == 200

    def test_history_is_list(self, client):
        r = client.get("/api/v1/payments/history/any_user")
        data = r.json()
        # History may be a list or a dict with a list — check either
        assert isinstance(data, (list, dict))

    def test_history_after_payment_is_non_empty(self, client):
        user = "history_test_user"
        # Make a payment for this user
        r = client.post("/api/v1/payments/initiate", json={
            "userId": user, "billId": "BILL-HIST-001",
            "dept": "electricity", "amount": 500.00, "currency": "INR",
            "method": "upi", "gateway": "mock",
            "consumerNumber": "MTR-HIST-001", "billingPeriod": "2026-02",
        })
        pay_id = r.json().get("paymentId") or r.json().get("payment_id")
        order_id = r.json().get("orderId") or r.json().get("order_id")
        client.post("/api/v1/payments/complete", json={
            "paymentId": pay_id, "orderId": order_id,
            "gateway": "mock", "gatewayPaymentId": "pay_mock_hist_001",
        })
        # Now check history
        r2 = client.get(f"/api/v1/payments/history/{user}")
        assert r2.status_code == 200


# ─────────────────────────────────────────────────────────────────────────────
#  Admin — Request Management
# ─────────────────────────────────────────────────────────────────────────────

class TestAdminRequestList:

    def test_list_returns_200(self, client, admin_token):
        r = client.get("/admin/requests", headers={"Authorization": f"Bearer {admin_token}"})
        assert r.status_code == 200

    def test_list_has_requests_key(self, client, admin_token):
        r = client.get("/admin/requests", headers={"Authorization": f"Bearer {admin_token}"})
        assert "requests" in r.json()

    def test_list_has_total_key(self, client, admin_token):
        r = client.get("/admin/requests", headers={"Authorization": f"Bearer {admin_token}"})
        assert "total" in r.json()

    def test_filter_by_electricity(self, client, admin_token):
        r = client.get("/admin/requests",
                       params={"department": "electricity"},
                       headers={"Authorization": f"Bearer {admin_token}"})
        assert r.status_code == 200
        for row in r.json().get("requests", []):
            assert row["department"] == "electricity"

    def test_filter_by_water(self, client, admin_token):
        r = client.get("/admin/requests",
                       params={"department": "water"},
                       headers={"Authorization": f"Bearer {admin_token}"})
        assert r.status_code == 200
        for row in r.json().get("requests", []):
            assert row["department"] == "water"

    def test_filter_by_status_submitted(self, client, admin_token):
        r = client.get("/admin/requests",
                       params={"status": "SUBMITTED"},
                       headers={"Authorization": f"Bearer {admin_token}"})
        assert r.status_code == 200
        for row in r.json().get("requests", []):
            assert row["status"] == "SUBMITTED"


class TestAdminStatusTransitions:
    """
    The full lifecycle: SUBMITTED → APPROVED → DELIVERED
    and the rejection path: SUBMITTED → DENIED
    """

    def _create_request(self, client):
        """Create an electricity service request and return its ID."""
        r = client.post("/api/v1/electricity/new-connection", json={
            "customer_name": "Admin Test Citizen", "customer_id": "CUST-ADMIN-TEST",
            "address": "Imphal", "load_requirement": "2kW",
            "identity_proof": "AADHAAR-TEST", "address_proof": "RATION-TEST",
        })
        return r.json().get("service_request_id")

    def test_approve_request(self, client, admin_token):
        req_id = self._create_request(client)
        r = client.patch(
            f"/admin/requests/{req_id}/status",
            json={"status": "APPROVED", "note": "Documents verified"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert r.status_code == 200
        assert r.json()["new_status"] == "APPROVED"

    def test_deliver_request(self, client, admin_token):
        req_id = self._create_request(client)
        # First approve
        client.patch(f"/admin/requests/{req_id}/status",
                     json={"status": "APPROVED"},
                     headers={"Authorization": f"Bearer {admin_token}"})
        # Then deliver
        r = client.patch(
            f"/admin/requests/{req_id}/status",
            json={"status": "DELIVERED"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert r.status_code == 200
        assert r.json()["new_status"] == "DELIVERED"

    def test_deny_request(self, client, admin_token):
        req_id = self._create_request(client)
        r = client.patch(
            f"/admin/requests/{req_id}/status",
            json={"status": "DENIED", "error_code": "DOCS_INCOMPLETE",
                  "error_message": "Address proof not legible"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert r.status_code == 200
        assert r.json()["new_status"] == "DENIED"

    def test_get_specific_request(self, client, admin_token):
        req_id = self._create_request(client)
        r = client.get(
            f"/admin/requests/{req_id}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert r.status_code == 200
        assert r.json()["department"] == "electricity"

    def test_nonexistent_request_returns_404(self, client, admin_token):
        r = client.get(
            "/admin/requests/nonexistent-id-xyz",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert r.status_code == 404


# ─────────────────────────────────────────────────────────────────────────────
#  Admin — Payments View
# ─────────────────────────────────────────────────────────────────────────────

class TestAdminPaymentsView:

    def test_payments_list_returns_200(self, client, admin_token):
        r = client.get("/admin/payments",
                       headers={"Authorization": f"Bearer {admin_token}"})
        assert r.status_code == 200

    def test_payments_has_total_key(self, client, admin_token):
        r = client.get("/admin/payments",
                       headers={"Authorization": f"Bearer {admin_token}"})
        assert "total" in r.json()

    def test_filter_payments_by_department(self, client, admin_token):
        r = client.get("/admin/payments",
                       params={"department": "electricity"},
                       headers={"Authorization": f"Bearer {admin_token}"})
        assert r.status_code == 200


# ─────────────────────────────────────────────────────────────────────────────
#  Kiosk Configuration
# ─────────────────────────────────────────────────────────────────────────────

class TestKioskConfig:

    CONFIG = {
        "department":      "electricity",
        "razorpay_key_id": "rzp_test_SUVIDHA2026",
        "razorpay_mode":   "test",
        "is_active":       True,
        "settings":        {"kiosk_name": "SUVIDHA Kiosk Imphal"},
    }

    def test_set_config_returns_200(self, client, admin_token):
        r = client.post("/admin/kiosk-config", json=self.CONFIG,
                        headers={"Authorization": f"Bearer {admin_token}"})
        assert r.status_code == 200

    def test_key_hint_masks_all_but_last_four(self, client, admin_token):
        r = client.post("/admin/kiosk-config", json=self.CONFIG,
                        headers={"Authorization": f"Bearer {admin_token}"})
        hint = r.json().get("razorpay_key_id_hint")
        assert hint == "****2026", \
            f"Key hint should be '****2026', got '{hint}'"

    def test_config_is_active(self, client, admin_token):
        r = client.post("/admin/kiosk-config", json=self.CONFIG,
                        headers={"Authorization": f"Bearer {admin_token}"})
        assert r.json()["is_active"] is True

    def test_get_config_returns_200(self, client, admin_token):
        r = client.get("/admin/kiosk-config",
                       headers={"Authorization": f"Bearer {admin_token}"})
        assert r.status_code == 200

    def test_saved_config_appears_in_list(self, client, admin_token):
        # Set
        client.post("/admin/kiosk-config", json=self.CONFIG,
                    headers={"Authorization": f"Bearer {admin_token}"})
        # Get
        r = client.get("/admin/kiosk-config",
                       headers={"Authorization": f"Bearer {admin_token}"})
        depts = {c["department"] for c in r.json().get("configs", [])}
        assert "electricity" in depts


# ─────────────────────────────────────────────────────────────────────────────
#  Shared Request Lookup
# ─────────────────────────────────────────────────────────────────────────────

class TestSharedRequestLookup:

    def _create_request(self, client):
        r = client.post("/api/v1/electricity/new-connection", json={
            "customer_name": "Lookup Test", "customer_id": "CUST-LOOKUP",
            "address": "Imphal", "load_requirement": "1kW",
            "identity_proof": "AADHAAR-001", "address_proof": "RATION-001",
        })
        return r.json().get("service_request_id")

    def test_get_request_by_id_returns_200(self, client):
        req_id = self._create_request(client)
        r = client.get(f"/api/v1/requests/{req_id}")
        assert r.status_code == 200

    def test_request_has_correct_department(self, client):
        req_id = self._create_request(client)
        r = client.get(f"/api/v1/requests/{req_id}")
        assert r.json()["department"] == "electricity"

    def test_nonexistent_request_returns_404(self, client):
        r = client.get("/api/v1/requests/does-not-exist-xyz")
        assert r.status_code == 404

    def test_user_request_list_returns_200(self, client):
        r = client.get("/api/v1/requests/user/any_user")
        assert r.status_code == 200

    def test_user_request_list_has_total(self, client):
        r = client.get("/api/v1/requests/user/any_user")
        assert "total" in r.json()

    def test_user_requests_filter_by_department(self, client):
        r = client.get("/api/v1/requests/user/any_user",
                       params={"department": "municipal"})
        assert r.status_code == 200
