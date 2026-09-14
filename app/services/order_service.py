"""Order placement and lookup — business rules live here."""

from typing import Any, Optional

from fastapi import HTTPException, status

from app.repositories.menu_repository import MenuItemRepository
from app.repositories.order_repository import InsufficientStockError, OrderRepository
from app.utils.response import PaginatedResponse, paginate_query_params


class OrderService:
    """Service for placing and reading orders."""

    def __init__(
        self,
        menu_repo: Optional[MenuItemRepository] = None,
        order_repo: Optional[OrderRepository] = None,
    ):
        self.menu_repo = menu_repo or MenuItemRepository()
        self.order_repo = order_repo or OrderRepository()

    def place_order(self, customer_name: str, items: list[dict[str, Any]]) -> dict[str, Any]:
        """
        Validate catalog + stock, compute the total, then persist the order
        and decrement stock in one transaction.
        """
        total_price = 0.0
        prepared_items: list[dict[str, Any]] = []

        for item in items:
            menu_item_id = item["menu_item_id"]
            quantity = item["quantity"]

            menu_item = self.menu_repo.get_by_id(menu_item_id)
            if menu_item is None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Menu item does not exist",
                )

            if menu_item["available_stock"] < quantity:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Not enough stock",
                )

            unit_price = float(menu_item["price"])
            total_price += unit_price * quantity
            prepared_items.append(
                {
                    "menu_item_id": menu_item_id,
                    "quantity": quantity,
                    "price_per_unit": unit_price,
                    "menu_item_name": menu_item["name"],
                }
            )

        try:
            order_id = self.order_repo.create_order_with_items(
                customer_name=customer_name,
                total_price=total_price,
                items=prepared_items,
            )
        except InsufficientStockError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Not enough stock",
            ) from None

        return {
            "id": order_id,
            "customer_name": customer_name,
            "total_price": total_price,
            "status": "PLACED",
            "items": [
                {
                    "menu_item_id": item["menu_item_id"],
                    "menu_item_name": item["menu_item_name"],
                    "quantity": item["quantity"],
                    "price_per_unit": item["price_per_unit"],
                }
                for item in prepared_items
            ],
            "message": "Order placed successfully",
        }

    def get_order(self, order_id: int) -> dict[str, Any]:
        order = self.order_repo.get_by_id(order_id)
        if order is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Order not found",
            )
        order["items"] = self.order_repo.list_items(order_id)
        return order

    def list_orders(self, page: int = 1, page_size: int = 20) -> PaginatedResponse[dict[str, Any]]:
        limit, offset = paginate_query_params(page, page_size)
        orders = self.order_repo.list_orders(limit, offset)
        for order in orders:
            order["items"] = self.order_repo.list_items(order["id"])
        total_items = self.order_repo.count_orders()
        return PaginatedResponse.create(
            items=orders,
            page=page,
            page_size=limit,
            total_items=total_items,
        )
