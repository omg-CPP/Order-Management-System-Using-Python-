"""Health and readiness checks — infrastructure status via the service layer."""

from typing import Any

from app.repositories.db_pool import get_db_pool


class HealthService:
    """Service for liveness and readiness responses."""

    def get_root_status(self) -> dict[str, Any]:
        """Basic liveness payload for the API root — no sensitive info."""
        return {
            "name": "Order Management System API",
            "status": "ok",
        }

    def get_health(self) -> dict[str, Any]:
        """Public health check — only returns status, no infrastructure details."""
        pool = get_db_pool()
        return {
            "status": "healthy" if pool.is_available else "degraded",
        }
