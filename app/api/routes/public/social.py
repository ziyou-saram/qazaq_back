from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_user
from app.db.base import get_db
from app.models.bookmark import Bookmark
from app.models.content import Content, ContentStatus
from app.models.like import Like
from app.models.subscription import Subscription
from app.models.user import User

router = APIRouter(prefix="/public", tags=["Public Social"])


# Likes
@router.get("/content/{content_id}/like/status")
def get_like_status(
    content_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)]
) -> dict:
    """Check if current user liked the content."""
    existing_like = db.query(Like).filter(
        Like.user_id == current_user.id,
        Like.content_id == content_id
    ).first()
    
    return {"liked": existing_like is not None}


@router.post("/content/{content_id}/like", status_code=status.HTTP_201_CREATED)
def like_content(
    content_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)]
) -> dict:
    """Like published content.
    
    Args:
        content_id: Content ID
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Success message
        
    Raises:
        HTTPException: If content not found, not published, or already liked
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
    
    # Check if already liked
    existing_like = db.query(Like).filter(
        Like.user_id == current_user.id,
        Like.content_id == content_id
    ).first()
    
    if existing_like:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Content already liked"
        )
    
    # Create like
    like = Like(user_id=current_user.id, content_id=content_id)
    db.add(like)
    db.commit()
    
    return {"message": "Content liked successfully"}


@router.delete("/content/{content_id}/like")
def unlike_content(
    content_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)]
) -> dict:
    """Unlike content.
    
    Args:
        content_id: Content ID
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Success message
        
    Raises:
        HTTPException: If like not found
    """
    like = db.query(Like).filter(
        Like.user_id == current_user.id,
        Like.content_id == content_id
    ).first()
    
    if not like:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Like not found"
        )
    
    db.delete(like)
    db.commit()
    
    return {"message": "Content unliked successfully"}


# Bookmarks
@router.post("/content/{content_id}/bookmark", status_code=status.HTTP_201_CREATED)
def bookmark_content(
    content_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)]
) -> dict:
    """Bookmark published content.
    
    Args:
        content_id: Content ID
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Success message
        
    Raises:
        HTTPException: If content not found, not published, or already bookmarked
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
    
    # Check if already bookmarked
    existing_bookmark = db.query(Bookmark).filter(
        Bookmark.user_id == current_user.id,
        Bookmark.content_id == content_id
    ).first()
    
    if existing_bookmark:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Content already bookmarked"
        )
    
    # Create bookmark
    bookmark = Bookmark(user_id=current_user.id, content_id=content_id)
    db.add(bookmark)
    db.commit()
    
    return {"message": "Content bookmarked successfully"}


@router.delete("/content/{content_id}/bookmark")
def remove_bookmark(
    content_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)]
) -> dict:
    """Remove bookmark from content.
    
    Args:
        content_id: Content ID
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Success message
        
    Raises:
        HTTPException: If bookmark not found
    """
    bookmark = db.query(Bookmark).filter(
        Bookmark.user_id == current_user.id,
        Bookmark.content_id == content_id
    ).first()
    
    if not bookmark:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bookmark not found"
        )
    
    db.delete(bookmark)
    db.commit()
    
    return {"message": "Bookmark removed successfully"}


# Subscriptions
@router.post("/users/{user_id}/subscribe", status_code=status.HTTP_201_CREATED)
def subscribe_to_author(
    user_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)]
) -> dict:
    """Subscribe to an author.
    
    Args:
        user_id: Author user ID
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Success message
        
    Raises:
        HTTPException: If author not found, trying to subscribe to self, or already subscribed
    """
    # Can't subscribe to yourself
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot subscribe to yourself"
        )
    
    # Verify author exists
    author = db.query(User).filter(User.id == user_id, User.is_active == True).first()
    if not author:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Check if already subscribed
    existing_subscription = db.query(Subscription).filter(
        Subscription.subscriber_id == current_user.id,
        Subscription.author_id == user_id
    ).first()
    
    if existing_subscription:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Already subscribed to this author"
        )
    
    # Create subscription
    subscription = Subscription(subscriber_id=current_user.id, author_id=user_id)
    db.add(subscription)
    db.commit()
    
    return {"message": "Subscribed successfully"}


@router.delete("/users/{user_id}/subscribe")
def unsubscribe_from_author(
    user_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)]
) -> dict:
    """Unsubscribe from an author.
    
    Args:
        user_id: Author user ID
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Success message
        
    Raises:
        HTTPException: If subscription not found
    """
    subscription = db.query(Subscription).filter(
        Subscription.subscriber_id == current_user.id,
        Subscription.author_id == user_id
    ).first()
    
    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subscription not found"
        )
    
    db.delete(subscription)
    db.commit()
    
    return {"message": "Unsubscribed successfully"}
