from decimal import Decimal
from typing import Optional
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from backend.db import get_db
from backend.engine.financial_engine import project_goal_completion
from backend.models.goal import Goal

router = APIRouter(prefix="/goals", tags=["goals"])


@router.get("/")
def list_goals(user_id: str = "demo_user", db: Session = Depends(get_db)):
    return db.query(Goal).filter(Goal.user_id == user_id).all()


@router.get("/{goal_id}/projection")
def get_projection(
    goal_id: str,
    hypothetical_contribution: Optional[float] = None,
    db: Session = Depends(get_db),
):
    return project_goal_completion(goal_id, db, hypothetical_contribution=hypothetical_contribution)
