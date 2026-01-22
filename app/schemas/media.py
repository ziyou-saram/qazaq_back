from datetime import datetime

from pydantic import BaseModel, ConfigDict


class MediaUploadResponse(BaseModel):
    """Schema for media upload response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    filename: str
    file_path: str
    file_type: str
    file_size: int
    uploaded_by: int
    created_at: datetime
    
    # Public URL for accessing the file
    url: str
