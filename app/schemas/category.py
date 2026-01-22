from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


# Request schemas
class CategoryCreate(BaseModel):
    """Schema for creating a category."""
    name: str = Field(..., min_length=1, max_length=100)
    description: str | None = Field(None, max_length=500)
    parent_id: int | None = None
    order: int = 0


class CategoryUpdate(BaseModel):
    """Schema for updating a category."""
    name: str | None = Field(None, min_length=1, max_length=100)
    description: str | None = Field(None, max_length=500)
    parent_id: int | None = None
    order: int | None = None


# Response schemas
class CategoryResponse(BaseModel):
    """Schema for category response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    name: str
    slug: str
    description: str | None
    parent_id: int | None
    order: int
    created_at: datetime
    
    # Nested children
    children: list["CategoryResponse"] = []


class CategoryList(BaseModel):
    """Schema for category list."""
    items: list[CategoryResponse]
    total: int
