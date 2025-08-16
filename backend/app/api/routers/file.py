

from fastapi import APIRouter, Depends, UploadFile, File as FastAPIFile
from app.schemas import file as file_schema
from app.database.database import get_db
from sqlalchemy.orm import Session
from backend.app.services.extraction_service import file_extractor_service
from app.models.file import File
from backend.app.services.minio_service import upload_file_to_minio

router = APIRouter(prefix="/file", tags=["File"])  # Khởi tạo router với prefix /file


@router.post("/upload", response_model=file_schema.FileUploadResponse)
def upload_file(user_id: int, file: UploadFile = FastAPIFile(...), db: Session = Depends(get_db)):
    """
    API upload file:
    - Nhận file upload từ client và user_id.
    - Upload file lên MinIO.
    - Lưu link file trên MinIO vào database.
    - Trả về thông tin file vừa upload.
    """
    from uuid import uuid4
    from datetime import datetime

    # Sinh tên file duy nhất để tránh trùng lặp
    filename = f"{uuid4().hex}_{file.filename}"

    # Upload file lên MinIO
    file.file.seek(0)
    url = upload_file_to_minio(file.file, filename, content_type=file.content_type or "application/pdf")

    # Tạo đối tượng File và lưu vào database (lưu url thay vì file_path)
    file_obj = File(
        user_id=user_id,
        filename=file.filename,
        file_path=url,  # Lưu link MinIO
        created_at=datetime.utcnow()
    )
    db.add(file_obj)
    db.commit()
    db.refresh(file_obj)

    return file_schema.FileUploadResponse(
        file_id=file_obj.file_id,
        filename=file_obj.filename,
        created_at=file_obj.created_at
    )

# API duy nhất: extract text từ file_url (MinIO hoặc local)

@router.post("/extract", response_model=file_schema.FileExtractResponse)
def extract_file_api(file_id: int, db: Session = Depends(get_db)):
    import tempfile
    import requests
    from urllib.parse import urlparse
    # Lấy thông tin file từ DB
    file_obj = db.query(File).filter(File.file_id == file_id).first()
    if not file_obj:
        raise Exception("File not found")
    file_url = file_obj.file_path
    parsed = urlparse(file_url)
    if parsed.scheme in ("http", "https"):
        with tempfile.NamedTemporaryFile(delete=True, suffix=".pdf") as tmp:
            r = requests.get(file_url)
            r.raise_for_status()
            tmp.write(r.content)
            tmp.flush()
            extracted_text = file_extractor_service.extract_text(tmp.name)
    else:
        extracted_text = file_extractor_service.extract_text(file_url)
    if not extracted_text:
        raise Exception("Could not extract text from file")
    # Lưu extracted_text vào DB
    file_obj.extracted_text = extracted_text
    db.commit()
    return file_schema.FileExtractResponse(
        file_id=file_obj.file_id,
        extracted_text=extracted_text
    )
