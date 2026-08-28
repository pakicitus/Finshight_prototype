"""
FinSight AI Router
==================
Exposes the FinSight conversational AI pipeline through FastAPI HTTP endpoints:
  POST /ask
  POST /api/v1/ask

ARCHITECTURAL RULES:
- The router is strictly a transport and serialization boundary.
- Zero financial calculations are performed here.
- The deterministic financial engine is the only source of financial truth.
- Database session lifecycle is managed by FastAPI dependency injection.
"""

from typing import Any, Dict
# pyrefly: ignore [missing-import]
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ai.pipeline import run_finSight_pipeline, serialize_data_boundary
from backend.db import get_db
from backend.schemas import AskRequest, AskResponse

router = APIRouter(tags=["ai"])


@router.post("/ask", response_model=AskResponse)
@router.post("/api/v1/ask", response_model=AskResponse)
def ask_finsight(
    request: AskRequest,
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    Translates user natural language query into deterministic financial facts and a grounded explanation.
    """
    result = run_finSight_pipeline(
        user_id=request.user_id,
        query=request.query,
        context=request.context,
        db=db,
    )

    return {
        "answer_text": result.get("answer_text", ""),
        "structured_data": serialize_data_boundary(result.get("structured_data", {})),
    }
