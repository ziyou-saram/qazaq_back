from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.user import User


class Subscription(Base):
    """Subscription model for following authors."""
    
    __tablename__ = "subscriptions"
    __table_args__ = (
        UniqueConstraint("subscriber_id", "author_id", name="unique_subscriber_author"),
    )
    
    # Primary fields
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    
    # Foreign keys
    subscriber_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    author_id: Mapped[int] = mapped_column(
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
    subscriber: Mapped["User"] = relationship(
        "User",
        foreign_keys=[subscriber_id],
        back_populates="subscriptions"
    )
    author: Mapped["User"] = relationship(
        "User",
        foreign_keys=[author_id],
        back_populates="subscribers"
    )
    
    def __repr__(self) -> str:
        return f"<Subscription(id={self.id}, subscriber_id={self.subscriber_id}, author_id={self.author_id})>"
