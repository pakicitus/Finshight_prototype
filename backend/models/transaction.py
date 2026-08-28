from datetime import datetime, timezone
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Numeric, String
from backend.db import Base


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(String, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    account_id = Column(String, ForeignKey("accounts.id"), nullable=True)
    amount = Column(Numeric(12, 2), nullable=False)  # Positive = income, Negative = expense
    category = Column(String, nullable=False, index=True)
    description = Column(String, nullable=True)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    is_recurring = Column(Boolean, default=False)
    merchant = Column(String, nullable=True)
