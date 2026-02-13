from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from app.api.deps import RequireEditor, get_db
from app.models.content import Content, ContentStatus
from app.models.user import User
from app.schemas.content import (
    ContentCreate,
    ContentList,
    ContentListItem,
    ContentResponse,
    ContentUpdate,
    RevisionResponse,
)
from app.utils.pagination import paginate_query
from app.utils.slug import generate_unique_slug

router = APIRouter(prefix="/cms/editor", tags=["CMS - Editor"])


@router.get("/dashboard")
def get_editor_dashboard(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, RequireEditor],
) -> dict:
    """Get editor dashboard statistics.

    Args:
        db: Database session
        current_user: Current authenticated editor

    Returns:
        Dashboard statistics
    """
    drafts_count = (
        db.query(func.count(Content.id))
        .filter(
            Content.author_id == current_user.id, Content.status == ContentStatus.DRAFT
        )
        .scalar()
    )

    in_review_count = (
        db.query(func.count(Content.id))
        .filter(
            Content.author_id == current_user.id,
            Content.status == ContentStatus.IN_REVIEW,
        )
        .scalar()
    )

    needs_revision_count = (
        db.query(func.count(Content.id))
        .filter(
            Content.author_id == current_user.id,
            Content.status == ContentStatus.NEEDS_REVISION,
        )
        .scalar()
    )

    published_count = (
        db.query(func.count(Content.id))
        .filter(
            Content.author_id == current_user.id,
            Content.status == ContentStatus.PUBLISHED,
        )
        .scalar()
    )

    return {
        "drafts": drafts_count,
        "in_review": in_review_count,
        "needs_revision": needs_revision_count,
        "published": published_count,
    }


@router.get("/content", response_model=ContentList)
def get_editor_content(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, RequireEditor],
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    status: ContentStatus | None = Query(None),
    search: str | None = Query(None),
) -> dict:
    """Get editor's own content.

    Args:
        db: Database session
        current_user: Current authenticated editor
        skip: Number of items to skip
        limit: Maximum number of items to return
        status: Optional status filter
        search: Optional text search (title/excerpt)

    Returns:
        Paginated list of editor's content
    """
    query = (
        db.query(Content)
        .filter(Content.author_id == current_user.id)
        .options(joinedload(Content.author))
        .order_by(Content.created_at.desc())
    )

    if status:
        query = query.filter(Content.status == status)

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


@router.post(
    "/content", response_model=ContentResponse, status_code=status.HTTP_201_CREATED
)
def create_content(
    content_data: ContentCreate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, RequireEditor],
) -> Content:
    """Create new content (draft).

    Args:
        content_data: Content data
        db: Database session
        current_user: Current authenticated editor

    Returns:
        Created content
    """
    # Generate unique slug
    slug = generate_unique_slug(db, Content, content_data.title)

    # Create content
    content = Content(
        title=content_data.title,
        slug=slug,
        content=content_data.content,
        excerpt=content_data.excerpt,
        type=content_data.type,
        category_id=content_data.category_id,
        cover_image_url=content_data.cover_image_url,
        author_id=current_user.id,
        status=ContentStatus.DRAFT,
    )

    db.add(content)
    db.commit()
    db.refresh(content)

    # Add computed fields
    content_dict = ContentResponse.model_validate(content).model_dump()
    content_dict["likes_count"] = 0
    content_dict["comments_count"] = 0

    return ContentResponse(**content_dict)


@router.get("/content/{content_id}", response_model=ContentResponse)
def get_content(
    content_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, RequireEditor],
) -> Content:
    """Get own content by ID.

    Args:
        content_id: Content ID
        db: Database session
        current_user: Current authenticated editor

    Returns:
        Content details

    Raises:
        HTTPException: If content not found or not owned by editor
    """
    content = (
        db.query(Content)
        .filter(Content.id == content_id, Content.author_id == current_user.id)
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


@router.put("/content/{content_id}", response_model=ContentResponse)
def update_content(
    content_id: int,
    content_data: ContentUpdate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, RequireEditor],
) -> Content:
    """Update own content.

    Args:
        content_id: Content ID
        content_data: Updated content data
        db: Database session
        current_user: Current authenticated editor

    Returns:
        Updated content

    Raises:
        HTTPException: If content not found, not owned, or not editable
    """
    content = (
        db.query(Content)
        .filter(Content.id == content_id, Content.author_id == current_user.id)
        .first()
    )

    if not content:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Content not found"
        )

    # Allow editing draft, needs_revision, approved, and published content
    if content.status in [ContentStatus.IN_REVIEW]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot edit content while it is in review",
        )

    # Update fields
    update_data = content_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(content, field, value)

    # Regenerate slug if title changed
    if content_data.title:
        content.slug = generate_unique_slug(db, Content, content_data.title)

    db.commit()
    db.refresh(content)

    # Add computed fields
    content_dict = ContentResponse.model_validate(content).model_dump()
    content_dict["likes_count"] = len(content.likes)
    content_dict["comments_count"] = len(
        [c for c in content.comments if not c.is_deleted]
    )

    return ContentResponse(**content_dict)


@router.delete("/content/{content_id}")
def delete_content(
    content_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, RequireEditor],
) -> dict:
    """Delete own draft content.

    Args:
        content_id: Content ID
        db: Database session
        current_user: Current authenticated editor

    Returns:
        Success message

    Raises:
        HTTPException: If content not found, not owned, or not draft
    """
    content = (
        db.query(Content)
        .filter(Content.id == content_id, Content.author_id == current_user.id)
        .first()
    )

    if not content:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Content not found"
        )

    # Can only delete drafts
    if content.status != ContentStatus.DRAFT:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Can only delete draft content",
        )

    db.delete(content)
    db.commit()

    return {"message": "Content deleted successfully"}


@router.post("/content/{content_id}/submit")
def submit_for_review(
    content_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, RequireEditor],
) -> dict:
    """Submit content for review.

    Args:
        content_id: Content ID
        db: Database session
        current_user: Current authenticated editor

    Returns:
        Success message

    Raises:
        HTTPException: If content not found, not owned, or not submittable
    """
    content = (
        db.query(Content)
        .filter(Content.id == content_id, Content.author_id == current_user.id)
        .first()
    )

    if not content:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Content not found"
        )

    # Can submit draft or needs_revision content
    if content.status not in [ContentStatus.DRAFT, ContentStatus.NEEDS_REVISION]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Content is not in a submittable state",
        )

    content.status = ContentStatus.IN_REVIEW
    db.commit()

    return {"message": "Content submitted for review"}


@router.get("/content/{content_id}/revisions", response_model=list[RevisionResponse])
def get_content_revisions(
    content_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, RequireEditor],
) -> list:
    """Get revision history for own content.

    Args:
        content_id: Content ID
        db: Database session
        current_user: Current authenticated editor

    Returns:
        List of revisions

    Raises:
        HTTPException: If content not found or not owned
    """
    content = (
        db.query(Content)
        .filter(Content.id == content_id, Content.author_id == current_user.id)
        .first()
    )

    if not content:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Content not found"
        )

    return content.revisions
