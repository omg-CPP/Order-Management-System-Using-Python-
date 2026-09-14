"""Menu item request/response models."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class MenuItemResponse(BaseModel):
    """A catalog item with current stock."""

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "id": 1,
                    "name": "Burger",
                    "price": 100.0,
                    "available_stock": 10,
                    "created_at": "2026-09-14T14:30:00",
                    "updated_at": "2026-09-14T14:30:00",
                }
            ]
        }
    }

    id: int = Field(..., description="Menu item ID")
    name: str = Field(..., description="Item name")
    price: float = Field(..., description="Unit price")
    available_stock: int = Field(..., description="Units remaining")
    created_at: Optional[datetime] = Field(None, description="Row created timestamp")
    updated_at: Optional[datetime] = Field(None, description="Row updated timestamp")
