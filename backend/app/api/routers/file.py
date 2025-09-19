import logging
import uuid
import tempfile
import requests
from urllib.parse import urlparse
import os
import mimetypes
from pathlib import Path

from fastapi import APIRouter, Depends, UploadFile, File as FastAPIFile, HTTPException
from app.schemas import file as file_schema
from app.database.database import get_db
from sqlalchemy.orm import Session
from app.services.extraction_service import file_extractor_service
from app.models.file import File
from app.services.minio_service import upload_file_to_minio, delete_file_from_minio
from uuid import uuid4
from datetime import datetime

from app.dependencies import verify_jwt

router = APIRouter(prefix="/file", tags=["File"])
logger = logging.getLogger(__name__)

# Security configuration
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
ALLOWED_EXTENSIONS = {
    '.txt', '.pdf', '.docx', '.doc', '.xlsx', '.xls', '.csv',
    '.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff'
}
ALLOWED_MIME_TYPES = {
    'text/plain', 'application/pdf', 'application/msword',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'application/vnd.ms-excel', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    'text/csv', 'image/png', 'image/jpeg', 'image/gif', 'image/bmp', 'image/tiff'
}

def validate_file_security(file: UploadFile) -> None:
    """Validate file for security concerns."""
    if not file.filename:
        raise HTTPException(status_code=422, detail="No filename provided")
    
    # Check file size
    if file.size and file.size > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail=f"File too large. Maximum size: {MAX_FILE_SIZE // (1024*1024)}MB")
    
    # Validate file extension
    file_extension = Path(file.filename).suffix.lower()
    if file_extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=422, 
            detail=f"File type not allowed. Allowed types: {', '.join(ALLOWED_EXTENSIONS)}"
        )
    
    # Validate MIME type
    if file.content_type and file.content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(status_code=422, detail="Invalid file type")
    
    # Additional security checks
    filename = file.filename.lower()
    dangerous_patterns = ['../', '..\\', '/etc/', '/var/', '/usr/', 'c:\\', '.exe', '.bat', '.cmd', '.scr']
    if any(pattern in filename for pattern in dangerous_patterns):
        raise HTTPException(status_code=422, detail="Potentially dangerous filename detected")

@router.post("/upload", response_model=file_schema.FileUploadResponse)
def upload_file(file: UploadFile = FastAPIFile(...), user=Depends(verify_jwt), db: Session = Depends(get_db)):
    """
    API upload file:
    - Nhận file upload từ client và user_id.
    - Upload file lên MinIO.
    - Lưu link file trên MinIO vào database.
    - Trả về thông tin file vừa upload.
    """
    try:
        # Security validation
        validate_file_security(file)
        
        # Sanitize filename
        safe_filename = "".join(c for c in file.filename if c.isalnum() or c in '._- ').strip()
        if not safe_filename:
            safe_filename = "uploaded_file"
        
        # Generate unique filename to avoid conflicts
        file_extension = Path(file.filename).suffix.lower()
        unique_filename = f"{uuid4().hex}_{safe_filename}"

        # Upload file to MinIO
        file.file.seek(0)
        url = upload_file_to_minio(
            file.file, 
            unique_filename, 
            content_type=file.content_type or "application/octet-stream"
        )

        # Create File object and save to database
        file_obj = File(
            user_id=user.user.id,
            filename=safe_filename,
            file_path=url,
            created_at=datetime.utcnow()
        )
        db.add(file_obj)
        db.commit()
        db.refresh(file_obj)

        logger.info(f"File uploaded successfully: {safe_filename} by user {user.user.id}")
        
        return file_schema.FileUploadResponse(
            file_id=file_obj.file_id,
            filename=file_obj.filename,
            url=file_obj.file_path,
            created_at=file_obj.created_at
        )
    
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Error uploading file: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Upload failed due to server error")

