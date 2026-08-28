from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from backend.db import get_db
from backend.engine.financial_engine import get_balance, get_spending_summary, get_insights

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/balance")
def read_balance(user_id: str = "demo_user", db: Session = Depends(get_db)):
    return get_balance(user_id, db)


@router.get("/spending")
def read_spending(user_id: str = "demo_user", period: str = "this_month", db: Session = Depends(get_db)):
    return get_spending_summary(user_id, db, period=period)


@router.get("/insights")
def read_insights(user_id: str = "demo_user", db: Session = Depends(get_db)):
    return get_insights(user_id, db)
