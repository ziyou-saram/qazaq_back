from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.user import User


class Media(Base):
    """Media model for tracking uploaded files."""
    
    __tablename__ = "media"
    
    # Primary fields
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    
    # File information
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    file_type: Mapped[str] = mapped_column(String(100), nullable=False)
    file_size: Mapped[int] = mapped_column(Integer, nullable=False)
    
    # Uploader
    uploaded_by: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
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
    uploaded_by_user: Mapped["User"] = relationship("User", back_populates="uploaded_media")
    
    def __repr__(self) -> str:
        return f"<Media(id={self.id}, filename='{self.filename}', uploaded_by={self.uploaded_by})>"
