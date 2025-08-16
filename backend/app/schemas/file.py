from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class FileUploadRequest(BaseModel):
    filename: str

class FileUploadResponse(BaseModel):
    file_id: int
    filename: str
    created_at: datetime

class FileExtractResponse(BaseModel):
    file_id: int
    extracted_text: Optional[str]

class FileOCRRequest(BaseModel):
    file_id: int

class FileOCRResponse(BaseModel):
    file_id: int
    extracted_text: str

class FileResponse(BaseModel):
    file_id: int
    filename: str
    file_path: str
    created_at: datetime
