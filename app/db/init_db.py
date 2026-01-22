from sqlalchemy.orm import Session

from app.core.security import get_password_hash
from app.db.base import SessionLocal
from app.models.category import Category
from app.models.user import User, UserRole


def init_db(db: Session) -> None:
    """Initialize database with default data.
    
    Args:
        db: Database session
    """
    # Create default admin user
    admin = db.query(User).filter(User.email == "admin@qazaq.kz").first()
    if not admin:
        admin = User(
            username="admin",
            email="admin@qazaq.kz",
            first_name="Admin",
            last_name="User",
            hashed_password=get_password_hash("admin123"),  # Change in production!
            role=UserRole.ADMIN,
            is_active=True
        )
        db.add(admin)
        print("✓ Created default admin user (admin@qazaq.kz / admin123)")
    
    # Create default categories
    default_categories = [
        {"name": "Политика", "slug": "politics", "order": 1},
        {"name": "Экономика", "slug": "economics", "order": 2},
        {"name": "Общество", "slug": "society", "order": 3},
        {"name": "Культура", "slug": "culture", "order": 4},
        {"name": "Спорт", "slug": "sport", "order": 5},
        {"name": "Технологии", "slug": "technology", "order": 6},
    ]
    
    for cat_data in default_categories:
        category = db.query(Category).filter(Category.slug == cat_data["slug"]).first()
        if not category:
            category = Category(**cat_data)
            db.add(category)
            print(f"✓ Created category: {cat_data['name']}")
    
    db.commit()
    print("✓ Database initialization complete")


if __name__ == "__main__":
    print("Initializing database...")
    db = SessionLocal()
    try:
        init_db(db)
    finally:
        db.close()
