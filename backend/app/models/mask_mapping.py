from sqlalchemy import Column, Integer, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
from app.database.database import Base
import uuid
from sqlalchemy.dialects.postgresql import UUID
class MaskMapping(Base):
    __tablename__ = "mask_mappings"
    session_id = Column(UUID(as_uuid=True), ForeignKey("chat_sessions.id"), primary_key=True)
    mapping = Column(JSONB, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
