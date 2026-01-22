"""Test S3 upload functionality."""
import asyncio
import io
from pathlib import Path

from PIL import Image
from fastapi import UploadFile

from app.core.storage import storage_service


async def test_s3_upload():
    """Test uploading a file to S3."""
    print("Testing S3 upload...")
    print(f"Storage type: {storage_service.storage_type}")
    
    # Create a test image
    img = Image.new('RGB', (100, 100), color='red')
    img_bytes = io.BytesIO()
    img.save(img_bytes, format='PNG')
    img_bytes.seek(0)
    
    # Create UploadFile
    upload_file = UploadFile(
        filename="test-image.png",
        file=img_bytes
    )
    upload_file.content_type = "image/png"
    
    try:
        # Upload to S3
        filename, file_url = await storage_service.save_upload(upload_file)
        
        print(f"✓ Upload successful!")
        print(f"  Filename: {filename}")
        print(f"  URL: {file_url}")
        
        # Test delete
        print("\nTesting S3 delete...")
        storage_service.delete_file(file_url)
        print("✓ Delete successful!")
        
    except Exception as e:
        print(f"✗ Upload failed: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_s3_upload())
