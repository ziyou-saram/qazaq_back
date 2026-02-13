import os
import uuid
from io import BytesIO
from pathlib import Path
from typing import BinaryIO, Tuple

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
                detail=f"Invalid file type. Allowed: {', '.join(settings.ALLOWED_IMAGE_EXTENSIONS)}",
            )

        # Check file size
        file.file.seek(0, 2)  # Seek to end
        file_size = file.file.tell()
        file.file.seek(0)  # Reset to beginning

        if file_size > settings.MAX_UPLOAD_SIZE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File too large. Maximum size: {settings.MAX_UPLOAD_SIZE / 1024 / 1024}MB",
            )

        # Validate it's actually an image
        try:
            image = Image.open(file.file)
            image.verify()
            file.file.seek(0)  # Reset after verification
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid image file"
            )

    def process_image(self, file: UploadFile) -> Tuple[bytes, str]:
        """Process image: resize and optimize.

        Args:
            file: UploadFile object

        Returns:
            Tuple of (processed_bytes, content_type)
        """
        try:
            image = Image.open(file.file)

            # Convert to RGB if necessary (e.g. for RGBA PNGs converting to JPEG,
            # though we usually keep format or convert PNGs to PNGs.
            # For optimization, let's keep original format unless it's huge,
            # but usually converting to JPEG/WebP is best for photos.
            # To be safe and simple: maintain format but resize and optimize quality.
            # Exception: RGBA to JPEG needs conversion.

            orig_format = image.format
            content_type = file.content_type

            # Resize if too large
            if image.width > settings.MAX_IMAGE_WIDTH:
                ratio = settings.MAX_IMAGE_WIDTH / image.width
                new_height = int(image.height * ratio)
                image = image.resize(
                    (settings.MAX_IMAGE_WIDTH, new_height), Image.Resampling.LANCZOS
                )

            output = BytesIO()

            # Save options based on format
            if orig_format == "JPEG":
                image.save(
                    output, format="JPEG", quality=settings.IMAGE_QUALITY, optimize=True
                )
                content_type = "image/jpeg"
            elif orig_format == "PNG":
                # PNG optimization is different, 'quality' param doesn't apply the same way in Pillow
                # Just optimize flag helps a bit
                image.save(output, format="PNG", optimize=True)
                content_type = "image/png"
            elif orig_format == "WEBP":
                image.save(output, format="WEBP", quality=settings.IMAGE_QUALITY)
                content_type = "image/webp"
            else:
                # Fallback for others (GIF, etc) - just save as is or converted
                image.save(output, format=orig_format)

            return output.getvalue(), content_type

        except Exception as e:
            # Fallback: return original content if processing fails
            print(f"Image processing failed: {e}")
            file.file.seek(0)
            return file.file.read(), file.content_type

    async def save_file_local(self, content: bytes, filename: str) -> str:
        """Save file to local storage.

        Args:
            content: File content bytes
            filename: Filename to use

        Returns:
            Relative path to saved file
        """
        file_path = Path(settings.UPLOAD_DIR) / filename

        with open(file_path, "wb") as buffer:
            buffer.write(content)

        return str(file_path)

    async def save_file_s3(
        self, content: bytes, filename: str, content_type: str
    ) -> str:
        """Save file to S3 storage.

        Args:
            content: File content bytes
            filename: Filename to use
            content_type: MIME type

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
                "s3",
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                region_name=settings.AWS_REGION,
            )

            # Upload to S3
            s3_client.put_object(
                Bucket=settings.S3_BUCKET_NAME,
                Key=filename,
                Body=content,
                ContentType=content_type,
            )

            # Generate public URL
            url = f"https://{settings.S3_BUCKET_NAME}.s3.{settings.AWS_REGION}.amazonaws.com/{filename}"
            return url

        except ClientError as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to upload to S3: {str(e)}",
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"S3 upload error: {str(e)}",
            )

    async def save_upload(self, file: UploadFile) -> tuple[str, str, int]:
        """Save uploaded file to configured storage.

        Args:
            file: File to save

        Returns:
            Tuple of (filename, file_path/url, file_size)
        """
        # Validate image
        self.validate_image(file)

        # Process image (resize/optimize)
        content, content_type = self.process_image(file)
        file_size = len(content)

        # Generate unique filename
        filename = self.generate_unique_filename(file.filename or "upload")

        # Save based on storage type
        if self.storage_type == "local":
            file_path = await self.save_file_local(content, filename)
        elif self.storage_type == "s3" and settings.is_s3_configured:
            file_path = await self.save_file_s3(content, filename, content_type)
        else:
            missing = []
            if not settings.STORAGE_TYPE == "s3":
                missing.append("STORAGE_TYPE!=s3")
            if not settings.AWS_ACCESS_KEY_ID:
                missing.append("AWS_ACCESS_KEY_ID")
            if not settings.AWS_SECRET_ACCESS_KEY:
                missing.append("AWS_SECRET_ACCESS_KEY")
            if not settings.S3_BUCKET_NAME:
                missing.append("S3_BUCKET_NAME")

            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Storage config error. Missing: {', '.join(missing)}",
            )

        return filename, file_path, file_size

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
                "s3",
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                region_name=settings.AWS_REGION,
            )

            # Delete from S3
            s3_client.delete_object(Bucket=settings.S3_BUCKET_NAME, Key=filename)
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
