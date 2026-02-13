import enum
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.category import Category
    from app.models.comment import Comment
    from app.models.like import Like
    from app.models.bookmark import Bookmark
    from app.models.revision import Revision


class ContentType(str, enum.Enum):
    """Content type enumeration."""

    NEWS = "news"
    ARTICLE = "article"


class ContentStatus(str, enum.Enum):
    """Content workflow status enumeration."""

    DRAFT = "draft"
    IN_REVIEW = "in_review"
    NEEDS_REVISION = "needs_revision"
    APPROVED = "approved"
    PUBLISHED = "published"


class Content(Base):
    """Content model for news and articles."""

    __tablename__ = "content"

    # Primary fields
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    slug: Mapped[str] = mapped_column(
        String(600), unique=True, index=True, nullable=False
    )

    # Content
    content: Mapped[str] = mapped_column(Text, nullable=False)
    excerpt: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Type and status
    type: Mapped[ContentType] = mapped_column(
        Enum(ContentType, native_enum=False, length=20), nullable=False, index=True
    )
    status: Mapped[ContentStatus] = mapped_column(
        Enum(ContentStatus, native_enum=False, length=20),
        default=ContentStatus.DRAFT,
        nullable=False,
        index=True,
    )
    is_pinned: Mapped[bool] = mapped_column(default=False, nullable=False, index=True)

    # Media
    cover_image_url: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Author
    author_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Category
    category_id: Mapped[int | None] = mapped_column(
        ForeignKey("categories.id", ondelete="SET NULL"), nullable=True, index=True
    )

    # Publishing
    published_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, index=True
    )
    scheduled_publish_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Metrics
    view_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    author: Mapped["User"] = relationship(
        "User", back_populates="authored_content", foreign_keys=[author_id]
    )
    category: Mapped["Category | None"] = relationship(
        "Category", back_populates="content_items"
    )
    comments: Mapped[list["Comment"]] = relationship(
        "Comment", back_populates="content_item", cascade="all, delete-orphan"
    )
    likes: Mapped[list["Like"]] = relationship(
        "Like", back_populates="content", cascade="all, delete-orphan"
    )
    bookmarks: Mapped[list["Bookmark"]] = relationship(
        "Bookmark", back_populates="content", cascade="all, delete-orphan"
    )
    revisions: Mapped[list["Revision"]] = relationship(
        "Revision", back_populates="content", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Content(id={self.id}, title='{self.title}', type='{self.type}', status='{self.status}')>"
