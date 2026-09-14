"""Order endpoints."""

from fastapi import APIRouter, Path, Query, status

from app.models.order import OrderResponse, PlaceOrderRequest, PlaceOrderResponse
from app.services.order_service import OrderService
from app.utils.response import PaginatedResponse

router = APIRouter(prefix="/orders", tags=["Orders"])


@router.post(
    "",
    response_model=PlaceOrderResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Place an order",
    description=(
        "Validate each line against the catalog and available stock, "
        "compute the total, persist the order, and decrement stock in one transaction."
    ),
    responses={
        201: {
            "description": "Order created",
            "content": {
                "application/json": {
                    "examples": {
                        "success": {
                            "summary": "Order placed",
                            "value": {
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
                                "message": "Order placed successfully",
                            },
                        }
                    }
                }
            },
        },
        400: {"description": "Unknown menu item or not enough stock"},
    },
)
async def place_order(payload: PlaceOrderRequest):
    service = OrderService()
    return service.place_order(
        customer_name=payload.customer_name,
        items=[item.model_dump() for item in payload.items],
    )


@router.get(
    "",
    response_model=PaginatedResponse[OrderResponse],
    summary="List orders",
    description="Return orders newest first, with pagination metadata.",
)
async def list_orders(
    page: int = Query(1, ge=1, description="1-indexed page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
):
    service = OrderService()
    return service.list_orders(page=page, page_size=page_size)


@router.get(
    "/{order_id}",
    response_model=OrderResponse,
    summary="Get an order",
    description="Return one order header and its line items.",
    responses={404: {"description": "Order not found"}},
)
async def get_order(
    order_id: int = Path(..., ge=1, description="Order ID"),
):
    service = OrderService()
    return service.get_order(order_id)
