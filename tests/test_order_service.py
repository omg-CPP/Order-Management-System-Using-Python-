"""OrderService unit tests using constructor-injected fakes."""

import pytest
from fastapi import HTTPException

from app.repositories.order_repository import InsufficientStockError
from app.services.order_service import OrderService


class FakeMenuRepository:
    def __init__(self, items: dict[int, dict]):
        self.items = items

    def get_by_id(self, item_id: int):
        return self.items.get(item_id)


class FakeOrderRepository:
    def __init__(self, raise_stock: bool = False):
        self.raise_stock = raise_stock
        self.created = None

    def create_order_with_items(self, customer_name, total_price, items):
        if self.raise_stock:
            raise InsufficientStockError(items[0]["menu_item_id"])
        self.created = (customer_name, total_price, items)
        return 42


def _burger_menu():
    return FakeMenuRepository(
        {
            1: {"id": 1, "name": "Burger", "price": 100.0, "available_stock": 10},
        }
    )


def test_place_order_computes_total_and_persists():
    order_repo = FakeOrderRepository()
    service = OrderService(menu_repo=_burger_menu(), order_repo=order_repo)

    result = service.place_order("Rahul", [{"menu_item_id": 1, "quantity": 2}])

    assert result["id"] == 42
    assert result["total_price"] == 200.0
    assert result["status"] == "PLACED"
    assert order_repo.created[0] == "Rahul"
    assert order_repo.created[1] == 200.0


def test_place_order_rejects_unknown_item():
    service = OrderService(menu_repo=_burger_menu(), order_repo=FakeOrderRepository())

    with pytest.raises(HTTPException) as exc:
        service.place_order("Rahul", [{"menu_item_id": 99, "quantity": 1}])

    assert exc.value.status_code == 400
    assert exc.value.detail == "Menu item does not exist"


def test_place_order_rejects_short_stock():
    service = OrderService(menu_repo=_burger_menu(), order_repo=FakeOrderRepository())

    with pytest.raises(HTTPException) as exc:
        service.place_order("Rahul", [{"menu_item_id": 1, "quantity": 50}])

    assert exc.value.status_code == 400
    assert exc.value.detail == "Not enough stock"


def test_place_order_maps_race_stock_error():
    service = OrderService(
        menu_repo=_burger_menu(),
        order_repo=FakeOrderRepository(raise_stock=True),
    )

    with pytest.raises(HTTPException) as exc:
        service.place_order("Rahul", [{"menu_item_id": 1, "quantity": 1}])

    assert exc.value.status_code == 400
    assert exc.value.detail == "Not enough stock"
