"""Order repository — orders and order_items writes/reads."""

from decimal import Decimal
from typing import Any, Optional

from app.repositories.base_repository import MySQLBaseRepository

_ORDER_FIELDS = "id, customer_name, total_price, status, created_at, updated_at"


class InsufficientStockError(Exception):
    """Raised when an atomic stock decrement matches no rows."""

    def __init__(self, menu_item_id: int):
        self.menu_item_id = menu_item_id
        super().__init__(f"Not enough stock for menu item {menu_item_id}")


def _parse_money(row: dict[str, Any], *fields: str) -> dict[str, Any]:
    for field in fields:
        value = row.get(field)
        if isinstance(value, Decimal):
            row[field] = float(value)
    return row


class OrderRepository(MySQLBaseRepository):
    """Repository for orders and order_items tables."""

    def create_order_with_items(
        self,
        customer_name: str,
        total_price: float,
        items: list[dict[str, Any]],
    ) -> int:
        """
        Decrement stock, insert the order header, and insert line items
        in a single transaction.
        """
        with self._transaction() as (_conn, cursor):
            for item in items:
                cursor.execute(
                    """
                    UPDATE menu_items
                    SET available_stock = available_stock - %s
                    WHERE id = %s AND available_stock >= %s
                    """,
                    (item["quantity"], item["menu_item_id"], item["quantity"]),
                )
                if cursor.rowcount == 0:
                    raise InsufficientStockError(item["menu_item_id"])

            cursor.execute(
                """
                INSERT INTO orders (customer_name, total_price, status)
                VALUES (%s, %s, %s)
                """,
                (customer_name, total_price, "PLACED"),
            )
            order_id = cursor.lastrowid

            for item in items:
                cursor.execute(
                    """
                    INSERT INTO order_items (
                        order_id, menu_item_id, quantity, price_per_unit
                    )
                    VALUES (%s, %s, %s, %s)
                    """,
                    (
                        order_id,
                        item["menu_item_id"],
                        item["quantity"],
                        item["price_per_unit"],
                    ),
                )

            return order_id

    def get_by_id(self, order_id: int) -> Optional[dict[str, Any]]:
        query = f"SELECT {_ORDER_FIELDS} FROM orders WHERE id = %s"
        row = self._execute_query(query, (order_id,), fetch_one=True)
        return _parse_money(row, "total_price") if row else None

    def list_orders(self, limit: int, offset: int) -> list[dict[str, Any]]:
        query = f"""
            SELECT {_ORDER_FIELDS}
            FROM orders
            ORDER BY id DESC
            LIMIT %s OFFSET %s
        """
        rows = self._execute_query(query, (limit, offset))
        return [_parse_money(row, "total_price") for row in rows]

    def count_orders(self) -> int:
        return self._count("orders")

    def list_items(self, order_id: int) -> list[dict[str, Any]]:
        query = """
            SELECT
                oi.id,
                oi.order_id,
                oi.menu_item_id,
                mi.name AS menu_item_name,
                oi.quantity,
                oi.price_per_unit
            FROM order_items oi
            JOIN menu_items mi ON mi.id = oi.menu_item_id
            WHERE oi.order_id = %s
            ORDER BY oi.id ASC
        """
        rows = self._execute_query(query, (order_id,))
        return [_parse_money(row, "price_per_unit") for row in rows]
