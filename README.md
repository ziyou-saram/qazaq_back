# Qazaq Platform - Backend

FastAPI backend for the Qazaq news and article publishing platform.

## Features

- 🔐 JWT-based authentication with refresh tokens
- 👥 Role-based access control (RBAC)
- 📝 Content management with workflow (Draft → Review → Approved → Published)
- 💬 Social features (likes, comments, bookmarks, subscriptions)
- 📸 Media upload with S3 support
- 🎯 Separate CMS endpoints for different roles

## Tech Stack

- **FastAPI** - Modern Python web framework
- **SQLAlchemy** - ORM for database operations
- **Alembic** - Database migrations
- **PostgreSQL** - Primary database
- **Pydantic v2** - Data validation
- **JWT** - Authentication tokens

## Setup

### 1. Create Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment

```bash
cp .env.example .env
# Edit .env with your configuration
```

### 4. Setup Database

```bash
# Create PostgreSQL database
createdb qazaq_db

# Run migrations
alembic upgrade head

# Initialize database with default data
python -m app.db.init_db
```

### 5. Run Development Server

```bash
uvicorn app.main:app --reload --port 8000
```

The API will be available at `http://localhost:8000`

## API Documentation

Once the server is running, visit:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Project Structure

```
backend/
├── app/
│   ├── api/
│   │   ├── routes/
│   │   │   ├── auth.py           # Authentication endpoints
│   │   │   ├── public/           # Public endpoints
│   │   │   │   ├── content.py
│   │   │   │   ├── comments.py
│   │   │   │   ├── social.py
│   │   │   │   └── user.py
│   │   │   ├── cms/              # CMS endpoints
│   │   │   │   ├── editor.py
│   │   │   │   ├── chief_editor.py
│   │   │   │   ├── publishing_editor.py
│   │   │   │   ├── moderator.py
│   │   │   │   └── admin.py
│   │   │   └── media.py          # Media upload
│   │   └── deps.py               # Dependencies
│   ├── core/
│   │   ├── config.py             # Configuration
│   │   ├── security.py           # Security utilities
│   │   └── storage.py            # File storage
│   ├── db/
│   │   ├── base.py               # Database base
│   │   └── init_db.py            # Database initialization
│   ├── models/                   # SQLAlchemy models
│   ├── schemas/                  # Pydantic schemas
│   ├── utils/                    # Utilities
│   └── main.py                   # FastAPI app
├── alembic/                      # Database migrations
├── tests/                        # Test files
├── requirements.txt
└── .env
```

## User Roles

- **user** - Regular public user
- **editor** - Creates and edits content
- **chief_editor** - Reviews and approves content
- **publishing_editor** - Publishes approved content
- **moderator** - Moderates comments and users
- **admin** - Manages users and roles

## Content Workflow

1. **Draft** - Editor creates content
2. **In Review** - Editor submits for review
3. **Needs Revision** - Chief editor requests changes
4. **Approved** - Chief editor approves
5. **Published** - Publishing editor publishes

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app tests/

# Run specific test file
pytest tests/test_auth.py -v
```

## Database Migrations

```bash
# Create new migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback migration
alembic downgrade -1
```

## Development

The backend follows FastAPI best practices:

- Dependency injection for database sessions and authentication
- Pydantic v2 for request/response validation
- SQLAlchemy 2.0 with async support ready
- Proper error handling with HTTPException
- CORS middleware for frontend integration

## License

Proprietary - Qazaq Platform
