from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import RequireAdmin, get_db
from app.models.user import User
from app.schemas.user import UserResponse, UserRoleUpdate, UserStatusUpdate
from app.utils.pagination import paginate_query

router = APIRouter(prefix="/cms/admin", tags=["CMS - Administrator"])


@router.get("/users", response_model=dict)
def get_all_users(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, RequireAdmin],
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100)
) -> dict:
    """Get all users.
    
    Args:
        db: Database session
        current_user: Current authenticated admin
        skip: Number of items to skip
        limit: Maximum number of items to return
        
    Returns:
        Paginated list of users
    """
    query = db.query(User).order_by(User.created_at.desc())
    items, total = paginate_query(query, skip, limit)
    
    # Convert to UserResponse
    user_responses = [UserResponse.model_validate(user) for user in items]
    
    return {
        "items": user_responses,
        "total": total,
        "skip": skip,
        "limit": limit
    }


@router.get("/users/{user_id}", response_model=UserResponse)
def get_user(
    user_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, RequireAdmin]
) -> User:
    """Get user details.
    
    Args:
        user_id: User ID
        db: Database session
        current_user: Current authenticated admin
        
    Returns:
        User details
        
    Raises:
        HTTPException: If user not found
    """
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return user


@router.put("/users/{user_id}/role")
def update_user_role(
    user_id: int,
    role_data: UserRoleUpdate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, RequireAdmin]
) -> dict:
    """Update user role.
    
    Args:
        user_id: User ID
        role_data: New role data
        db: Database session
        current_user: Current authenticated admin
        
    Returns:
        Success message
        
    Raises:
        HTTPException: If user not found or trying to change own role
    """
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot change your own role"
        )
    
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    user.role = role_data.role
    db.commit()
    
    return {"message": f"User role updated to {role_data.role.value}"}


@router.put("/users/{user_id}/status")
def update_user_status(
    user_id: int,
    status_data: UserStatusUpdate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, RequireAdmin]
) -> dict:
    """Update user active status.
    
    Args:
        user_id: User ID
        status_data: New status data
        db: Database session
        current_user: Current authenticated admin
        
    Returns:
        Success message
        
    Raises:
        HTTPException: If user not found or trying to change own status
    """
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot change your own status"
        )
    
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    user.is_active = status_data.is_active
    db.commit()
    
    status_text = "activated" if status_data.is_active else "deactivated"
    return {"message": f"User {status_text} successfully"}


@router.get("/content", response_model=dict)
def get_all_content(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, RequireAdmin],
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100)
) -> dict:
    """Get all content items (admin view).
    
    Args:
        db: Database session
        current_user: Current authenticated admin
        skip: Number of items to skip
        limit: Maximum number of items to return
        
    Returns:
        Paginated list of content with minimal details
    """
    from app.models.content import Content
    from app.schemas.content import ContentListItem
    
    query = db.query(Content).order_by(Content.created_at.desc())
    items, total = paginate_query(query, skip, limit)
    
    # Convert to ContentListItem manually or via model_validate if schema matches
    content_responses = [ContentListItem.model_validate(item) for item in items]
    
    return {
        "items": content_responses,
        "total": total,
        "skip": skip,
        "limit": limit
    }


@router.delete("/content/{content_id}")
def delete_content(
    content_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, RequireAdmin]
) -> dict:
    """Delete content item (hard delete).
    
    Args:
        content_id: Content ID
        db: Database session
        current_user: Current authenticated admin
        
    Returns:
        Success message
        
    Raises:
        HTTPException: If content not found
    """
    from app.models.content import Content
    
    content = db.query(Content).filter(Content.id == content_id).first()
    
    if not content:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Content not found"
        )
    
    db.delete(content)
    db.commit()
    
    return {"message": "Content deleted successfully"}
