import uuid
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import Column, String, DateTime, Integer, func
from app.database.database import Base

class File(Base):
    __tablename__ = "files"
    file_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(UUID(as_uuid=True), nullable=False, default=uuid.uuid4)  # kiểu UUID
    filename = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    extracted_text = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
