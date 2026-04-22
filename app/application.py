"""FastAPI application factory."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi
from fastapi.responses import ORJSONResponse
from fastapi.middleware.cors import CORSMiddleware
from structlog.contextvars import bind_contextvars

from app.router import api_router
from config.logging import logger
from config.settings import settings
from global_utils.web_app import run_on_startup, run_on_shutdown


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler for startup and shutdown."""
    # Startup
    bind_contextvars(
        operation="application_startup",
        component="application_lifecycle",
        event_type="startup"
    )
    logger.info("🚀 Starting Medical Triage API server...")

    try:
        await run_on_startup()
        logger.info("✅ Server startup successful")
    except Exception as e:
        logger.error(f"❌ Startup failed: {e}")
        raise

    yield  # Server is running

    # Shutdown
    bind_contextvars(
        operation="application_shutdown",
        component="application_lifecycle",
        event_type="shutdown"
    )
    logger.info("🔒 Shutting down Medical Triage API server...")

    try:
        await run_on_shutdown()
        logger.info("✅ Server shutdown successful")
    except Exception as e:
        logger.error(f"❌ Shutdown failed: {e}")


def get_app() -> FastAPI:
    """Create and configure the FastAPI application.
    
    Returns:
        Configured FastAPI application instance
    """
    app = FastAPI(
        debug=settings.debug,
        title="Medical Triage Assistant API",
        version="1.0.0",
        description="AI-powered medical triage system with multi-agent workflow",
        default_response_class=ORJSONResponse,
        lifespan=lifespan,
        openapi_url="/swagger.json",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost",
            "http://localhost:3000",
            "http://localhost:5173",
            "http://127.0.0.1",
            "http://127.0.0.1:3000",
            "http://127.0.0.1:5173",
            settings.frontend_url,
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include routers
    app.include_router(api_router)

    # Custom OpenAPI schema
    def custom_openapi():
        if app.openapi_schema:
            return app.openapi_schema
        
        openapi_schema = get_openapi(
            title=app.title,
            version=app.version,
            description=app.description,
            routes=app.routes,
        )
        app.openapi_schema = openapi_schema
        return app.openapi_schema

    app.openapi = custom_openapi

    return app

