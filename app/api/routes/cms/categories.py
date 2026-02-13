from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.deps import RequireAdmin, RequireEditor, get_db
from app.models.category import Category
from app.models.user import User
from app.utils.slug import generate_unique_slug
from app.schemas.category import (
    CategoryCreate,
    CategoryList,
    CategoryResponse,
    CategoryUpdate,
)

router = APIRouter(prefix="/cms/categories", tags=["CMS - Categories"])


@router.get("", response_model=CategoryList)
def get_categories(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, RequireEditor],
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
) -> dict:
    """Get all categories.

    Args:
        db: Database session
        current_user: Current authenticated editor (or higher)
        skip: Number of items to skip
        limit: Maximum number of items to return

    Returns:
        List of categories and total count
    """
    total = db.query(Category).count()
    query = db.query(Category).order_by(Category.order.asc(), Category.name.asc())

    if limit > 0:
        query = query.offset(skip).limit(limit)

    items = query.all()

    # Pydantic v2 validation
    category_responses = [CategoryResponse.model_validate(item) for item in items]

    return {"items": category_responses, "total": total}


@router.post("", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
def create_category(
    category_data: CategoryCreate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, RequireAdmin],
) -> Category:
    """Create new category (Admin only).

    Args:
        category_data: Category data
        db: Database session
        current_user: Current authenticated admin

    Returns:
        Created category
    """
    # Check if name exists
    if db.query(Category).filter(Category.name == category_data.name).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Category with this name already exists",
        )

    slug = generate_unique_slug(db, Category, category_data.name)

    # Calculate order if not provided or 0
    if category_data.order == 0:
        max_order = db.query(func.max(Category.order)).scalar() or 0
        category_data.order = max_order + 10

    category = Category(
        name=category_data.name,
        slug=slug,
        description=category_data.description,
        parent_id=category_data.parent_id,
        order=category_data.order,
    )

    db.add(category)
    db.commit()
    db.refresh(category)

    return category


@router.get("/{category_id}", response_model=CategoryResponse)
def get_category(
    category_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, RequireEditor],
) -> Category:
    """Get category details.

    Args:
        category_id: Category ID
        db: Database session
        current_user: Current authenticated editor

    Returns:
        Category details
    """
    category = db.query(Category).filter(Category.id == category_id).first()

    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Category not found"
        )

    return category


@router.put("/{category_id}", response_model=CategoryResponse)
def update_category(
    category_id: int,
    category_data: CategoryUpdate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, RequireAdmin],
) -> Category:
    """Update category (Admin only).

    Args:
        category_id: Category ID
        category_data: Updated category data
        db: Database session
        current_user: Current authenticated admin

    Returns:
        Updated category
    """
    category = db.query(Category).filter(Category.id == category_id).first()

    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Category not found"
        )

    update_data = category_data.model_dump(exclude_unset=True)

    # Handle name change -> slug update
    if "name" in update_data and update_data["name"] != category.name:
        category.slug = generate_unique_slug(db, Category, update_data["name"])

    for field, value in update_data.items():
        setattr(category, field, value)

    db.commit()
    db.refresh(category)

    return category


@router.delete("/{category_id}")
def delete_category(
    category_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, RequireAdmin],
) -> dict:
    """Delete category (Admin only).

    Args:
        category_id: Category ID
        db: Database session
        current_user: Current authenticated admin

    Returns:
        Success message
    """
    category = db.query(Category).filter(Category.id == category_id).first()

    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Category not found"
        )

    db.delete(category)
    db.commit()

    return {"message": "Category deleted successfully"}
