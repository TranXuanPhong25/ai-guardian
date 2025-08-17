from sqlalchemy import Column, ForeignKey, DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database.database import Base
import uuid

class MessageFile(Base):
    __tablename__ = "message_files"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    message_id = Column(UUID(as_uuid=True), ForeignKey("messages.id", ondelete="CASCADE"), nullable=False)
    file_id = Column("file_id", ForeignKey("files.file_id"), nullable=False)
    created_at = Column(DateTime, server_default=func.now())

    # Relationships
    message = relationship("Message", back_populates="attached_files")
    file = relationship("File")
