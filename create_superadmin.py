"""
create_superadmin.py
====================
One-time script to bootstrap the first super admin account.
Run once before starting the server for the first time.

    python create_superadmin.py

Uses the same DATABASE_URL and hashing logic as the main app,
so the account works immediately with the API and admin_app.py.
"""

import os
import sys
import getpass

# ── Allow running from project root without installing the package ─────────────
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.department.database.database import SessionLocal, init_db
from src.department.database.models import Admin

# ── Hash helper (mirrors deps.py — avoids importing the whole app) ────────────
try:
    from passlib.context import CryptContext
    _pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")
    def hash_password(plain: str) -> str:
        return _pwd.hash(plain)
except ImportError:
    print("⚠  passlib not installed — password will be stored in plain text (dev only)")
    def hash_password(plain: str) -> str:  # type: ignore[misc]
        return plain


def prompt(label: str, secret: bool = False, default: str = "") -> str:
    suffix = f" [{default}]" if default else ""
    if secret:
        val = getpass.getpass(f"  {label}{suffix}: ")
    else:
        val = input(f"  {label}{suffix}: ").strip()
    return val or default


def main():
    print("\n╔══════════════════════════════════════╗")
    print("║   KOISK — Create Super Admin         ║")
    print("╚══════════════════════════════════════╝\n")

    init_db()
    db = SessionLocal()

    try:
        existing = db.query(Admin).filter(Admin.role == "super_admin").count()
        if existing:
            print(f"  ℹ  {existing} super admin(s) already exist.")
            cont = input("  Create another? (y/N): ").strip().lower()
            if cont != "y":
                print("  Aborted.\n")
                return

        print("  Fill in the new super admin's details:\n")
        username  = prompt("Username")
        email     = prompt("Email")
        full_name = prompt("Full name")

        while True:
            password = prompt("Password (min 8 chars)", secret=True)
            if len(password) < 8:
                print("  ✗  Password must be at least 8 characters.\n")
                continue
            confirm = prompt("Confirm password", secret=True)
            if password != confirm:
                print("  ✗  Passwords do not match.\n")
                continue
            break

        # Validate uniqueness
        if db.query(Admin).filter(Admin.username == username).first():
            print(f"\n  ✗  Username '{username}' is already taken.\n")
            return
        if db.query(Admin).filter(Admin.email == email).first():
            print(f"\n  ✗  Email '{email}' is already registered.\n")
            return

        admin = Admin(
            username        = username,
            email           = email,
            full_name       = full_name,
            hashed_password = hash_password(password),
            role            = "super_admin",
            department      = None,
            is_active       = True,
        )
        db.add(admin)
        db.commit()
        db.refresh(admin)

        print(f"\n  ✅  Super admin created successfully!")
        print(f"      ID       : {admin.id}")
        print(f"      Username : {admin.username}")
        print(f"      Email    : {admin.email}")
        print(f"      Role     : {admin.role}")
        print()

    except KeyboardInterrupt:
        print("\n\n  Aborted.\n")
    finally:
        db.close()


if __name__ == "__main__":
    main()
