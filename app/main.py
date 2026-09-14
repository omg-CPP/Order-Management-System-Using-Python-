"""Order Management System API — FastAPI application."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from fastapi.responses import JSONResponse

from app.api.v1 import menu, orders
from app.config import settings
from app.models.health import HealthResponse, RootHealthResponse
from app.repositories.db_pool import close_db_pool, get_db_pool
from app.services.health_service import HealthService
from app.utils.response import ErrorResponse

logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler for startup and shutdown."""
    logger.info("Starting Order Management System API...")
    try:
        get_db_pool()
        logger.info("Database connection pool initialized")
    except Exception as e:
        logger.error("Failed to initialize database pool: %s", e)
        if not settings.ALLOW_DB_FAILURE:
            raise

    yield

    logger.info("Shutting down Order Management System API...")
    close_db_pool()
    logger.info("Database connection pool closed")


API_DESCRIPTION = """Restaurant order API.

Place orders, read the menu, and inspect saved orders. Stock is checked and
decremented in a single MySQL transaction.

Interactive docs (when `DEBUG=true`):

- Swagger UI: `/docs`
- ReDoc: `/redoc`
- OpenAPI JSON: `/openapi.json`
"""

app = FastAPI(
    title="Order Management System API",
    description=API_DESCRIPTION,
    version="1.0.0",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    lifespan=lifespan,
    swagger_ui_parameters={
        "persistAuthorization": True,
        "displayRequestDuration": True,
        "filter": True,
        "docExpansion": "none",
    },
    openapi_tags=[
        {
            "name": "Menu",
            "description": "Catalog of menu items with current price and stock.",
        },
        {
            "name": "Orders",
            "description": (
                "Place an order, list orders, or fetch one order with its line items. "
                "Placement validates stock and writes the header, lines, and stock update atomically."
            ),
        },
        {"name": "Health", "description": "System health and readiness checks."},
    ],
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle uncaught exceptions with a flat error response."""
    logger.exception("Unhandled exception: %s", exc)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )


API_V1_PREFIX = "/api/v1"

app.include_router(menu.router, prefix=API_V1_PREFIX)
app.include_router(orders.router, prefix=API_V1_PREFIX)


@app.get(
    "/",
    tags=["Health"],
    response_model=RootHealthResponse,
    summary="Root health",
    description="Basic liveness check. Returns API name and status only.",
)
async def root():
    return HealthService().get_root_status()


@app.get(
    "/health",
    tags=["Health"],
    response_model=HealthResponse,
    summary="Health check",
    description="Public health check. Returns status only (healthy or degraded).",
)
async def health_check():
    return HealthService().get_health()


def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
        tags=app.openapi_tags,
    )
    schema.setdefault("components", {})
    schema["components"].setdefault("schemas", {})
    schema["components"]["schemas"]["ErrorResponse"] = ErrorResponse.model_json_schema()
    schema["servers"] = [
        {"url": "/", "description": "Current host"},
        {"url": "http://localhost:8000", "description": "Local development"},
    ]

    error_ref = {"$ref": "#/components/schemas/ErrorResponse"}
    for path_item in schema.get("paths", {}).values():
        for operation in path_item.values():
            if not isinstance(operation, dict):
                continue
            responses = operation.setdefault("responses", {})
            responses.setdefault("422", {"description": "Request validation error"})
            responses.setdefault(
                "500",
                {
                    "description": "Unhandled server error",
                    "content": {"application/json": {"schema": error_ref}},
                },
            )

    app.openapi_schema = schema
    return schema


app.openapi = custom_openapi  # type: ignore[method-assign]


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        # Watch app/ only. Watching the whole repo (including venv) causes
        # reload storms on Windows, especially under OneDrive.
        reload_dirs=["app"] if settings.DEBUG else None,
    )
