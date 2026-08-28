"""
FinSight Algorithmic Insights Engine
Extracts deterministic financial insights from transaction data.
"""

from decimal import Decimal
from typing import Any, Dict, List
from sqlalchemy.orm import Session


def generate_insights(user_id: str, db: Session) -> List[Dict[str, Any]]:
    """
    Generates algorithmic insights based on spending changes and transaction patterns.
    """
    from backend.engine.financial_engine import get_spending_summary

    insights: List[Dict[str, Any]] = []
    spending_summary = get_spending_summary(user_id, db, period="this_month")
    vs_last = spending_summary.get("vs_last_period_pct", {})
    by_category = spending_summary.get("by_category", {})

    # Detect spending increases (> 10%)
    for category, pct_val in vs_last.items():
        if category == "total":
            continue
        if pct_val > Decimal("10.0"):
            insights.append({
                "type": "spending_increase",
                "category": category,
                "pct": pct_val,
                "period": "this_month",
            })

    # If no significant category spike, provide total spending trend if increased
    if not insights and vs_last.get("total", Decimal("0")) > Decimal("5.0"):
        insights.append({
            "type": "spending_increase",
            "category": "total",
            "pct": vs_last["total"],
            "period": "this_month",
        })

    return insights
