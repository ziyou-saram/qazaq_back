from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session, joinedload

from app.api.deps import RequireModerator, get_db
from app.models.comment import Comment
from app.models.user import User
from app.schemas.comment import CommentList, CommentResponse
from app.utils.pagination import paginate_query

router = APIRouter(prefix="/cms/moderator", tags=["CMS - Moderator"])


@router.get("/comments", response_model=CommentList)
def get_all_comments(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, RequireModerator],
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    include_deleted: bool = Query(False)
) -> dict:
    """Get all comments for moderation.
    
    Args:
        db: Database session
        current_user: Current authenticated moderator
        skip: Number of items to skip
        limit: Maximum number of items to return
        include_deleted: Include deleted comments
        
    Returns:
        Paginated list of comments
    """
    query = db.query(Comment).options(
        joinedload(Comment.user)
    ).order_by(Comment.created_at.desc())
    
    if not include_deleted:
        query = query.filter(Comment.is_deleted == False)
    
    items, total = paginate_query(query, skip, limit)
    
    return {
        "items": items,
        "total": total
    }


@router.delete("/comments/{comment_id}")
def delete_comment(
    comment_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, RequireModerator]
) -> dict:
    """Delete (soft delete) a comment.
    
    Args:
        comment_id: Comment ID
        db: Database session
        current_user: Current authenticated moderator
        
    Returns:
        Success message
        
    Raises:
        HTTPException: If comment not found
    """
    comment = db.query(Comment).filter(Comment.id == comment_id).first()
    
    if not comment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Comment not found"
        )
    
    comment.is_deleted = True
    db.commit()
    
    return {"message": "Comment deleted successfully"}


@router.post("/users/{user_id}/block")
def block_user(
    user_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, RequireModerator]
) -> dict:
    """Block a user.
    
    Args:
        user_id: User ID to block
        db: Database session
        current_user: Current authenticated moderator
        
    Returns:
        Success message
        
    Raises:
        HTTPException: If user not found or trying to block self
    """
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot block yourself"
        )
    
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    user.is_active = False
    db.commit()
    
    return {"message": "User blocked successfully"}


@router.post("/users/{user_id}/unblock")
def unblock_user(
    user_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, RequireModerator]
) -> dict:
    """Unblock a user.
    
    Args:
        user_id: User ID to unblock
        db: Database session
        current_user: Current authenticated moderator
        
    Returns:
        Success message
        
    Raises:
        HTTPException: If user not found
    """
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    user.is_active = True
    db.commit()
    
    return {"message": "User unblocked successfully"}
