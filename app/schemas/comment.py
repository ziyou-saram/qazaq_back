from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.user import UserPublicProfile


# Request schemas
class CommentCreate(BaseModel):
    """Schema for creating a comment."""
    content: str = Field(..., min_length=1, max_length=2000)
    parent_id: int | None = None


class CommentUpdate(BaseModel):
    """Schema for updating a comment."""
    content: str = Field(..., min_length=1, max_length=2000)


# Response schemas
class CommentResponse(BaseModel):
    """Schema for comment response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    content: str
    user_id: int
    user: UserPublicProfile
    content_id: int
    parent_id: int | None
    is_deleted: bool
    created_at: datetime
    updated_at: datetime
    
    # Nested replies
    replies: list["CommentResponse"] = []


class CommentList(BaseModel):
    """Schema for paginated comment list."""
    items: list[CommentResponse]
    total: int
