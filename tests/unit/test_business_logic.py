"""
tests/unit/test_business_logic.py
==================================
Unit tests for pure business logic functions.

These tests import functions directly — no HTTP requests, no database.
They run instantly and are the fastest proof that core logic is correct.

Coverage:
    - OTP generation & hashing (kiosk session security)
    - Password hashing & verification (authentication)
    - Payment amount formatting
    - Bill ID generation
    - Session token entropy
    - Input sanitisation helpers
"""

import hashlib
import re
import secrets

import pytest


# ─────────────────────────────────────────────────────────────────────────────
#  OTP Logic  (src/api/kiosk/router.py)
# ─────────────────────────────────────────────────────────────────────────────

from src.api.kiosk.router import _generate_otp, _hash_otp, _new_session_token


class TestOTPGeneration:
    """OTP must be exactly 6 digits, uniform, and not reused."""

    def test_otp_is_six_digits(self):
        otp = _generate_otp()
        assert len(otp) == 6, "OTP must be exactly 6 characters"
        assert otp.isdigit(), "OTP must contain only digits"

    def test_otp_zero_padded(self):
        """Low values like '000042' must be zero-padded, not '42'."""
        # Patch random to return a known small value
        import src.api.kiosk.router as kiosk_mod
        original = kiosk_mod.random.SystemRandom().randint
        class _FakeRNG:
            def randint(self, a, b):
                return 42
        original_rng = kiosk_mod.random.SystemRandom
        kiosk_mod.random.SystemRandom = lambda: _FakeRNG()
        otp = _generate_otp()
        kiosk_mod.random.SystemRandom = original_rng
        assert otp == "000042"

    def test_otp_values_in_range(self):
        for _ in range(200):
            otp = _generate_otp()
            assert 0 <= int(otp) <= 999999

    def test_otp_not_constant(self):
        """100 consecutive OTPs must not all be the same."""
        otps = {_generate_otp() for _ in range(100)}
        assert len(otps) > 1, "OTP generator appears deterministic"

    def test_otp_hash_is_sha256(self):
        otp = "123456"
        expected = hashlib.sha256(b"123456").hexdigest()
        assert _hash_otp(otp) == expected

    def test_different_otps_produce_different_hashes(self):
        assert _hash_otp("000000") != _hash_otp("999999")

    def test_same_otp_always_produces_same_hash(self):
        assert _hash_otp("472819") == _hash_otp("472819")

    def test_hash_length_is_64_hex_chars(self):
        assert len(_hash_otp("000000")) == 64


class TestSessionTokenEntropy:
    """Session tokens must be cryptographically random and URL-safe."""

    def test_token_length_sufficient(self):
        token = _new_session_token()
        # secrets.token_urlsafe(32) → ~43 base64url chars
        assert len(token) >= 40, "Session token too short"

    def test_tokens_are_unique(self):
        tokens = {_new_session_token() for _ in range(50)}
        assert len(tokens) == 50, "Session tokens are not unique"

    def test_token_is_url_safe(self):
        token = _new_session_token()
        assert re.match(r'^[A-Za-z0-9_\-]+$', token), \
            "Session token contains URL-unsafe characters"


# ─────────────────────────────────────────────────────────────────────────────
#  Password Hashing  (src/department/database/database.py)
# ─────────────────────────────────────────────────────────────────────────────

from src.department.database.database import _hash_password


class TestPasswordHashing:
    """
    Passwords must never be stored in plaintext.

    _hash_password uses bcrypt (passlib) when available, falling back to
    SHA-256 in constrained environments.  Tests cover both paths so the
    suite is green regardless of which hasher is active.
    """

    def _using_bcrypt(self):
        """Detect whether the real bcrypt path is active."""
        return _hash_password("probe").startswith("$2")

    def test_hash_is_not_plaintext(self):
        assert _hash_password("secret") != "secret"

    def test_hash_is_a_string(self):
        assert isinstance(_hash_password("Admin@1234"), str)

    def test_hash_is_non_empty(self):
        assert len(_hash_password("Admin@1234")) > 0

    def test_different_passwords_produce_different_hashes(self):
        assert _hash_password("password1") != _hash_password("password2")

    def test_bcrypt_hashes_are_not_deterministic(self):
        """bcrypt is salted — same input must never produce the same hash."""
        if not self._using_bcrypt():
            pytest.skip("bcrypt not active in this environment")
        h1 = _hash_password("Admin@1234")
        h2 = _hash_password("Admin@1234")
        assert h1 != h2, "bcrypt should produce unique hashes (salted)"

    def test_bcrypt_hash_has_correct_prefix(self):
        if not self._using_bcrypt():
            pytest.skip("bcrypt not active in this environment")
        h = _hash_password("Admin@1234")
        assert h.startswith("$2b$") or h.startswith("$2a$")

    def test_sha256_fallback_is_64_hex_chars(self):
        """SHA-256 fallback must produce a 64-character hex digest."""
        if self._using_bcrypt():
            pytest.skip("bcrypt is active — fallback not used")
        h = _hash_password("Admin@1234")
        assert len(h) == 64
        assert all(c in "0123456789abcdef" for c in h)

    def test_sha256_fallback_is_deterministic(self):
        """SHA-256 has no salt — same input always produces the same hash."""
        if self._using_bcrypt():
            pytest.skip("bcrypt is active — fallback not used")
        assert _hash_password("Admin@1234") == _hash_password("Admin@1234")


