from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.content import Content
    from app.models.user import User


class Revision(Base):
    """Revision model for tracking content review history."""
    
    __tablename__ = "revisions"
    
    # Primary fields
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    
    # Foreign keys
    content_id: Mapped[int] = mapped_column(
        ForeignKey("content.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    editor_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Revision comment from chief editor
    comment: Mapped[str] = mapped_column(Text, nullable=False)
    
    # Timestamp
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True
    )
    
    # Relationships
    content: Mapped["Content"] = relationship("Content", back_populates="revisions")
    editor: Mapped["User"] = relationship("User")
    
    def __repr__(self) -> str:
        return f"<Revision(id={self.id}, content_id={self.content_id}, editor_id={self.editor_id})>"
