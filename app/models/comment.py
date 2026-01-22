from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.content import Content


class Comment(Base):
    """Comment model for user comments on content."""
    
    __tablename__ = "comments"
    
    # Primary fields
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    
    # Foreign keys
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    content_id: Mapped[int] = mapped_column(
        ForeignKey("content.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Nested comments support (replies)
    parent_id: Mapped[int | None] = mapped_column(
        ForeignKey("comments.id", ondelete="CASCADE"),
        nullable=True,
        index=True
    )
    
    # Soft delete
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="comments")
    content_item: Mapped["Content"] = relationship("Content", back_populates="comments")
    
    parent: Mapped["Comment | None"] = relationship(
        "Comment",
        remote_side=[id],
        back_populates="replies"
    )
    replies: Mapped[list["Comment"]] = relationship(
        "Comment",
        back_populates="parent",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self) -> str:
        return f"<Comment(id={self.id}, user_id={self.user_id}, content_id={self.content_id})>"
