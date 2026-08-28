from datetime import datetime, timezone
from sqlalchemy import Column, DateTime, ForeignKey, Numeric, String
from backend.db import Base


class Goal(Base):
    __tablename__ = "goals"

    id = Column(String, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    name = Column(String, nullable=False, index=True)
    target_amount = Column(Numeric(12, 2), nullable=False)
    current_amount = Column(Numeric(12, 2), default=0.0)
    monthly_contribution = Column(Numeric(12, 2), default=0.0)
    target_date = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
