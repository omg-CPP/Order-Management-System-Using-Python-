"""Health-check response models."""

from pydantic import BaseModel, Field


class RootHealthResponse(BaseModel):
    """Liveness payload for GET /."""

    model_config = {
        "json_schema_extra": {
            "example": {
                "name": "Order Management System API",
                "status": "ok",
            }
        }
    }

    name: str = Field(..., description="API display name")
    status: str = Field(..., description="Liveness status")


class HealthResponse(BaseModel):
    """Public health check response — no sensitive infrastructure details."""

    model_config = {
        "json_schema_extra": {
            "example": {
                "status": "healthy",
            }
        }
    }

    status: str = Field(..., description="Overall health status (healthy or degraded)")
