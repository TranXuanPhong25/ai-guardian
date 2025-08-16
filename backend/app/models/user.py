from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func
from app.database.database import Base
from sqlalchemy.dialects.postgresql import UUID

class User(Base):
    __tablename__ = "users"
    __table_args__ = {"schema": "auth"}  # schema must be set
    id = Column(UUID(as_uuid=True), primary_key=True)
