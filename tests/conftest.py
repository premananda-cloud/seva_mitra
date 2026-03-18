"""
tests/conftest.py
=================
Shared pytest fixtures for KOISK unit and integration tests.
Portable across all environments.
"""

import os
import hashlib
import tempfile

# ── Temp file DB — avoids all SQLite in-memory connection sharing issues ──────
_DB_FILE = os.path.join(tempfile.gettempdir(), "koisk_test.db")
# Remove stale DB from a previous failed run
try:
    os.remove(_DB_FILE)
except OSError:
    pass

os.environ["DATABASE_URL"] = f"sqlite:///{_DB_FILE}"
os.environ["MOCK_PAYMENT"] = "true"

# ── SHA-256 password helpers ──────────────────────────────────────────────────
# Bypasses bcrypt entirely — consistent across all environments.

def _sha256(plain: str) -> str:
    return hashlib.sha256(plain.encode()).hexdigest()

def _sha256_verify(plain: str, hashed: str) -> bool:
    return _sha256(plain) == hashed

# Patch _hash_password (used when seeding)
import src.department.database.database as _db_module
_db_module._hash_password = _sha256

# Patch verify_password AND the _pwd context object in deps
# (deps.py may call either depending on code path)
import src.api.shared.deps as _deps_module
_deps_module.verify_password = _sha256_verify

class _SHA256Ctx:
    def verify(self, plain, hashed): return _sha256_verify(plain, hashed)
    def hash(self, plain): return _sha256(plain)

_deps_module._pwd = _SHA256Ctx()

# ── Now import app modules (after patches, after DATABASE_URL is set) ─────────
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

from src.department.database.models import Base, Admin, User

# ── Single test engine pointing at the temp file ─────────────────────────────
TEST_ENGINE = create_engine(
    f"sqlite:///{_DB_FILE}",
    connect_args={"check_same_thread": False},
)

@event.listens_for(TEST_ENGINE, "connect")
def _pragmas(conn, _):
    conn.execute("PRAGMA foreign_keys=ON")

TestSessionLocal = sessionmaker(bind=TEST_ENGINE, autocommit=False, autoflush=False)

# ── Redirect the app's own engine to TEST_ENGINE ──────────────────────────────
# init_db() calls create_all(bind=engine) and SessionLocal uses engine.
# We replace both so the app and our tests share exactly one engine object.
_db_module.engine = TEST_ENGINE
_db_module.SessionLocal = TestSessionLocal


def _seed_db(session):
    session.add(Admin(
        username="admin", email="admin@koisk.local", full_name="Super Admin",
        hashed_password=_sha256("Admin@1234"),
        role="super_admin", department=None, is_active=True,
    ))
    session.add(Admin(
        username="water_admin", email="water@koisk.local", full_name="Water Admin",
        hashed_password=_sha256("Water@1234"),
        role="department_admin", department="water", is_active=True,
    ))
    session.add(User(
        username="test_user_001", email="test@koisk.local", full_name="Test Citizen",
        phone_number="+919999000001", hashed_password=_sha256("Citizen@1234"),
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
