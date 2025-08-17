from sqlalchemy import Column, Integer, String, Text, UniqueConstraint, Index
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class PiiMapping(Base):
    __tablename__ = "pii_mappings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    entity_type = Column(String(50), nullable=False)
    original_value = Column(Text, nullable=False)
    pseudonymized_value = Column(Text, nullable=False)
    hash_key = Column(Text, nullable=False)

    __table_args__ = (
        UniqueConstraint("entity_type", "original_value", name="unique_entity_value"),
        Index("idx_entity_hash", "entity_type", "hash_key"),
    )
