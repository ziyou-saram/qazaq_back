from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from app.api.deps import RequireChiefEditor, get_db
from app.models.content import Content, ContentStatus
from app.models.revision import Revision
from app.models.user import User
from app.schemas.content import (
    ContentList,
    ContentListItem,
    ContentResponse,
    RevisionRequest,
)
from app.utils.pagination import paginate_query

router = APIRouter(prefix="/cms/chief-editor", tags=["CMS - Chief Editor"])


@router.get("/dashboard")
def get_chief_editor_dashboard(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, RequireChiefEditor],
) -> dict:
    """Get chief editor dashboard statistics.

    Args:
        db: Database session
        current_user: Current authenticated chief editor

    Returns:
        Dashboard statistics
    """
    in_review_count = (
        db.query(func.count(Content.id))
        .filter(Content.status == ContentStatus.IN_REVIEW)
        .scalar()
    )

    approved_count = (
        db.query(func.count(Content.id))
        .filter(Content.status == ContentStatus.APPROVED)
        .scalar()
    )

    needs_revision_count = (
        db.query(func.count(Content.id))
        .filter(Content.status == ContentStatus.NEEDS_REVISION)
        .scalar()
    )

    return {
        "in_review": in_review_count,
        "approved": approved_count,
        "needs_revision": needs_revision_count,
    }


@router.get("/review-queue", response_model=ContentList)
def get_review_queue(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, RequireChiefEditor],
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    search: str | None = Query(None),
) -> dict:
    """Get content in review queue.

    Args:
        db: Database session
        current_user: Current authenticated chief editor
        skip: Number of items to skip
        limit: Maximum number of items to return
        search: Optional text search

    Returns:
        Paginated list of content in review
    """
    query = (
        db.query(Content)
        .filter(Content.status == ContentStatus.IN_REVIEW)
        .options(joinedload(Content.author))
        .order_by(Content.updated_at.asc())
    )

    if search:
        search_term = f"%{search}%"
        query = query.filter(
            (Content.title.ilike(search_term)) | (Content.excerpt.ilike(search_term))
        )

    items, total = paginate_query(query, skip, limit)

    # Add computed fields
    items_with_counts = []
    for item in items:
        item_dict = ContentListItem.model_validate(item).model_dump()
        item_dict["likes_count"] = len(item.likes)
        item_dict["comments_count"] = len(
            [c for c in item.comments if not c.is_deleted]
        )
        items_with_counts.append(ContentListItem(**item_dict))

    return {"items": items_with_counts, "total": total, "skip": skip, "limit": limit}


@router.get("/content/{content_id}", response_model=ContentResponse)
def get_content_for_review(
    content_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, RequireChiefEditor],
) -> Content:
    """Get content details for review.

    Args:
        content_id: Content ID
        db: Database session
        current_user: Current authenticated chief editor

    Returns:
        Content details

    Raises:
        HTTPException: If content not found
    """
    content = (
        db.query(Content)
        .filter(Content.id == content_id)
        .options(joinedload(Content.author))
        .first()
    )

    if not content:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Content not found"
        )

    # Add computed fields
    content_dict = ContentResponse.model_validate(content).model_dump()
    content_dict["likes_count"] = len(content.likes)
    content_dict["comments_count"] = len(
        [c for c in content.comments if not c.is_deleted]
    )

    return ContentResponse(**content_dict)


@router.post("/content/{content_id}/approve")
def approve_content(
    content_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, RequireChiefEditor],
) -> dict:
    """Approve content for publishing.

    Args:
        content_id: Content ID
        db: Database session
        current_user: Current authenticated chief editor

    Returns:
        Success message

    Raises:
        HTTPException: If content not found or not in review
    """
    content = db.query(Content).filter(Content.id == content_id).first()

    if not content:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Content not found"
        )

    if content.status != ContentStatus.IN_REVIEW:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Content is not in review"
        )

    content.status = ContentStatus.APPROVED
    db.commit()

    return {"message": "Content approved successfully"}


@router.post("/content/{content_id}/request-revision")
def request_revision(
    content_id: int,
    revision_data: RevisionRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, RequireChiefEditor],
) -> dict:
    """Request revision for content.

    Args:
        content_id: Content ID
        revision_data: Revision request with comment
        db: Database session
        current_user: Current authenticated chief editor

    Returns:
        Success message

    Raises:
        HTTPException: If content not found or not in review
    """
    content = db.query(Content).filter(Content.id == content_id).first()

    if not content:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Content not found"
        )

    if content.status != ContentStatus.IN_REVIEW:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Content is not in review"
        )

    # Create revision record
    revision = Revision(
        content_id=content_id, editor_id=current_user.id, comment=revision_data.comment
    )
    db.add(revision)

    # Update content status
    content.status = ContentStatus.NEEDS_REVISION
    db.commit()

    return {"message": "Revision requested successfully"}
