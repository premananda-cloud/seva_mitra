"""
tests/conftest.py
=================
Shared pytest fixtures for KOISK unit and integration tests.

Portable — works whether bcrypt is functional or falls back to SHA-256.
"""

import os
import hashlib

# ── Point to isolated in-memory DB BEFORE any app import ─────────────────────
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["MOCK_PAYMENT"] = "true"

# ── Detect whether bcrypt is usable in this environment ──────────────────────
# Some environments have a broken passlib/bcrypt pairing. We detect this once
# and patch consistently so seeding and verification always use the same scheme.
def _bcrypt_works() -> bool:
    try:
        from passlib.context import CryptContext
        ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")
        h = ctx.hash("probe")
        return ctx.verify("probe", h)
    except Exception:
        return False

_USE_BCRYPT = _bcrypt_works()

def _hash_pw(plain: str) -> str:
    if _USE_BCRYPT:
        from passlib.context import CryptContext
        return CryptContext(schemes=["bcrypt"], deprecated="auto").hash(plain)
    return hashlib.sha256(plain.encode()).hexdigest()

def _verify_pw(plain: str, hashed: str) -> bool:
    if _USE_BCRYPT:
        from passlib.context import CryptContext
        try:
            return CryptContext(schemes=["bcrypt"], deprecated="auto").verify(plain, hashed)
        except Exception:
            return False
    return hashlib.sha256(plain.encode()).hexdigest() == hashed

# Patch both modules so seeding and login use the same scheme
import src.department.database.database as _db_module
_db_module._hash_password = _hash_pw

import src.api.shared.deps as _deps_module
_deps_module.verify_password = _verify_pw

# ── Standard imports (after patches) ─────────────────────────────────────────
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from src.department.database.database import _hash_password
from src.department.database.models import (
    Base, Admin, User,
)

# ── Single shared in-memory engine ───────────────────────────────────────────
# StaticPool + check_same_thread=False ensures every session and the
# TestClient all see the same in-memory database.
TEST_ENGINE = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

# Enable foreign keys for SQLite
@event.listens_for(TEST_ENGINE, "connect")
def _sqlite_pragmas(dbapi_conn, _):
    dbapi_conn.execute("PRAGMA foreign_keys=ON")

TestSessionLocal = sessionmaker(bind=TEST_ENGINE, autocommit=False, autoflush=False)


def _seed_db(session):
    session.add(Admin(
        username="admin",
        email="admin@koisk.local",
        full_name="Super Admin",
        hashed_password=_hash_pw("Admin@1234"),
        role="super_admin",
        department=None,
        is_active=True,
    ))
    session.add(Admin(
        username="water_admin",
        email="water@koisk.local",
        full_name="Water Admin",
        hashed_password=_hash_pw("Water@1234"),
        role="department_admin",
        department="water",
        is_active=True,
    ))
    session.add(User(
        username="test_user_001",
        email="test@koisk.local",
        full_name="Test Citizen",
        phone_number="+919999000001",
        hashed_password=_hash_pw("Citizen@1234"),
        is_active=True,
    ))
    session.commit()


@pytest.fixture(scope="session", autouse=True)
def _create_tables():
    """Create all tables once and seed them. Shared across the full session."""
    Base.metadata.create_all(bind=TEST_ENGINE)
    s = TestSessionLocal()
    _seed_db(s)
    s.close()
    yield
    Base.metadata.drop_all(bind=TEST_ENGINE)


@pytest.fixture()
def db_session():
    """Per-test DB session. Changes are visible within the test, not after."""
    session = TestSessionLocal()
    yield session
    session.close()


@pytest.fixture(scope="session")
def client(_create_tables):
    """
    FastAPI TestClient wired to TEST_ENGINE via dependency override.
    scope=session so the same client is reused — avoids re-creating tables.
    """
    from main import app
    from src.department.database.database import get_db

    def _override_get_db():
        session = TestSessionLocal()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture(scope="session")
def admin_token(client):
    r = client.post("/admin/login", data={"username": "admin", "password": "Admin@1234"})
    assert r.status_code == 200, f"Admin login failed: {r.text}"
    return r.json()["access_token"]


@pytest.fixture(scope="session")
def dept_token(client):
    r = client.post("/admin/login", data={"username": "water_admin", "password": "Water@1234"})
    assert r.status_code == 200, f"Dept admin login failed: {r.text}"
    return r.json()["access_token"]


def crack_otp(session_id: int) -> str | None:
    """
    Brute-force the 6-digit OTP by SHA-256 matching against the DB.
    Uses TEST_ENGINE directly — guaranteed to see the same in-memory DB
    as the TestClient via StaticPool.
    Test-only. Never called from production code.
    """
    from src.department.database.models import KioskSession
    session = TestSessionLocal()
    try:
        row = session.query(KioskSession).filter(KioskSession.id == session_id).first()
        if not row:
            return None
        stored = row.otp_code
        for n in range(1_000_000):
            candidate = f"{n:06d}"
            if hashlib.sha256(candidate.encode()).hexdigest() == stored:
                return candidate
        return None
    finally:
        session.close()
