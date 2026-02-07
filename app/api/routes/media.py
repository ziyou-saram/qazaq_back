from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_user
from app.core.storage import storage_service
from app.core.config import settings
from app.db.base import get_db
from app.models.media import Media
from app.models.user import User
from app.schemas.media import MediaUploadResponse

router = APIRouter(prefix="/media", tags=["Media"])


@router.post("/upload", response_model=MediaUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_media(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> dict:
    """Upload media file.
    
    Args:
        file: File to upload
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Uploaded media information
        
    Raises:
        HTTPException: If file upload fails
    """
    # Save file using storage service
    filename, file_path = await storage_service.save_upload(file)
    
    # Create media record
    media = Media(
        filename=filename,
        file_path=file_path,
        file_type=file.content_type or "application/octet-stream",
        file_size=file.size or 0,
        uploaded_by=current_user.id
    )
    
    db.add(media)
    db.commit()
    db.refresh(media)
    
    # For S3 keep the absolute URL, for local keep the static media route.
    if settings.STORAGE_TYPE == "s3":
        url = file_path
    else:
        url = f"/media/{filename}"
    
    # Manually construct response with all fields
    return {
        "id": media.id,
        "filename": media.filename,
        "file_path": media.file_path,
        "file_type": media.file_type,
        "file_size": media.file_size,
        "uploaded_by": media.uploaded_by,
        "created_at": media.created_at,
        "url": url
    }


# Media serving is handled by StaticFiles in main.py
