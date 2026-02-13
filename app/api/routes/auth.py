from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status
from jose import JWTError
from sqlalchemy.orm import Session

from app.api.deps import (
    get_current_active_user,
    get_current_user,
    get_current_user_from_cookie,
)
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    get_password_hash,
    verify_password,
)
from app.db.base import get_db
from app.models.user import User, UserRole
from app.schemas.user import (
    Token,
    TokenRefresh,
    TokenResponse,
    UserCreate,
    UserLogin,
    UserResponse,
)

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED
)
def register(user_data: UserCreate, db: Annotated[Session, Depends(get_db)]) -> User:
    """Register a new user.

    Args:
        user_data: User registration data
        db: Database session

    Returns:
        Created user

    Raises:
        HTTPException: If username or email already exists
    """
    # Check if username exists
    if db.query(User).filter(User.username == user_data.username).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered",
        )

    # Check if email exists
    if db.query(User).filter(User.email == user_data.email).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered"
        )

    role = user_data.role or UserRole.USER
    if role == UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Admin role cannot be assigned during registration",
        )

    # Create user
    user = User(
        username=user_data.username,
        email=user_data.email,
        first_name=user_data.first_name,
        last_name=user_data.last_name,
        hashed_password=get_password_hash(user_data.password),
        role=role,
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return user


@router.post("/login")
def login(
    credentials: UserLogin, response: Response, db: Annotated[Session, Depends(get_db)]
):
    """Login user and return JWT tokens.

    Sets httpOnly cookies for secure authentication and also returns
    tokens in response for backward compatibility.

    Args:
        credentials: User login credentials
        response: FastAPI response object to set cookies
        db: Database session

    Returns:
        User information and tokens

    Raises:
        HTTPException: If credentials are invalid
    """
    # Find user by email
    user = db.query(User).filter(User.email == credentials.email).first()

    if not user or not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="User account is inactive"
        )

    # Create tokens
    access_token = create_access_token(data={"sub": str(user.id)})
    refresh_token = create_refresh_token(data={"sub": str(user.id)})

    # Set httpOnly cookies for CMS
    from app.core.config import settings

    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=settings.COOKIE_SECURE,
        samesite=settings.COOKIE_SAMESITE,
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        domain=settings.COOKIE_DOMAIN or None,
    )

    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=settings.COOKIE_SECURE,
        samesite=settings.COOKIE_SAMESITE,
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
        domain=settings.COOKIE_DOMAIN or None,
    )

    # Return tokens in JSON for backward compatibility (public frontend)
    return {
        "message": "Login successful",
        "user": {
            "id": user.id,
            "email": user.email,
            "username": user.username,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "role": user.role,
        },
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }


@router.post("/refresh", response_model=TokenResponse)
def refresh_token(
    token_data: TokenRefresh, db: Annotated[Session, Depends(get_db)]
) -> dict:
    """Refresh access token using refresh token.

    Args:
        token_data: Refresh token data
        db: Database session

    Returns:
        New access token

    Raises:
        HTTPException: If refresh token is invalid
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = decode_token(token_data.refresh_token)

        # Check token type
        if payload.get("type") != "refresh":
            raise credentials_exception

        user_id: int | None = payload.get("sub")
        if user_id is None:
            raise credentials_exception

    except JWTError:
        raise credentials_exception

    # Verify user exists and is active
    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user or not user.is_active:
        raise credentials_exception

    # Create new access token
    access_token = create_access_token(data={"sub": str(user.id)})

    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=UserResponse)
def get_current_user_info(
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> User:
    """Get current user information.

    Args:
        current_user: Current authenticated user

    Returns:
        Current user data
    """
    return current_user


@router.get("/me/cookie", response_model=UserResponse)
def get_current_user_info_from_cookie(
    current_user: Annotated[User, Depends(get_current_user_from_cookie)],
) -> User:
    """Get current user information (Cookie auth).

    Used by CMS for cookie-based authentication.

    Args:
        current_user: Current authenticated user from cookie

    Returns:
        Current user data
    """
    return current_user


@router.post("/logout")
def logout(response: Response) -> dict:
    """Logout user by clearing httpOnly cookies.

    Args:
        response: FastAPI response object to clear cookies

    Returns:
        Success message
    """
    # Clear httpOnly cookies
    response.delete_cookie(key="access_token")
    response.delete_cookie(key="refresh_token")

    return {"message": "Logout successful"}
