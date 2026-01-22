from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session, joinedload

from app.api.deps import get_current_active_user
from app.db.base import get_db
from app.models.comment import Comment
from app.models.content import Content, ContentStatus
from app.models.user import User
from app.schemas.comment import CommentCreate, CommentList, CommentResponse
from app.utils.pagination import paginate_query

router = APIRouter(prefix="/public", tags=["Public Comments"])


@router.get("/content/{content_id}/comments", response_model=CommentList)
def get_content_comments(
    content_id: int,
    db: Annotated[Session, Depends(get_db)],
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100)
) -> dict:
    """Get comments for published content.
    
    Args:
        content_id: Content ID
        db: Database session
        skip: Number of items to skip
        limit: Maximum number of items to return
        
    Returns:
        Paginated list of comments
        
    Raises:
        HTTPException: If content not found or not published
    """
    # Verify content exists and is published
    content = db.query(Content).filter(
        Content.id == content_id,
        Content.status == ContentStatus.PUBLISHED
    ).first()
    
    if not content:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Content not found"
        )
    
    # Get top-level comments (not replies)
    query = db.query(Comment).filter(
        Comment.content_id == content_id,
        Comment.parent_id.is_(None),
        Comment.is_deleted == False
    ).options(
        joinedload(Comment.user),
        joinedload(Comment.replies)
    ).order_by(Comment.created_at.desc())
    
    items, total = paginate_query(query, skip, limit)
    
    return {
        "items": items,
        "total": total
    }


@router.post("/content/{content_id}/comments", response_model=CommentResponse, status_code=status.HTTP_201_CREATED)
def create_comment(
    content_id: int,
    comment_data: CommentCreate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)]
) -> Comment:
    """Create a comment on published content.
    
    Args:
        content_id: Content ID
        comment_data: Comment data
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Created comment
        
    Raises:
        HTTPException: If content not found or not published
    """
    # Verify content exists and is published
    content = db.query(Content).filter(
        Content.id == content_id,
        Content.status == ContentStatus.PUBLISHED
    ).first()
    
    if not content:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Content not found"
        )
    
    # Create comment
    comment = Comment(
        content=comment_data.content,
        user_id=current_user.id,
        content_id=content_id,
        parent_id=comment_data.parent_id
    )
    
    db.add(comment)
    db.commit()
    db.refresh(comment)
    
    return comment


@router.post("/comments/{comment_id}/reply", response_model=CommentResponse, status_code=status.HTTP_201_CREATED)
def reply_to_comment(
    comment_id: int,
    reply_data: CommentCreate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)]
) -> Comment:
    """Reply to a comment.
    
    Args:
        comment_id: Parent comment ID
        reply_data: Reply data
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Created reply
        
    Raises:
        HTTPException: If parent comment not found
    """
    # Verify parent comment exists
    parent_comment = db.query(Comment).filter(
        Comment.id == comment_id,
        Comment.is_deleted == False
    ).first()
    
    if not parent_comment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Comment not found"
        )
    
    # Create reply
    reply = Comment(
        content=reply_data.content,
        user_id=current_user.id,
        content_id=parent_comment.content_id,
        parent_id=comment_id
    )
    
    db.add(reply)
    db.commit()
    db.refresh(reply)
    
    return reply