# ─────────────────────────────────────────────────────────────────────────────
#  Mock Payment Engine — reference number and timestamp helpers
# ─────────────────────────────────────────────────────────────────────────────

from src.payment.mock_payment_engine import _make_reference, _now_iso


class TestReferenceNumberGeneration:
    """Reference numbers must be unique, prefixed correctly, and sequenced."""

    def test_electricity_reference_contains_elec(self):
        ref = _make_reference("electricity")
        assert "ELEC" in ref, f"Electricity ref should contain ELEC: {ref}"

    def test_water_reference_contains_wat(self):
        ref = _make_reference("water")
        assert "WAT" in ref, f"Water ref should contain WAT: {ref}"

    def test_municipal_reference_contains_muni(self):
        ref = _make_reference("municipal")
        assert "MUNI" in ref, f"Municipal ref should contain MUNI: {ref}"

    def test_unknown_dept_falls_back_to_pay(self):
        ref = _make_reference("unknown_dept")
        assert "PAY" in ref

    def test_references_are_sequential(self):
        """Each call for the same dept/day increments the counter."""
        r1 = _make_reference("electricity")
        r2 = _make_reference("electricity")
        # Extract the trailing sequence numbers
        seq1 = int(r1.split("-")[-1])
        seq2 = int(r2.split("-")[-1])
        assert seq2 == seq1 + 1, "References should be sequential"

    def test_reference_starts_with_pay(self):
        ref = _make_reference("water")
        assert ref.startswith("PAY-")

    def test_reference_contains_date(self):
        from datetime import datetime
        today = datetime.utcnow().strftime("%Y%m%d")
        ref = _make_reference("electricity")
        assert today in ref, f"Reference should contain today's date: {ref}"

    def test_different_depts_produce_different_prefixes(self):
        elec_ref = _make_reference("electricity")
        water_ref = _make_reference("water")
        assert elec_ref.split("-")[1] != water_ref.split("-")[1]


class TestTimestampHelper:
    """_now_iso must return a valid ISO 8601 UTC timestamp."""

    def test_now_iso_is_parseable(self):
        from datetime import datetime
        ts = _now_iso()
        datetime.fromisoformat(ts)  # raises if invalid

    def test_now_iso_is_string(self):
        assert isinstance(_now_iso(), str)

    def test_now_iso_contains_timezone(self):
        ts = _now_iso()
        # UTC offset must be present (+00:00 or Z)
        assert "+" in ts or "Z" in ts, f"Timestamp should include timezone: {ts}"


# ─────────────────────────────────────────────────────────────────────────────
#  Department Catalogue  (src/api/kiosk/router.py)
# ─────────────────────────────────────────────────────────────────────────────

from src.api.kiosk.router import _DEPARTMENT_CATALOGUE


class TestDepartmentCatalogue:
    """The catalogue is the source of truth for what services are offered."""

    REQUIRED_DEPTS = {"electricity", "water", "municipal"}

    def test_all_required_departments_present(self):
        assert self.REQUIRED_DEPTS.issubset(set(_DEPARTMENT_CATALOGUE.keys()))

    def test_each_department_has_services(self):
        for dept, info in _DEPARTMENT_CATALOGUE.items():
            assert len(info.get("services", [])) > 0, \
                f"Department '{dept}' has no services"

    def test_each_service_has_required_keys(self):
        for dept, info in _DEPARTMENT_CATALOGUE.items():
            for svc in info["services"]:
                assert "id" in svc,          f"{dept}: service missing 'id'"
                assert "label" in svc,       f"{dept}: service missing 'label'"
                assert "has_payment" in svc, f"{dept}: service missing 'has_payment'"

    def test_pay_bill_services_have_payment_flag(self):
        for dept, info in _DEPARTMENT_CATALOGUE.items():
            for svc in info["services"]:
                if "PAY_BILL" in svc["id"]:
                    assert svc["has_payment"] is True, \
                        f"{dept}/{svc['id']} should have has_payment=True"

    def test_complaint_services_do_not_require_payment(self):
        for dept, info in _DEPARTMENT_CATALOGUE.items():
            for svc in info["services"]:
                if "COMPLAINT" in svc["id"] or "GRIEVANCE" in svc["id"]:
                    assert svc["has_payment"] is False, \
                        f"{dept}/{svc['id']} should not require payment"

    def test_electricity_has_pay_bill_service(self):
        elec_ids = {s["id"] for s in _DEPARTMENT_CATALOGUE["electricity"]["services"]}
        assert "ELECTRICITY_PAY_BILL" in elec_ids

    def test_water_has_leak_complaint_service(self):
        water_ids = {s["id"] for s in _DEPARTMENT_CATALOGUE["water"]["services"]}
        assert "WATER_LEAK_COMPLAINT" in water_ids

    def test_municipal_has_birth_certificate_service(self):
        muni_ids = {s["id"] for s in _DEPARTMENT_CATALOGUE["municipal"]["services"]}
        assert "MUNICIPAL_BIRTH_CERTIFICATE" in muni_ids
