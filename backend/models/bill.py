from datetime import datetime, timezone
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Numeric, String
from backend.db import Base


class Bill(Base):
    __tablename__ = "bills"

    id = Column(String, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    name = Column(String, nullable=False)
    amount = Column(Numeric(12, 2), nullable=False)
    due_date = Column(DateTime, nullable=False)
    category = Column(String, default="Bills")
    is_paid = Column(Boolean, default=False)
    is_recurring = Column(Boolean, default=True)
