"""Update slugs for existing content."""
from sqlalchemy.orm import Session

from app.db.base import SessionLocal
from app.models.content import Content
from app.utils.slug import generate_unique_slug


def update_content_slugs():
    """Update all content slugs to use transliterated titles."""
    print("Updating content slugs...")
    db = SessionLocal()
    
    try:
        # Get all content
        all_content = db.query(Content).all()
        
        for content in all_content:
            # Generate new slug from title
            new_slug = generate_unique_slug(db, Content, content.title)
            
            print(f"Updating: {content.title[:50]}...")
            print(f"  Old slug: {content.slug}")
            print(f"  New slug: {new_slug}")
            
            content.slug = new_slug
        
        db.commit()
        print(f"\n✓ Updated {len(all_content)} content items")
        
    finally:
        db.close()


if __name__ == "__main__":
    update_content_slugs()
