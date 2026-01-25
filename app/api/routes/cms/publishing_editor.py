from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from app.api.deps import RequirePublishingEditor, get_db
from app.models.content import Content, ContentStatus
from app.models.user import User
from app.schemas.content import ContentList, ContentListItem, ContentPublish, ContentResponse
from app.utils.pagination import paginate_query

router = APIRouter(prefix="/cms/publishing", tags=["CMS - Publishing Editor"])


@router.get("/dashboard")
def get_publishing_dashboard(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, RequirePublishingEditor]
) -> dict:
    """Get publishing editor dashboard statistics.
    
    Args:
        db: Database session
        current_user: Current authenticated publishing editor
        
    Returns:
        Dashboard statistics
    """
    approved_count = db.query(func.count(Content.id)).filter(
        Content.status == ContentStatus.APPROVED
    ).scalar()
    
    published_count = db.query(func.count(Content.id)).filter(
        Content.status == ContentStatus.PUBLISHED
    ).scalar()
    
    scheduled_count = db.query(func.count(Content.id)).filter(
        Content.status == ContentStatus.APPROVED,
        Content.scheduled_publish_at.isnot(None)
    ).scalar()
    
    return {
        "approved": approved_count,
        "published": published_count,
        "scheduled": scheduled_count
    }


@router.get("/approved-queue", response_model=ContentList)
def get_approved_queue(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, RequirePublishingEditor],
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100)
) -> dict:
    """Get approved content ready for publishing.
    
    Args:
        db: Database session
        current_user: Current authenticated publishing editor
        skip: Number of items to skip
        limit: Maximum number of items to return
        
    Returns:
        Paginated list of approved content
    """
    query = db.query(Content).filter(
        Content.status == ContentStatus.APPROVED
    ).options(
        joinedload(Content.author)
    ).order_by(Content.updated_at.asc())
    
    items, total = paginate_query(query, skip, limit)
    
    # Add computed fields
    items_with_counts = []
    for item in items:
        item_dict = ContentListItem.model_validate(item).model_dump()
        item_dict["likes_count"] = len(item.likes)
        item_dict["comments_count"] = len([c for c in item.comments if not c.is_deleted])
        items_with_counts.append(ContentListItem(**item_dict))
    
    return {
        "items": items_with_counts,
        "total": total,
        "skip": skip,
        "limit": limit
    }


@router.get("/content/{content_id}", response_model=ContentResponse)
def get_publishing_content(
    content_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, RequirePublishingEditor]
) -> Content:
    """Get approved content details for publishing.
    
    Args:
        content_id: Content ID
        db: Database session
        current_user: Current authenticated publishing editor
        
    Returns:
        Content details
        
    Raises:
        HTTPException: If content not found
    """
    content = db.query(Content).filter(
        Content.id == content_id
    ).options(
        joinedload(Content.author)
    ).first()
    
    if not content:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Content not found"
        )
    
    # Allow viewing if approved OR published
    if content.status not in [ContentStatus.APPROVED, ContentStatus.PUBLISHED]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Content is not accessible for publishing editor"
        )
    
    # Add computed fields
    content_dict = ContentResponse.model_validate(content).model_dump()
    content_dict["likes_count"] = len(content.likes)
    content_dict["comments_count"] = len([c for c in content.comments if not c.is_deleted])
    
    return ContentResponse(**content_dict)


@router.post("/content/{content_id}/publish")
def publish_content(
    content_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, RequirePublishingEditor],
    publish_data: ContentPublish | None = None
) -> dict:
    """Publish approved content.
    
    Args:
        content_id: Content ID
        publish_data: Optional publish data (for scheduling)
        db: Database session
        current_user: Current authenticated publishing editor
        
    Returns:
        Success message
        
    Raises:
        HTTPException: If content not found or not approved
    """
    content = db.query(Content).filter(Content.id == content_id).first()
    
    if not content:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Content not found"
        )
    
    if content.status != ContentStatus.APPROVED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Content is not approved for publishing"
        )
    
    # Check if scheduling
    if publish_data and publish_data.scheduled_publish_at:
        content.scheduled_publish_at = publish_data.scheduled_publish_at
        db.commit()
        return {"message": "Content scheduled for publishing"}
    
    # Publish immediately
    content.status = ContentStatus.PUBLISHED
    content.published_at = datetime.now(timezone.utc)
    db.commit()
    
    return {"message": "Content published successfully"}


@router.post("/content/{content_id}/schedule")
def schedule_content(
    content_id: int,
    publish_data: ContentPublish,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, RequirePublishingEditor]
) -> dict:
    """Schedule content for future publishing.
    
    Args:
        content_id: Content ID
        publish_data: Publish data with scheduled time
        db: Database session
        current_user: Current authenticated publishing editor
        
    Returns:
        Success message
        
    Raises:
        HTTPException: If content not found, not approved, or no schedule time
    """
    if not publish_data.scheduled_publish_at:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Scheduled publish time is required"
        )
    
    content = db.query(Content).filter(Content.id == content_id).first()
    
    if not content:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Content not found"
        )
    
    if content.status != ContentStatus.APPROVED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Content is not approved for publishing"
        )
    
    content.scheduled_publish_at = publish_data.scheduled_publish_at
    db.commit()
    
    return {"message": "Content scheduled successfully"}


@router.post("/content/{content_id}/unpublish")
def unpublish_content(
    content_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, RequirePublishingEditor]
) -> dict:
    """Unpublish content.
    
    Args:
        content_id: Content ID
        db: Database session
        current_user: Current authenticated publishing editor
        
    Returns:
        Success message
        
    Raises:
        HTTPException: If content not found or not published
    """
    content = db.query(Content).filter(Content.id == content_id).first()
    
    if not content:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Content not found"
        )
    
    if content.status != ContentStatus.PUBLISHED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Content is not published"
        )
    
    content.status = ContentStatus.APPROVED
    db.commit()
    
    return {"message": "Content unpublished successfully"}
