"""API router configuration."""

from fastapi import APIRouter
from fastapi.responses import ORJSONResponse

from modules.auth.routes import router as auth_router
from modules.patients.routes import router as patients_router
from modules.triage.routes import router as triage_router
from modules.dashboard.routes import router as dashboard_router
from modules.rag.routes import router as rag_router


# Main API router
api_router = APIRouter()


# Health check endpoints
@api_router.get("/_healthz", include_in_schema=False)
async def healthz():
    """Health check endpoint."""
    return ORJSONResponse(status_code=200, content={"success": True, "status": "healthy"})


@api_router.get("/_readyz", include_in_schema=False)
async def readyz():
    """Readiness check endpoint."""
    return ORJSONResponse(status_code=200, content={"success": True, "status": "ready"})


# API v1 router
api_v1_router = APIRouter(prefix="/api/v1")

# Include module routers
api_v1_router.include_router(auth_router)
api_v1_router.include_router(patients_router)
api_v1_router.include_router(triage_router)
api_v1_router.include_router(dashboard_router)
api_v1_router.include_router(rag_router)

# Add v1 router to main router
api_router.include_router(api_v1_router)

