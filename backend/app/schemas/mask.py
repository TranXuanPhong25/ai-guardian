from pydantic import BaseModel
from typing import Dict, Any
from datetime import datetime


class MaskRequest(BaseModel):
    session_id: str  # Accept UUID as string
    content: str


class UnmaskRequest(BaseModel):
    session_id: str  # Accept UUID as string
    content: str


class MaskMappingResponse(BaseModel):
    session_id: str  # Accept UUID as string
    mapping: Dict[str, Any]
    created_at: datetime

class ValidateSensitiveRequest(BaseModel):
    content: str

class ValidateSensitiveResponse(BaseModel):
    is_sensitive: bool
    message: str
