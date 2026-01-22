from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.content import Content


class Like(Base):
    """Like model for content likes."""
    
    __tablename__ = "likes"
    __table_args__ = (
        UniqueConstraint("user_id", "content_id", name="unique_user_content_like"),
    )
    
    # Primary fields
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    
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
    
    # Timestamp
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="likes")
    content: Mapped["Content"] = relationship("Content", back_populates="likes")
    
    def __repr__(self) -> str:
        return f"<Like(id={self.id}, user_id={self.user_id}, content_id={self.content_id})>"
