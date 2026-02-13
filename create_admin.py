"""
Script to create an admin user for the Qazaq Platform.
Run this script from the backend directory: python create_admin.py
"""

from sqlalchemy import select
from app.db.base import SessionLocal
from app.models.user import User, UserRole
from app.core.security import get_password_hash


def create_admin_user():
    """Create an admin user if it doesn't exist."""

    # Admin user details
    admin_email = "admin@qazaq.kz"
    admin_username = "admin"
    admin_password = "admin123"  # Change this after first login!

    db = SessionLocal()

    try:
        # Check if admin already exists
        result = db.execute(select(User).where(User.email == admin_email))
        existing_user = result.scalar_one_or_none()

        if existing_user:
            print(f"✅ Admin user already exists: {existing_user.email}")
            print(f"   Username: {existing_user.username}")
            print(f"   Role: {existing_user.role}")
            return

        # Create admin user
        admin_user = User(
            email=admin_email,
            username=admin_username,
            hashed_password=get_password_hash(admin_password),
            first_name="Admin",
            last_name="User",
            role=UserRole.ADMIN,
            is_active=True,
        )

        db.add(admin_user)
        db.commit()
        db.refresh(admin_user)

        print("🎉 Admin user created successfully!")
        print(f"   Email: {admin_user.email}")
        print(f"   Username: {admin_user.username}")
        print(f"   Password: {admin_password}")
        print(f"   Role: {admin_user.role}")
        print("\n⚠️  IMPORTANT: Change the password after first login!")
        print("\n📝 Login at: http://localhost:3001/login (CMS)")

    except Exception as e:
        db.rollback()
        print(f"❌ Error creating admin user: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    create_admin_user()
