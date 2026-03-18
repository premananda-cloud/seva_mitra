"""
tests/integration/test_kiosk.py
================================
Integration tests for the kiosk session / OTP flow.

Tests prove:
    1. Session creation for new and returning citizens
    2. OTP verification (correct and incorrect)
    3. Session validation via token
    4. Session expiry / end
    5. Department catalogue completeness
"""

import pytest
from tests.conftest import crack_otp





# ─────────────────────────────────────────────────────────────────────────────

class TestDepartmentCatalogue:

    def test_catalogue_returns_200(self, client):
        r = client.get("/kiosk/departments")
        assert r.status_code == 200

    def test_catalogue_contains_departments_key(self, client):
        r = client.get("/kiosk/departments")
        assert "departments" in r.json()

    def test_electricity_is_in_catalogue(self, client):
        depts = {d["id"] for d in client.get("/kiosk/departments").json()["departments"]}
        assert "electricity" in depts

    def test_water_is_in_catalogue(self, client):
        depts = {d["id"] for d in client.get("/kiosk/departments").json()["departments"]}
        assert "water" in depts

    def test_municipal_is_in_catalogue(self, client):
        depts = {d["id"] for d in client.get("/kiosk/departments").json()["departments"]}
        assert "municipal" in depts

    def test_each_department_has_services_list(self, client):
        for dept in client.get("/kiosk/departments").json()["departments"]:
            assert "services" in dept, f"Department '{dept['id']}' has no services key"
            assert len(dept["services"]) > 0, \
                f"Department '{dept['id']}' has empty services list"


class TestKioskSessionNew:
    """New citizen OTP session — session creation and OTP verification."""

    PHONE = "+919856111222"  # unique number for this test class

    def test_session_start_returns_200(self, client):
        r = client.post("/kiosk/session/start", json={
            "full_name":    "Ibemhal Devi",
            "phone_number": self.PHONE,
            "kiosk_id":     "KIOSK-TEST-01",
        })
        assert r.status_code == 200

    def test_session_start_returns_session_id(self, client):
        r = client.post("/kiosk/session/start", json={
            "full_name":    "Ibemhal Devi",
            "phone_number": self.PHONE,
            "kiosk_id":     "KIOSK-TEST-01",
        })
        assert r.json().get("session_id") is not None

    def test_session_start_otp_sent_flag(self, client):
        r = client.post("/kiosk/session/start", json={
            "full_name":    "Ibemhal Devi",
            "phone_number": self.PHONE,
            "kiosk_id":     "KIOSK-TEST-01",
        })
        assert r.json().get("otp_sent") is True

    def test_wrong_otp_returns_400(self, client):
        r = client.post("/kiosk/session/start", json={
            "full_name": "Test", "phone_number": "+919000000099", "kiosk_id": "K1",
        })
        sess_id = r.json()["session_id"]
        bad = client.post("/kiosk/session/verify-otp", json={
            "session_id": sess_id,
            "otp_code":   "000000",  # almost certainly wrong
        })
        # Either 400 (bad OTP) or a specific error — must not be 200
        assert bad.status_code != 200

    def test_correct_otp_issues_session_token(self, client):
        r = client.post("/kiosk/session/start", json={
            "full_name":    "Laishram Tomba",
            "phone_number": "+919856333444",
            "kiosk_id":     "KIOSK-TEST-01",
        })
        sess_id = r.json()["session_id"]
        otp = crack_otp(sess_id)
        assert otp is not None, "Could not retrieve OTP from DB"

        r2 = client.post("/kiosk/session/verify-otp", json={
            "session_id": sess_id,
            "otp_code":   otp,
        })
        assert r2.status_code == 200
        assert r2.json().get("session_token")

    def test_correct_otp_returns_correct_name(self, client):
        r = client.post("/kiosk/session/start", json={
            "full_name":    "Wangam Sanjit",
            "phone_number": "+919856555666",
            "kiosk_id":     "KIOSK-TEST-01",
        })
        sess_id = r.json()["session_id"]
        otp = crack_otp(sess_id)

        r2 = client.post("/kiosk/session/verify-otp", json={
            "session_id": sess_id,
            "otp_code":   otp,
        })
        assert r2.json().get("full_name") == "Wangam Sanjit"

    def test_correct_otp_success_flag(self, client):
        r = client.post("/kiosk/session/start", json={
            "full_name":    "Thokchom Bino",
            "phone_number": "+919856777888",
            "kiosk_id":     "KIOSK-TEST-01",
        })
        otp = crack_otp(r.json()["session_id"])
        r2 = client.post("/kiosk/session/verify-otp", json={
            "session_id": r.json()["session_id"],
            "otp_code":   otp,
        })
        assert r2.json().get("success") is True


class TestKioskSessionReturning:
    """
    Second session start with same phone → is_returning_user = True.
    The backend only marks a session as returning if a VERIFIED session
    already exists for that phone number.
    """

    PHONE = "+919856999000"

    def _verified_session(self, client):
        """Start a session, crack the OTP, verify it — returns the token."""
        r = client.post("/kiosk/session/start", json={
            "full_name": "Ningol Sanatombi", "phone_number": self.PHONE, "kiosk_id": "K1",
        })
        sess_id = r.json()["session_id"]
        otp = crack_otp(sess_id)
        if otp:
            client.post("/kiosk/session/verify-otp", json={
                "session_id": sess_id, "otp_code": otp,
            })

    def test_first_session_is_new_user(self, client):
        r = client.post("/kiosk/session/start", json={
            "full_name": "Ningol Sanatombi", "phone_number": self.PHONE, "kiosk_id": "K1",
        })
        assert r.json().get("is_returning_user") is False

    def test_second_session_after_verification_is_returning(self, client):
        """Verify first session, then a new start should show is_returning_user=True."""
        self._verified_session(client)
        r = client.post("/kiosk/session/start", json={
            "full_name": "Ningol Sanatombi", "phone_number": self.PHONE, "kiosk_id": "K1",
        })
        assert r.json().get("is_returning_user") is True


class TestSessionValidationAndEnd:
    """Token validation and session termination."""

    def _get_token(self, client):
        r = client.post("/kiosk/session/start", json={
            "full_name": "Yumnam Okendra", "phone_number": "+919812340000", "kiosk_id": "K1",
        })
        otp = crack_otp(r.json()["session_id"])
        r2 = client.post("/kiosk/session/verify-otp", json={
            "session_id": r.json()["session_id"], "otp_code": otp,
        })
        return r2.json().get("session_token")

    def test_valid_token_validates_successfully(self, client):
        token = self._get_token(client)
        r = client.get("/kiosk/session/validate", params={"session_token": token})
        assert r.status_code == 200
        assert r.json().get("valid") is True

    def test_invalid_token_returns_401(self, client):
        r = client.get("/kiosk/session/validate", params={
            "session_token": "this_is_not_a_real_token_xyz",
        })
        assert r.status_code == 401

    def test_session_end_returns_success(self, client):
        token = self._get_token(client)
        r = client.post("/kiosk/session/end", json={"session_token": token})
        assert r.status_code == 200
        assert r.json().get("success") is True

    def test_ended_session_token_is_invalid(self, client):
        token = self._get_token(client)
        client.post("/kiosk/session/end", json={"session_token": token})
        r = client.get("/kiosk/session/validate", params={"session_token": token})
        assert r.status_code == 401
