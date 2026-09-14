"""Menu catalog endpoints."""

from fastapi import APIRouter, Path

from app.models.menu import MenuItemResponse
from app.services.menu_service import MenuService

router = APIRouter(prefix="/menu", tags=["Menu"])


@router.get(
    "",
    response_model=list[MenuItemResponse],
    summary="List menu items",
    description="Return the full catalog with current prices and stock. No authentication required.",
)
async def list_menu():
    service = MenuService()
    return service.list_menu()


@router.get(
    "/{item_id}",
    response_model=MenuItemResponse,
    summary="Get a menu item",
    description="Return one catalog item by ID.",
    responses={404: {"description": "Menu item does not exist"}},
)
async def get_menu_item(
    item_id: int = Path(..., ge=1, description="Menu item ID"),
):
    service = MenuService()
    return service.get_menu_item(item_id)
