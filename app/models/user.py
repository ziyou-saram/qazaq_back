import enum
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, Enum, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.content import Content
    from app.models.comment import Comment
    from app.models.like import Like
    from app.models.bookmark import Bookmark
    from app.models.subscription import Subscription
    from app.models.media import Media


class UserRole(str, enum.Enum):
    """User role enumeration."""
    USER = "user"
    EDITOR = "editor"
    CHIEF_EDITOR = "chief_editor"
    PUBLISHING_EDITOR = "publishing_editor"
    MODERATOR = "moderator"
    ADMIN = "admin"


class User(Base):
    """User model for authentication and authorization."""
    
    __tablename__ = "users"
    
    # Primary fields
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    
    # Profile fields
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    bio: Mapped[str | None] = mapped_column(Text, nullable=True)
    avatar_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    
    # Role and status
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, native_enum=False, length=50),
        default=UserRole.USER,
        nullable=False
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    
    # Relationships
    authored_content: Mapped[list["Content"]] = relationship(
        "Content",
        back_populates="author",
        foreign_keys="Content.author_id"
    )
    comments: Mapped[list["Comment"]] = relationship(
        "Comment",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    likes: Mapped[list["Like"]] = relationship(
        "Like",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    bookmarks: Mapped[list["Bookmark"]] = relationship(
        "Bookmark",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    
    # Subscriptions (as subscriber)
    subscriptions: Mapped[list["Subscription"]] = relationship(
        "Subscription",
        foreign_keys="Subscription.subscriber_id",
        back_populates="subscriber",
        cascade="all, delete-orphan"
    )
    
    # Subscribers (as author being followed)
    subscribers: Mapped[list["Subscription"]] = relationship(
        "Subscription",
        foreign_keys="Subscription.author_id",
        back_populates="author",
        cascade="all, delete-orphan"
    )
    
    uploaded_media: Mapped[list["Media"]] = relationship(
        "Media",
        back_populates="uploaded_by_user",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self) -> str:
        return f"<User(id={self.id}, username='{self.username}', role='{self.role}')>"
