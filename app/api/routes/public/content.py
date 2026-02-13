from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session, joinedload

from app.db.base import get_db
from app.models.content import Content, ContentStatus, ContentType
from app.models.category import Category
from app.schemas.content import ContentList, ContentListItem, ContentResponse
from app.schemas.category import CategoryList
from app.utils.pagination import paginate_query

router = APIRouter(prefix="/public", tags=["Public Content"])


@router.get("/news", response_model=ContentList)
def get_published_news(
    db: Annotated[Session, Depends(get_db)],
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    category_id: int | None = Query(None),
    search: str | None = Query(None),
) -> dict:
    """Get list of published news.

    Args:
        db: Database session
        skip: Number of items to skip
        limit: Maximum number of items to return
        category_id: Optional category filter
        search: Optional search term

    Returns:
        Paginated list of published news
    """
    query = (
        db.query(Content)
        .filter(
            Content.type == ContentType.NEWS, Content.status == ContentStatus.PUBLISHED
        )
        .options(joinedload(Content.author))
        .order_by(Content.published_at.desc())
    )

    if category_id:
        query = query.filter(Content.category_id == category_id)

    if search:
        search_filter = f"%{search}%"
        query = query.filter(
            (Content.title.ilike(search_filter))
            | (Content.excerpt.ilike(search_filter))
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


@router.get("/articles", response_model=ContentList)
def get_published_articles(
    db: Annotated[Session, Depends(get_db)],
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    category_id: int | None = Query(None),
    search: str | None = Query(None),
) -> dict:
    """Get list of published articles.

    Args:
        db: Database session
        skip: Number of items to skip
        limit: Maximum number of items to return
        category_id: Optional category filter
        search: Optional search term

    Returns:
        Paginated list of published articles
    """
    query = (
        db.query(Content)
        .filter(
            Content.type == ContentType.ARTICLE,
            Content.status == ContentStatus.PUBLISHED,
        )
        .options(joinedload(Content.author))
        .order_by(Content.published_at.desc())
    )

    if category_id:
        query = query.filter(Content.category_id == category_id)

    if search:
        search_filter = f"%{search}%"
        query = query.filter(
            (Content.title.ilike(search_filter))
            | (Content.excerpt.ilike(search_filter))
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


@router.get("/search", response_model=ContentList)
def search_content(
    db: Annotated[Session, Depends(get_db)],
    q: str = Query(..., min_length=1),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
) -> dict:
    """Search across all published content.

    Args:
        db: Database session
        q: Search query
        skip: Number of items to skip
        limit: Maximum number of items to return

    Returns:
        Paginated list of search results
    """
    search_filter = f"%{q}%"
    query = (
        db.query(Content)
        .filter(
            Content.status == ContentStatus.PUBLISHED,
            (Content.title.ilike(search_filter))
            | (Content.excerpt.ilike(search_filter)),
        )
        .options(joinedload(Content.author))
        .order_by(Content.published_at.desc())
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


@router.get("/content/{slug}", response_model=ContentResponse)
def get_content_by_slug(slug: str, db: Annotated[Session, Depends(get_db)]) -> Content:
    """Get published content by slug.

    Args:
        slug: Content slug
        db: Database session

    Returns:
        Content details

    Raises:
        HTTPException: If content not found or not published
    """
    content = (
        db.query(Content)
        .filter(Content.slug == slug, Content.status == ContentStatus.PUBLISHED)
        .options(joinedload(Content.author))
        .first()
    )

    if not content:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Content not found"
        )

    # Increment view count
    content.view_count += 1
    db.commit()

    # Add computed fields
    content_dict = ContentResponse.model_validate(content).model_dump()
    content_dict["likes_count"] = len(content.likes)
    content_dict["comments_count"] = len(
        [c for c in content.comments if not c.is_deleted]
    )

    return ContentResponse(**content_dict)


@router.get("/categories", response_model=CategoryList)
def get_categories(
    db: Annotated[Session, Depends(get_db)],
    has_content: bool = Query(False),
) -> dict:
    """Get all categories.

    Args:
        db: Database session
        has_content: If True, return only categories with published content

    Returns:
        List of categories
    """
    query = db.query(Category).filter(Category.parent_id.is_(None))

    if has_content:
        query = (
            query.join(Category.content_items)
            .filter(Content.status == ContentStatus.PUBLISHED)
            .distinct()
        )

    categories = query.order_by(Category.order, Category.name).all()

    return {"items": categories, "total": len(categories)}


@router.get("/categories/{slug}/content", response_model=ContentList)
def get_content_by_category(
    slug: str,
    db: Annotated[Session, Depends(get_db)],
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    search: str | None = Query(None),
) -> dict:
    """Get published content by category slug.

    Args:
        slug: Category slug
        db: Database session
        skip: Number of items to skip
        limit: Maximum number of items to return
        search: Optional search term

    Returns:
        Paginated list of published content in category

    Raises:
        HTTPException: If category not found
    """
    category = db.query(Category).filter(Category.slug == slug).first()
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Category not found"
        )

    query = (
        db.query(Content)
        .filter(
            Content.category_id == category.id,
            Content.status == ContentStatus.PUBLISHED,
        )
        .options(joinedload(Content.author))
        .order_by(Content.published_at.desc())
    )

    if search:
        search_filter = f"%{search}%"
        query = query.filter(
            (Content.title.ilike(search_filter))
            | (Content.excerpt.ilike(search_filter))
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
