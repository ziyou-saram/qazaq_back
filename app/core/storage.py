import os
import uuid
from pathlib import Path
from typing import BinaryIO

from fastapi import HTTPException, UploadFile, status
from PIL import Image

from app.core.config import settings


class StorageService:
    """Service for handling file storage (local or S3)."""
    
    def __init__(self):
        self.storage_type = settings.STORAGE_TYPE
        
        # Ensure upload directory exists for local storage
        if self.storage_type == "local":
            Path(settings.UPLOAD_DIR).mkdir(parents=True, exist_ok=True)
    
    def generate_unique_filename(self, original_filename: str) -> str:
        """Generate a unique filename while preserving extension.
        
        Args:
            original_filename: Original filename from upload
            
        Returns:
            Unique filename with UUID
        """
        ext = Path(original_filename).suffix.lower()
        unique_name = f"{uuid.uuid4()}{ext}"
        return unique_name
    
    def validate_image(self, file: UploadFile) -> None:
        """Validate uploaded image file.
        
        Args:
            file: Uploaded file to validate
            
        Raises:
            HTTPException: If file is invalid
        """
        # Check file extension
        ext = Path(file.filename or "").suffix.lower()
        if ext not in settings.ALLOWED_IMAGE_EXTENSIONS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid file type. Allowed: {', '.join(settings.ALLOWED_IMAGE_EXTENSIONS)}"
            )
        
        # Check file size
        file.file.seek(0, 2)  # Seek to end
        file_size = file.file.tell()
        file.file.seek(0)  # Reset to beginning
        
        if file_size > settings.MAX_UPLOAD_SIZE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File too large. Maximum size: {settings.MAX_UPLOAD_SIZE / 1024 / 1024}MB"
            )
        
        # Validate it's actually an image
        try:
            image = Image.open(file.file)
            image.verify()
            file.file.seek(0)  # Reset after verification
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid image file"
            )
    
    async def save_file_local(self, file: UploadFile, filename: str) -> str:
        """Save file to local storage.
        
        Args:
            file: File to save
            filename: Filename to use
            
        Returns:
            Relative path to saved file
        """
        file_path = Path(settings.UPLOAD_DIR) / filename
        
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        return str(file_path)
    
    async def save_file_s3(self, file: UploadFile, filename: str) -> str:
        """Save file to S3 storage.
        
        Args:
            file: File to save
            filename: Filename to use
            
        Returns:
            S3 URL to saved file
            
        Raises:
            HTTPException: If S3 upload fails
        """
        try:
            import boto3
            from botocore.exceptions import ClientError
            
            # Create S3 client
            s3_client = boto3.client(
                's3',
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                region_name=settings.AWS_REGION
            )
            
            # Read file content
            content = await file.read()
            
            # Upload to S3
            s3_client.put_object(
                Bucket=settings.S3_BUCKET_NAME,
                Key=filename,
                Body=content,
                ContentType=file.content_type or 'application/octet-stream'
            )
            
            # Generate public URL
            url = f"https://{settings.S3_BUCKET_NAME}.s3.{settings.AWS_REGION}.amazonaws.com/{filename}"
            return url
            
        except ClientError as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to upload to S3: {str(e)}"
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"S3 upload error: {str(e)}"
            )
    
    async def save_upload(self, file: UploadFile) -> tuple[str, str]:
        """Save uploaded file to configured storage.
        
        Args:
            file: File to save
            
        Returns:
            Tuple of (filename, file_path/url)
        """
        # Validate image
        self.validate_image(file)
        
        # Generate unique filename
        filename = self.generate_unique_filename(file.filename or "upload")
        
        # Save based on storage type
        if self.storage_type == "local":
            file_path = await self.save_file_local(file, filename)
        elif self.storage_type == "s3" and settings.is_s3_configured:
            file_path = await self.save_file_s3(file, filename)
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Storage not properly configured"
            )
        
        return filename, file_path
    
    def delete_file_local(self, file_path: str) -> None:
        """Delete file from local storage.
        
        Args:
            file_path: Path to file to delete
        """
        try:
            Path(file_path).unlink(missing_ok=True)
        except Exception:
            pass  # Silently fail if file doesn't exist
    
    def delete_file_s3(self, filename: str) -> None:
        """Delete file from S3 storage.
        
        Args:
            filename: Filename to delete
        """
        try:
            import boto3
            from botocore.exceptions import ClientError
            
            # Create S3 client
            s3_client = boto3.client(
                's3',
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                region_name=settings.AWS_REGION
            )
            
            # Delete from S3
            s3_client.delete_object(
                Bucket=settings.S3_BUCKET_NAME,
                Key=filename
            )
        except Exception:
            # Silently fail - file might not exist
            pass
    
    def delete_file(self, file_path: str) -> None:
        """Delete file from configured storage.
        
        Args:
            file_path: Path or URL to file to delete
        """
        if self.storage_type == "local":
            self.delete_file_local(file_path)
        elif self.storage_type == "s3":
            # Extract filename from S3 URL
            filename = Path(file_path).name
            self.delete_file_s3(filename)


# Global storage service instance
storage_service = StorageService()
