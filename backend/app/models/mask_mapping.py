from sqlalchemy import Column, Integer, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
from app.database.database import Base

class MaskMapping(Base):
    __tablename__ = "mask_mappings"
    conversation_id = Column(Integer, ForeignKey("conversations.conversation_id"), primary_key=True)
    mapping = Column(JSONB, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
