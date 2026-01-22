from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import auth, media
from app.api.routes.public import comments, content, social
from app.api.routes.cms import admin, chief_editor, editor, moderator, publishing_editor
from app.core.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    print(f"Starting {settings.PROJECT_NAME} v{settings.VERSION}")
    yield
    # Shutdown
    print("Shutting down...")


# Create FastAPI application
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Backend API for Qazaq news and article publishing platform",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.BACKEND_CORS_ALLOW_ALL else [str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
    allow_credentials=False if settings.BACKEND_CORS_ALLOW_ALL else True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
# Authentication
app.include_router(auth.router)

# Public routes
app.include_router(content.router)
app.include_router(comments.router)
app.include_router(social.router)

# Media
app.include_router(media.router)

# CMS routes
app.include_router(editor.router)
app.include_router(chief_editor.router)
app.include_router(publishing_editor.router)
app.include_router(moderator.router)
app.include_router(admin.router)


@app.get("/")
def root():
    """Root endpoint."""
    return {
        "message": f"Welcome to {settings.PROJECT_NAME} API",
        "version": settings.VERSION,
        "docs": "/docs",
        "redoc": "/redoc"
    }


@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}
