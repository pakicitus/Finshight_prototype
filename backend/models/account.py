from datetime import datetime, timezone
from sqlalchemy import Column, DateTime, ForeignKey, Numeric, String
from backend.db import Base


class Account(Base):
    __tablename__ = "accounts"

    id = Column(String, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    name = Column(String, nullable=False)
    account_type = Column(String, default="savings")
    balance = Column(Numeric(12, 2), default=0.0)
    currency = Column(String, default="INR")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
