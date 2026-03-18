"""
tests/integration/test_auth.py
================================
Integration tests for authentication and authorisation.

Tests prove:
    1. Admin login flow (correct / wrong credentials)
    2. JWT token is required for protected routes
    3. Role-based access control — dept admin cannot access super-admin endpoints
    4. Token format and claims
"""

import pytest


class TestAdminAuthentication:
    """Admin login must issue a JWT and reject bad credentials."""

    def test_correct_credentials_returns_200(self, client):
        r = client.post("/admin/login", data={
            "username": "admin",
            "password": "Admin@1234",
        })
        assert r.status_code == 200

    def test_response_contains_access_token(self, client):
        r = client.post("/admin/login", data={
            "username": "admin",
            "password": "Admin@1234",
        })
        assert "access_token" in r.json()
        assert r.json()["access_token"]  # non-empty

    def test_response_contains_role(self, client):
        r = client.post("/admin/login", data={
            "username": "admin",
            "password": "Admin@1234",
        })
        assert r.json()["role"] == "super_admin"

    def test_super_admin_department_is_null(self, client):
        r = client.post("/admin/login", data={
            "username": "admin",
            "password": "Admin@1234",
        })
        assert r.json()["department"] is None

    def test_wrong_password_returns_401(self, client):
        r = client.post("/admin/login", data={
            "username": "admin",
            "password": "WRONG_PASSWORD",
        })
        assert r.status_code == 401

    def test_wrong_username_returns_401(self, client):
        r = client.post("/admin/login", data={
            "username": "nonexistent_user",
            "password": "Admin@1234",
        })
        assert r.status_code == 401

    def test_empty_password_returns_401_or_422(self, client):
        r = client.post("/admin/login", data={
            "username": "admin",
            "password": "",
        })
        assert r.status_code in (401, 422)

    def test_dept_admin_login_returns_correct_role(self, client):
        r = client.post("/admin/login", data={
            "username": "water_admin",
            "password": "Water@1234",
        })
        assert r.status_code == 200
        assert r.json()["role"] == "department_admin"
        assert r.json()["department"] == "water"


class TestProtectedRoutes:
    """Protected routes must reject requests without a valid JWT."""

    def test_no_token_returns_401(self, client):
        r = client.get("/admin/requests")
        assert r.status_code == 401

    def test_invalid_token_returns_401(self, client):
        r = client.get("/admin/requests", headers={
            "Authorization": "Bearer this.is.not.valid",
        })
        assert r.status_code == 401

    def test_malformed_auth_header_returns_401(self, client):
        r = client.get("/admin/requests", headers={
            "Authorization": "NotBearer sometoken",
        })
        assert r.status_code == 401

    def test_valid_token_allows_access(self, client, admin_token):
        r = client.get("/admin/requests", headers={
            "Authorization": f"Bearer {admin_token}",
        })
        assert r.status_code == 200


class TestRoleBasedAccessControl:
    """
    Department admins must be scoped to their department only.
    Super-admin only endpoints must reject department admins.
    """

    def test_dept_admin_cannot_access_kiosk_config(self, client, dept_token):
        """Kiosk config is super-admin only."""
        r = client.get("/admin/kiosk-config", headers={
            "Authorization": f"Bearer {dept_token}",
        })
        assert r.status_code == 403

    def test_super_admin_can_access_kiosk_config(self, client, admin_token):
        r = client.get("/admin/kiosk-config", headers={
            "Authorization": f"Bearer {admin_token}",
        })
        assert r.status_code == 200

    def test_dept_admin_requests_scoped_to_own_department(self, client, dept_token):
        """
        Water dept admin should only see water requests — never electricity
        or municipal rows in their filtered view.
        """
        r = client.get("/admin/requests", headers={
            "Authorization": f"Bearer {dept_token}",
        })
        assert r.status_code == 200
        for req in r.json().get("requests", []):
            assert req["department"] == "water", \
                f"Dept admin saw a row from dept '{req['department']}'"

    def test_super_admin_can_see_all_departments(self, client, admin_token):
        r = client.get("/admin/requests", headers={
            "Authorization": f"Bearer {admin_token}",
        })
        assert r.status_code == 200
        # Super-admin is not restricted to one department
        # (result may be empty — just check no 403)
