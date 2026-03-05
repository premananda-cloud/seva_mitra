"""
src/department
==============
KOISK Department Services — top-level package.

Sub-packages:
  electricity  — Electricity_Services.py
  water        — Water_Services_Complete.py
  municipal    — municipal_services.py
  database     — SQLAlchemy engine, session, and ORM models
"""

# Department sub-packages are imported lazily by their own __init__.py files.
# This top-level __init__ intentionally stays lightweight to avoid circular imports.

__all__ = ["electricity", "water", "municipal", "database"]
