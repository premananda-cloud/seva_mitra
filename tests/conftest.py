"""
tests/conftest.py
=================
Shared pytest fixtures for KOISK unit and integration tests.
Works on machines with working bcrypt AND broken/missing bcrypt.
"""

import os
import hashlib
import tempfile

# ── Temp file DB ──────────────────────────────────────────────────────────────
_DB_FILE = os.path.join(tempfile.gettempdir(), "koisk_test.db")
try:
    os.remove(_DB_FILE)
except OSError:
    pass

os.environ["DATABASE_URL"] = f"sqlite:///{_DB_FILE}"
os.environ["MOCK_PAYMENT"] = "true"

# ── Determine which hasher to use ─────────────────────────────────────────────
# Try bcrypt for real. If it crashes at hash time, fall back to SHA-256.
# This is tested with a real hash call, not just an import check.
def _try_bcrypt_hash(plain: str):
    from passlib.context import CryptContext
    ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")
    return ctx.hash(plain)  # raises if bcrypt is broken

def _try_bcrypt_verify(plain: str, hashed: str) -> bool:
    from passlib.context import CryptContext
    ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")
    return ctx.verify(plain, hashed)

try:
    _test_hash = _try_bcrypt_hash("test")
    assert _try_bcrypt_verify("test", _test_hash)
    _BCRYPT_OK = True
except Exception:
    _BCRYPT_OK = False

def _hash_pw(plain: str) -> str:
    if _BCRYPT_OK:
        return _try_bcrypt_hash(plain)
    return hashlib.sha256(plain.encode()).hexdigest()

def _verify_pw(plain: str, hashed: str) -> bool:
    if _BCRYPT_OK:
        try:
            return _try_bcrypt_verify(plain, hashed)
        except Exception:
            return False
    return hashlib.sha256(plain.encode()).hexdigest() == hashed

# ── Patch app modules ─────────────────────────────────────────────────────────
import src.department.database.database as _db_module
_db_module._hash_password = _hash_pw

import src.api.shared.deps as _deps_module
_deps_module.verify_password = _verify_pw

class _PwdCtx:
    def verify(self, plain, hashed): return _verify_pw(plain, hashed)
    def hash(self, plain): return _hash_pw(plain)

_deps_module._pwd = _PwdCtx()

# ── Standard imports ──────────────────────────────────────────────────────────
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

from src.department.database.models import Base, Admin, User

# ── Single shared engine ──────────────────────────────────────────────────────
TEST_ENGINE = create_engine(
    f"sqlite:///{_DB_FILE}",
    connect_args={"check_same_thread": False},
)

@event.listens_for(TEST_ENGINE, "connect")
def _pragmas(conn, _):
    conn.execute("PRAGMA foreign_keys=ON")

TestSessionLocal = sessionmaker(bind=TEST_ENGINE, autocommit=False, autoflush=False)

# ── Redirect the app's engine to TEST_ENGINE ──────────────────────────────────
_db_module.engine = TEST_ENGINE
_db_module.SessionLocal = TestSessionLocal


def _seed_db(session):
    session.add(Admin(
        username="admin", email="admin@koisk.local", full_name="Super Admin",
        hashed_password=_hash_pw("Admin@1234"),
        role="super_admin", department=None, is_active=True,
    ))
    session.add(Admin(
        username="water_admin", email="water@koisk.local", full_name="Water Admin",
        hashed_password=_hash_pw("Water@1234"),
        role="department_admin", department="water", is_active=True,
    ))
    session.add(User(
        username="test_user_001", email="test@koisk.local", full_name="Test Citizen",
        phone_number="+919999000001", hashed_password=_hash_pw("Citizen@1234"),
        is_active=True,
    ))
    session.commit()


@pytest.fixture(scope="session", autouse=True)
def _create_tables():
    Base.metadata.create_all(bind=TEST_ENGINE)
    s = TestSessionLocal()
    _seed_db(s)
    s.close()
    yield
    Base.metadata.drop_all(bind=TEST_ENGINE)
    try:
        os.remove(_DB_FILE)
    except OSError:
        pass


@pytest.fixture()
def db_session():
    session = TestSessionLocal()
    yield session
    session.close()


@pytest.fixture(scope="session")
def client(_create_tables):
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
    """Brute-force 6-digit OTP from the test DB. Test-only."""
    from src.department.database.models import KioskSession
    session = TestSessionLocal()
    try:
        row = session.query(KioskSession).filter(KioskSession.id == session_id).first()
        if not row:
            return None
        for n in range(1_000_000):
            candidate = f"{n:06d}"
            if hashlib.sha256(candidate.encode()).hexdigest() == row.otp_code:
                return candidate
        return None
    finally:
        session.close()
