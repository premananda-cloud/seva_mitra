# src/database/database.py
"""
Database Configuration
SQLAlchemy setup and session management
"""

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
import os
from .models import Base

# Get database URL from environment
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://koisk_user:koisk_password@localhost:5432/koisk_db"
)

# Use SQLite for development if needed
if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
else:
    # PostgreSQL
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,
        pool_size=10,
        max_overflow=20,
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Session:
    """Get database session for dependency injection"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initialize database tables"""
    Base.metadata.create_all(bind=engine)
    print("Database tables initialized successfully!")


def drop_db():
    """Drop all tables (for development only!)"""
    Base.metadata.drop_all(bind=engine)
    print("Database tables dropped successfully!")


# Event listeners for connection management
if not DATABASE_URL.startswith("sqlite"):
    @event.listens_for(engine, "connect")
    def receive_connect(dbapi_conn, connection_record):
        """Configure PostgreSQL connection"""
        # Enable psycopg2 extensions if available
        try:
            cursor = dbapi_conn.cursor()
            cursor.execute("CREATE SCHEMA IF NOT EXISTS public")
            cursor.commit()
            cursor.close()
        except Exception as e:
            print(f"Warning: Could not set up schema: {e}")
