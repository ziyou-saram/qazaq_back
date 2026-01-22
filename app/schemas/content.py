from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.content import ContentStatus, ContentType
from app.schemas.user import UserPublicProfile


# Base schemas
class ContentBase(BaseModel):
    """Base content schema."""
    title: str = Field(..., min_length=1, max_length=500)
    content: str = Field(..., min_length=1)
    excerpt: str | None = Field(None, max_length=500)
    type: ContentType
    category_id: int | None = None
    cover_image_url: str | None = None


# Request schemas
class ContentCreate(ContentBase):
    """Schema for creating content."""
    pass


class ContentUpdate(BaseModel):
    """Schema for updating content."""
    title: str | None = Field(None, min_length=1, max_length=500)
    content: str | None = Field(None, min_length=1)
    excerpt: str | None = Field(None, max_length=500)
    category_id: int | None = None
    cover_image_url: str | None = None


class ContentStatusUpdate(BaseModel):
    """Schema for updating content status."""
    status: ContentStatus


class ContentPublish(BaseModel):
    """Schema for publishing content."""
    scheduled_publish_at: datetime | None = None


class RevisionRequest(BaseModel):
    """Schema for requesting content revision."""
    comment: str = Field(..., min_length=1, max_length=1000)


# Response schemas
class ContentResponse(ContentBase):
    """Schema for content response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    slug: str
    status: ContentStatus
    author_id: int
    author: UserPublicProfile
    view_count: int
    published_at: datetime | None
    created_at: datetime
    updated_at: datetime
    
    # Computed fields
    likes_count: int = 0
    comments_count: int = 0


class ContentListItem(BaseModel):
    """Schema for content list item (lighter version)."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    title: str
    slug: str
    excerpt: str | None
    type: ContentType
    status: ContentStatus
    cover_image_url: str | None
    author: UserPublicProfile
    view_count: int
    published_at: datetime | None
    created_at: datetime
    
    # Computed fields
    likes_count: int = 0
    comments_count: int = 0


class ContentList(BaseModel):
    """Schema for paginated content list."""
    items: list[ContentListItem]
    total: int
    skip: int
    limit: int


class RevisionResponse(BaseModel):
    """Schema for revision response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    content_id: int
    editor_id: int
    comment: str
    created_at: datetime
