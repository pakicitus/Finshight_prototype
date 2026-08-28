from datetime import datetime, timezone
from sqlalchemy import Column, DateTime, ForeignKey, String, Text
from backend.db import Base


class Document(Base):
    __tablename__ = "documents"

    id = Column(String, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    title = Column(String, nullable=False)
    content = Column(Text, nullable=True)
    doc_type = Column(String, default="receipt")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
