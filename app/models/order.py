"""Order request/response models."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class OrderItemRequest(BaseModel):
    """A single line in a place-order request."""

    menu_item_id: int = Field(..., ge=1, description="ID of the menu item", examples=[1])
    quantity: int = Field(..., ge=1, description="Units to order", examples=[2])


class PlaceOrderRequest(BaseModel):
    """Place a customer order."""

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "customer_name": "Rahul",
                    "items": [{"menu_item_id": 1, "quantity": 2}],
                },
                {
                    "customer_name": "Anita",
                    "items": [
                        {"menu_item_id": 1, "quantity": 1},
                        {"menu_item_id": 3, "quantity": 2},
                    ],
                },
            ]
        }
    }

    customer_name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Customer name",
        examples=["Rahul"],
    )
    items: list[OrderItemRequest] = Field(..., min_length=1, description="Line items")

    @field_validator("customer_name", mode="before")
    @classmethod
    def strip_name(cls, value):
        if isinstance(value, str):
            return value.strip()
        return value


class OrderItemResponse(BaseModel):
    """A persisted order line."""

    menu_item_id: int = Field(..., description="Menu item ID")
    menu_item_name: Optional[str] = Field(None, description="Menu item name at read time")
    quantity: int = Field(..., description="Ordered quantity")
    price_per_unit: float = Field(..., description="Unit price captured at order time")


class OrderResponse(BaseModel):
    """Order header returned after create or fetch."""

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "id": 1,
                    "customer_name": "Rahul",
                    "total_price": 200.0,
                    "status": "PLACED",
                    "items": [
                        {
                            "menu_item_id": 1,
                            "menu_item_name": "Burger",
                            "quantity": 2,
                            "price_per_unit": 100.0,
                        }
                    ],
                    "created_at": "2026-09-14T14:30:00",
                    "updated_at": "2026-09-14T14:30:00",
                }
            ]
        }
    }

    id: int = Field(..., description="Order ID")
    customer_name: str = Field(..., description="Customer name")
    total_price: float = Field(..., description="Sum of line totals")
    status: str = Field(..., description="Order status")
    items: list[OrderItemResponse] = Field(default_factory=list, description="Line items")
    created_at: Optional[datetime] = Field(None, description="Created timestamp")
    updated_at: Optional[datetime] = Field(None, description="Updated timestamp")


class PlaceOrderResponse(OrderResponse):
    """Created-order payload with a confirmation message."""

    message: str = Field(
        default="Order placed successfully",
        description="Human-readable result",
    )
