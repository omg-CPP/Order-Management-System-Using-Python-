"""Menu catalog service."""

from typing import Any, Optional

from fastapi import HTTPException, status

from app.repositories.menu_repository import MenuItemRepository


class MenuService:
    """Service for reading the menu catalog."""

    def __init__(self, menu_repo: Optional[MenuItemRepository] = None):
        self.menu_repo = menu_repo or MenuItemRepository()

    def list_menu(self) -> list[dict[str, Any]]:
        return self.menu_repo.list_all()

    def get_menu_item(self, item_id: int) -> dict[str, Any]:
        item = self.menu_repo.get_by_id(item_id)
        if item is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Menu item does not exist",
            )
        return item
