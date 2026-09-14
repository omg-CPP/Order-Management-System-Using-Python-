"""Menu item repository — reads from menu_items."""

from decimal import Decimal
from typing import Any, Optional

from app.repositories.base_repository import MySQLBaseRepository

_SELECT_FIELDS = "id, name, price, available_stock, created_at, updated_at"


def _parse_menu_item(row: Optional[dict[str, Any]]) -> Optional[dict[str, Any]]:
    if row is None:
        return None
    price = row.get("price")
    if isinstance(price, Decimal):
        row["price"] = float(price)
    return row


class MenuItemRepository(MySQLBaseRepository):
    """Repository for the menu_items table."""

    def list_all(self) -> list[dict[str, Any]]:
        query = f"SELECT {_SELECT_FIELDS} FROM menu_items ORDER BY id ASC"
        rows = self._execute_query(query)
        return [_parse_menu_item(row) for row in rows]

    def get_by_id(self, item_id: int) -> Optional[dict[str, Any]]:
        query = f"SELECT {_SELECT_FIELDS} FROM menu_items WHERE id = %s"
        return _parse_menu_item(self._execute_query(query, (item_id,), fetch_one=True))
