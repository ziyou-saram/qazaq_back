from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models.user import UserRole


# Base schemas
class UserBase(BaseModel):
    """Base user schema."""
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)


# Request schemas
class UserCreate(UserBase):
    """Schema for user registration."""
    password: str = Field(..., min_length=8, max_length=100)
    role: UserRole | None = None


class UserLogin(BaseModel):
    """Schema for user login."""
    email: EmailStr
    password: str


class UserUpdate(BaseModel):
    """Schema for updating user profile."""
    first_name: str | None = Field(None, min_length=1, max_length=100)
    last_name: str | None = Field(None, min_length=1, max_length=100)
    bio: str | None = Field(None, max_length=1000)
    avatar_url: str | None = None


class UserRoleUpdate(BaseModel):
    """Schema for updating user role (admin only)."""
    role: UserRole


class UserStatusUpdate(BaseModel):
    """Schema for updating user status (admin only)."""
    is_active: bool


# Response schemas
class UserResponse(UserBase):
    """Schema for user response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    role: UserRole
    bio: str | None = None
    avatar_url: str | None = None
    is_active: bool
    created_at: datetime


class UserPublicProfile(BaseModel):
    """Schema for public user profile."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    username: str
    first_name: str
    last_name: str
    bio: str | None = None
    avatar_url: str | None = None
    created_at: datetime


# Token schemas
class Token(BaseModel):
    """Schema for authentication tokens."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenRefresh(BaseModel):
    """Schema for refreshing access token."""
    refresh_token: str


class TokenResponse(BaseModel):
    """Schema for token response."""
    access_token: str
    token_type: str = "bearer"
