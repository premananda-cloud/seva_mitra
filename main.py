"""
main.py
=======
KOISK Unified FastAPI Backend — SUVIDHA 2026
App factory: mounts all routers from src/api/.
/admin/* endpoints are restricted to localhost only.
"""

import logging
import os
from datetime import datetime

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from src.department.database.database import init_db

from src.api.admin.router       import router as admin_router
from src.api.electricity.router  import router as electricity_router
from src.api.water.router        import router as water_router
from src.api.gas.router          import router as gas_router
from src.api.complaints.router   import router as complaints_router
from src.api.municipal.router    import router as municipal_router
from src.api.kiosk.router        import router as kiosk_router
from src.api.payments.router     import router as payments_router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ─── Localhost-only guard for /admin ─────────────────────────────────────────

_ALLOWED_HOSTS = {"127.0.0.1", "::1", "localhost"}

class AdminLocalhostMiddleware(BaseHTTPMiddleware):
    """Block any /admin* request that doesn't come from the local machine."""
    async def dispatch(self, request: Request, call_next):
        if request.url.path.startswith("/admin"):
            client_host = request.client.host if request.client else ""
            if client_host not in _ALLOWED_HOSTS:
                logger.warning(
                    "Blocked admin access attempt from %s → %s",
                    client_host, request.url.path,
                )
                return JSONResponse(
                    status_code=403,
                    content={"detail": "Admin endpoints are only accessible from localhost."},
                )
        return await call_next(request)

# ─── App ─────────────────────────────────────────────────────────────────────

app = FastAPI(
    title="KOISK Utility Services API",
    description="Electricity · Water · Municipal — with mock payment support",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS must be added before the localhost guard so preflight requests
# from the frontend aren't caught by the middleware.
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "http://localhost:5173").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(AdminLocalhostMiddleware)

# ─── Startup ─────────────────────────────────────────────────────────────────

@app.on_event("startup")
def startup():
    init_db()
    logger.info("✅ KOISK API started — admin restricted to localhost")

# ─── Health ──────────────────────────────────────────────────────────────────

@app.get("/health", tags=["Health"])
async def health():
    return {
        "status":       "healthy",
        "timestamp":    datetime.utcnow().isoformat(),
        "mock_payment": os.getenv("MOCK_PAYMENT", "true"),
        "departments":  ["electricity", "water", "gas", "municipal"],
    }

# ─── Routers ─────────────────────────────────────────────────────────────────

app.include_router(admin_router)
app.include_router(electricity_router)
app.include_router(water_router)
app.include_router(gas_router)
app.include_router(complaints_router)
app.include_router(municipal_router)
app.include_router(kiosk_router)
app.include_router(payments_router)
