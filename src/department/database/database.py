"""
src/department/database/database.py
====================================
SQLAlchemy engine, session factory, and DB initialisation for KOISK.

DATABASE_URL env var controls which backend to use:
  - Default (dev):   sqlite:///./koisk.db
  - Production:      postgresql://user:pass@host:5432/koisk_db

Imported by main.py:
    from src.department.database.database import get_db, init_db
"""

import os
import logging
from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

logger = logging.getLogger(__name__)

# ─── Connection URL ────────────────────────────────────────────────────────────

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./koisk.db")

# ─── Engine configuration ──────────────────────────────────────────────────────

_is_sqlite = DATABASE_URL.startswith("sqlite")

if _is_sqlite:
    # SQLite needs special settings for FastAPI's async context
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},
        # Use StaticPool so every thread shares one in-memory connection
        # (only relevant for sqlite:///:memory: testing)
        poolclass=StaticPool if ":memory:" in DATABASE_URL else None,
        echo=os.getenv("SQL_ECHO", "false").lower() == "true",
    )

    # Enable WAL mode + foreign keys for SQLite
    @event.listens_for(engine, "connect")
    def _sqlite_pragmas(dbapi_conn, _connection_record):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

else:
    # PostgreSQL (production)
    engine = create_engine(
        DATABASE_URL,
        pool_size=int(os.getenv("DB_POOL_SIZE", "10")),
        max_overflow=int(os.getenv("DB_MAX_OVERFLOW", "20")),
        pool_pre_ping=True,       # reconnect on stale connections
        echo=os.getenv("SQL_ECHO", "false").lower() == "true",
    )

# ─── Session factory ──────────────────────────────────────────────────────────

SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,   # avoids lazy-load errors after commit in FastAPI
)


# ─── FastAPI dependency ───────────────────────────────────────────────────────

def get_db():
    """
    Yields a SQLAlchemy Session for use in FastAPI route handlers.

    Usage:
        @app.get("/...")
        def my_route(db: Session = Depends(get_db)):
            ...
    """
    db: Session = SessionLocal()
    try:
        yield db
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


# ─── DB initialisation ────────────────────────────────────────────────────────

def init_db() -> None:
    """
    Create all tables and seed a default super-admin if none exists.
    Called once at FastAPI startup via @app.on_event("startup").
    """
    # Import here to avoid circular imports
    from .models import Base, Admin

    logger.info(f"[DB] Connecting to: {_safe_url(DATABASE_URL)}")
    Base.metadata.create_all(bind=engine)
    logger.info("[DB] Tables created / verified.")

    _seed_default_admin()


def _seed_default_admin() -> None:
    """Insert a default super-admin row on first run (idempotent)."""
    from .models import Admin

    db = SessionLocal()
    try:
        exists = db.query(Admin).filter(Admin.username == "admin").first()
        if exists:
            return

        # Hash the default password (bcrypt if passlib is available)
        default_password = os.getenv("ADMIN_DEFAULT_PASSWORD", "Admin@1234")
        hashed = _hash_password(default_password)

        admin = Admin(
            username="admin",
            email="admin@koisk.local",
            full_name="Super Admin",
            hashed_password=hashed,
            role="super_admin",
            department=None,
            is_active=True,
        )
        db.add(admin)
        db.commit()
        logger.info(
            "[DB] Default super-admin created  username=admin  "
            "password=(from ADMIN_DEFAULT_PASSWORD env or 'Admin@1234')"
        )
    except Exception as exc:
        db.rollback()
        logger.error(f"[DB] Failed to seed default admin: {exc}")
    finally:
        db.close()


def _hash_password(plain: str) -> str:
    """Hash a plaintext password using bcrypt (passlib) or SHA-256 fallback."""
    try:
        from passlib.context import CryptContext
        ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")
        return ctx.hash(plain)
    except ImportError:
        import hashlib
        logger.warning("[DB] passlib not installed — using SHA-256 password hash (dev only)")
        return hashlib.sha256(plain.encode()).hexdigest()


def _safe_url(url: str) -> str:
    """Mask the password in a DB URL for safe logging."""
    try:
        from urllib.parse import urlparse, urlunparse
        parsed = urlparse(url)
        if parsed.password:
            netloc = parsed.netloc.replace(f":{parsed.password}@", ":****@")
            return urlunparse(parsed._replace(netloc=netloc))
    except Exception:
        pass
    return url
