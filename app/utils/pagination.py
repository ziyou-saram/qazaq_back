from typing import TypeVar

from pydantic import BaseModel
from sqlalchemy.orm import Query

T = TypeVar("T")


class PaginationParams(BaseModel):
    """Pagination parameters."""
    skip: int = 0
    limit: int = 20
    
    def __init__(self, skip: int = 0, limit: int = 20):
        super().__init__(skip=max(0, skip), limit=min(max(1, limit), 100))


def paginate_query(query: Query, skip: int = 0, limit: int = 20) -> tuple[list[T], int]:
    """Paginate a SQLAlchemy query.
    
    Args:
        query: SQLAlchemy query to paginate
        skip: Number of items to skip
        limit: Maximum number of items to return
        
    Returns:
        Tuple of (items, total_count)
    """
    total = query.count()
    items = query.offset(skip).limit(limit).all()
    return items, total
