"""Standard API response models — flat RESTful responses."""

from typing import Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class PaginationMeta(BaseModel):
    """Pagination metadata for flat paginated responses."""

    page: int = Field(..., ge=1, description="Current page number (1-indexed)", examples=[1])
    page_size: int = Field(..., ge=1, le=100, description="Items per page", examples=[20])
    total_items: int = Field(..., ge=0, description="Total number of items", examples=[100])
    total_pages: int = Field(..., ge=0, description="Total number of pages", examples=[5])
    has_next: bool = Field(..., description="Whether there are more pages")
    has_previous: bool = Field(..., description="Whether there are previous pages")


class PaginatedResponse(BaseModel, Generic[T]):
    """Flat paginated response — items plus pagination metadata."""

    items: list[T] = Field(..., description="List of items for the current page")
    pagination: PaginationMeta = Field(..., description="Pagination metadata")

    @classmethod
    def create(
        cls,
        items: list[T],
        page: int,
        page_size: int,
        total_items: int,
    ) -> "PaginatedResponse[T]":
        """Create a paginated response with computed pagination metadata."""
        total_pages = (total_items + page_size - 1) // page_size if page_size > 0 else 0
        pagination = PaginationMeta(
            page=page,
            page_size=page_size,
            total_items=total_items,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_previous=page > 1,
        )
        return cls(items=items, pagination=pagination)


class ErrorResponse(BaseModel):
    """Standard FastAPI error body used by 4xx/5xx responses."""

    model_config = {
        "json_schema_extra": {
            "example": {"detail": "Not enough stock"},
        }
    }

    detail: str = Field(..., description="Human-readable error message")


def paginate_query_params(page: int = 1, page_size: int = 20) -> tuple[int, int]:
    """Convert 1-indexed page parameters to LIMIT/OFFSET values."""
    page = max(1, page)
    page_size = max(1, min(100, page_size))
    offset = (page - 1) * page_size
    return page_size, offset