@router.post("/extract", response_model=file_schema.FileExtractResponse)
def extract_file_api(body: dict, user=Depends(verify_jwt), db: Session = Depends(get_db)):
    """
    API extract text từ file đã upload.
    Only allows extraction for files owned by the authenticated user.
    """
    # Input validation
    if not isinstance(body, dict):
        raise HTTPException(status_code=422, detail="Request body must be a JSON object")
    
    file_id = body.get("file_id")
    if not file_id:
        raise HTTPException(status_code=422, detail="file_id is required")
    
    if not isinstance(file_id, int) or file_id <= 0:
        raise HTTPException(status_code=422, detail="file_id must be a positive integer")
    
    try:
        # Get file information from DB with user ownership check
        file_obj = db.query(File).filter(
            File.file_id == file_id,
            File.user_id == user.user.id  # Security: ensure user owns the file
        ).first()
        
        if not file_obj:
            raise HTTPException(status_code=404, detail="File not found or access denied")
        
        # If already extracted, return cached result
        if file_obj.extracted_text:
            return file_schema.FileExtractResponse(
                file_id=file_obj.file_id,
                extracted_text=file_obj.extracted_text
            )
        
        file_url = file_obj.file_path
        parsed = urlparse(file_url)
        
        # Validate URL
        if not all([parsed.scheme, parsed.netloc]):
            raise HTTPException(status_code=400, detail="Invalid file URL")
        
        # Determine file extension from filename
        file_extension = Path(file_obj.filename).suffix.lower()
        if not file_extension:
            file_extension = ".pdf"  # default
        # Extract text based on URL type
        # if parsed.scheme in ("http", "https"):
        #     # Download file to temp location and extract
        #     with tempfile.NamedTemporaryFile(delete=False, suffix=file_extension) as tmp:
        #         try:
        #             response = requests.get(file_url)
        #             response.raise_for_status()
        #             tmp.write(response.content)
        #             tmp.flush()
        #
        #             extracted_text = file_extractor_service.extract_text(tmp.name, file_extension)
        #         finally:
        #             # Clean up temp file
        #             if os.path.exists(tmp.name):
        #                 os.unlink(tmp.name)
        # else:
        #     # Local file path
        extracted_text = file_extractor_service.extract_text(file_url, file_extension)
        
        if not extracted_text:
            raise HTTPException(status_code=422, detail="Could not extract text from file")
        
        # Lưu extracted_text vào DB
        file_obj.extracted_text = extracted_text
        db.commit()
        
        return file_schema.FileExtractResponse(
            file_id=file_obj.file_id,
            extracted_text=extracted_text
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error extracting file {file_id}: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Extraction failed: {str(e)}")

@router.get("", response_model=list[file_schema.FileResponse])
def get_files(user_id: str, db: Session = Depends(get_db)):
    """
    API lấy danh sách file đã upload của người dùng.
    """
    try:
        files = db.query(File).filter(File.user_id == user_id).all()
        return [file_schema.FileResponse(
            file_id=file.file_id,
            filename=file.filename,
            file_path=file.file_path,
            created_at=file.created_at,
            extracted_text=file.extracted_text
        ) for file in files]
    
    except Exception as e:
        logger.error(f"Error getting files for user {user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get files: {str(e)}")

@router.delete("/file/{file_id}", response_model=file_schema.FileResponse)
def delete_file(file_id: int, db: Session = Depends(get_db)):
    """
    API xóa file đã upload.
    """
    try:
        file_obj = db.query(File).filter(File.file_id == file_id).first()
        if not file_obj:
            raise HTTPException(status_code=404, detail="File not found")
        
        # Extract filename from URL for MinIO deletion
        file_url = file_obj.file_path
        parsed = urlparse(file_url)
        
        # Get filename from URL path (last part after /)
        filename_from_url = parsed.path.split('/')[-1] if parsed.path else None
        
        if filename_from_url:
            # Try to delete from MinIO
            try:
                success = delete_file_from_minio(filename_from_url)
                if not success:
                    logger.warning(f"Could not delete file {filename_from_url} from MinIO")
            except Exception as e:
                logger.error(f"Error deleting from MinIO: {str(e)}")
                # Continue with DB deletion even if MinIO fails
        
        # Store response data before deletion
        response_data = file_schema.FileResponse(
            file_id=file_obj.file_id,
            filename=file_obj.filename,
            file_path=file_obj.file_path,
            created_at=file_obj.created_at,
            extracted_text=file_obj.extracted_text
        )
        
        # Delete from database
        db.delete(file_obj)
        db.commit()
        
        return response_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting file {file_id}: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Delete failed: {str(e)}")