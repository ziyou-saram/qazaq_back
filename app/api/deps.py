from typing import Annotated, Generator

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy.orm import Session

from app.core.security import decode_token
from app.db.base import get_db
from app.models.user import User, UserRole

# Security scheme
security = HTTPBearer()
security_optional = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
    db: Annotated[Session, Depends(get_db)],
) -> User:
    """Get current authenticated user from JWT token.

    Args:
        credentials: HTTP bearer credentials
        db: Database session

    Returns:
        Current user

    Raises:
        HTTPException: If token is invalid or user not found
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        token = credentials.credentials
        payload = decode_token(token)

        # Check token type
        if payload.get("type") != "access":
            raise credentials_exception

        user_id: int | None = payload.get("sub")
        if user_id is None:
            raise credentials_exception

    except JWTError:
        raise credentials_exception

    # Get user from database
    user = db.query(User).filter(User.id == int(user_id)).first()
    if user is None:
        raise credentials_exception

    return user


def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    """Get current active user.

    Args:
        current_user: Current user from token

    Returns:
        Current active user

    Raises:
        HTTPException: If user is inactive
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Inactive user"
        )
    return current_user


def get_current_user_from_cookie(
    request: Request, db: Annotated[Session, Depends(get_db)]
) -> User:
    """Get current authenticated user from httpOnly cookie.

    Used for CMS authentication where cookies are preferred over Bearer tokens.

    Args:
        request: FastAPI request object
        db: Database session

    Returns:
        Current user

    Raises:
        HTTPException: If token is invalid or user not found
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Not authenticated",
    )

    # Get token from cookie
    token = request.cookies.get("access_token")
    if not token:
        raise credentials_exception

    try:
        payload = decode_token(token)

        # Check token type
        if payload.get("type") != "access":
            raise credentials_exception

        user_id: int | None = payload.get("sub")
        if user_id is None:
            raise credentials_exception

    except JWTError:
        raise credentials_exception

    # Get user from database
    user = db.query(User).filter(User.id == int(user_id)).first()
    if user is None or not user.is_active:
        raise credentials_exception

    return user


def get_current_user_unified(
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    token_creds: Annotated[
        HTTPAuthorizationCredentials | None, Depends(security_optional)
    ],
) -> User:
    """Get current user from either Bearer token or Cookie.

    Tries Bearer token first, then falls back to Cookie.

    Args:
        request: FastAPI request
        db: Database session
        token_creds: Bearer credentials (optional)

    Returns:
        Authenticated user

    Raises:
        HTTPException: If authentication fails
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Not authenticated",
    )

    # 1. Try Bearer token
    if token_creds:
        try:
            token = token_creds.credentials
            payload = decode_token(token)

            if payload.get("type") != "access":
                raise credentials_exception

            user_id: int | None = payload.get("sub")
            if user_id is None:
                raise credentials_exception

            user = db.query(User).filter(User.id == int(user_id)).first()
            if user and user.is_active:
                return user

        except (JWTError, ValueError):
            # If token is invalid, don't fallback to cookie?
            # Or should we? Usually if token is provided but invalid, we reject.
            # But here let's be strict: if token provided, it must be valid.
            raise credentials_exception

    # 2. Try Cookie
    try:
        return get_current_user_from_cookie(request, db)
    except HTTPException:
        pass

    # 3. Fail
    raise credentials_exception


def require_role(*allowed_roles: UserRole):
    """Dependency factory for role-based access control.

    Args:
        *allowed_roles: Roles that are allowed to access the endpoint

    Returns:
        Dependency function that checks user role
    """

    def role_checker(
        current_user: Annotated[User, Depends(get_current_user_unified)],
    ) -> User:
        """Check if user has required role.

        Args:
            current_user: Current authenticated user

        Returns:
            Current user if role is allowed

        Raises:
            HTTPException: If user doesn't have required role
        """
        if not current_user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Inactive user"
            )

        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required roles: {', '.join(r.value for r in allowed_roles)}",
            )
        return current_user

    return role_checker


# Common role dependencies
RequireEditor = Depends(
    require_role(
        UserRole.EDITOR,
        UserRole.CHIEF_EDITOR,
        UserRole.PUBLISHING_EDITOR,
        UserRole.ADMIN,
    )
)

RequireChiefEditor = Depends(require_role(UserRole.CHIEF_EDITOR, UserRole.ADMIN))

RequirePublishingEditor = Depends(
    require_role(UserRole.PUBLISHING_EDITOR, UserRole.ADMIN)
)

RequireModerator = Depends(require_role(UserRole.MODERATOR, UserRole.ADMIN))

RequireAdmin = Depends(require_role(UserRole.ADMIN))

RequirePublisherOrChief = Depends(
    require_role(UserRole.PUBLISHING_EDITOR, UserRole.CHIEF_EDITOR, UserRole.ADMIN)
)

RequireCategoryManagement = Depends(
    require_role(
        UserRole.EDITOR,
        UserRole.CHIEF_EDITOR,
        UserRole.PUBLISHING_EDITOR,
        UserRole.MODERATOR,
        UserRole.ADMIN,
    )
)
