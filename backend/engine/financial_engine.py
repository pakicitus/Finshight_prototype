"""
FinSight Deterministic Financial Engine
======================================
The single source of financial truth.
Authoritative calculation of balances, spending breakdowns, percentages,
affordability decisions, goal projections, and algorithmic insights.
"""

from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Dict, List, Optional
from sqlalchemy import func
from sqlalchemy.orm import Session

from backend.models.bill import Bill
from backend.models.goal import Goal
from backend.models.transaction import Transaction

CATEGORIES = [
    "Food",
    "Transport",
    "Shopping",
    "Bills",
    "Entertainment",
    "Healthcare",
    "Education",
    "Other",
]


def get_balance(user_id: str, db: Session) -> Dict[str, Any]:
    """
    Fetches authoritative balance derived strictly from transaction history.
    DO NOT use accounts.balance as authoritative.
    """
    total_balance_query = (
        db.query(func.coalesce(func.sum(Transaction.amount), 0.0))
        .filter(Transaction.user_id == str(user_id))
        .scalar()
    )
    balance_decimal = Decimal(str(total_balance_query)).quantize(Decimal("0.01"))
    as_of_time = datetime.now(timezone.utc)

    return {
        "balance": balance_decimal,
        "as_of": as_of_time,
    }


def get_spending_summary(
    user_id: str,
    db: Session,
    period: str = "this_month",
) -> Dict[str, Any]:
    """
    Retrieves spending breakdown and deterministic percentage changes vs previous period.
    The engine calculates all percentages. The LLM must NEVER calculate them.
    """
    now = datetime.now(timezone.utc)

    # Determine date windows
    if period == "last_month":
        # First day of last month
        year = now.year if now.month > 1 else now.year - 1
        month = now.month - 1 if now.month > 1 else 12
        start_curr = datetime(year, month, 1, tzinfo=timezone.utc)
        # End of last month
        end_curr = datetime(now.year, now.month, 1, tzinfo=timezone.utc)
        # Prior month for comparison
        prev_year = year if month > 1 else year - 1
        prev_month = month - 1 if month > 1 else 12
        start_prev = datetime(prev_year, prev_month, 1, tzinfo=timezone.utc)
        end_prev = start_curr
    else:  # default: this_month
        start_curr = datetime(now.year, now.month, 1, tzinfo=timezone.utc)
        end_curr = now
        prev_year = now.year if now.month > 1 else now.year - 1
        prev_month = now.month - 1 if now.month > 1 else 12
        start_prev = datetime(prev_year, prev_month, 1, tzinfo=timezone.utc)
        end_prev = start_curr

    # Fetch current period expenses (amount < 0)
    curr_txs = (
        db.query(Transaction)
        .filter(
            Transaction.user_id == str(user_id),
            Transaction.amount < 0,
            Transaction.timestamp >= start_curr,
            Transaction.timestamp <= end_curr,
        )
        .all()
    )

    # Fetch previous period expenses
    prev_txs = (
        db.query(Transaction)
        .filter(
            Transaction.user_id == str(user_id),
            Transaction.amount < 0,
            Transaction.timestamp >= start_prev,
            Transaction.timestamp < end_prev,
        )
        .all()
    )

    by_category: Dict[str, Decimal] = {cat: Decimal("0.00") for cat in CATEGORIES}
    prev_by_category: Dict[str, Decimal] = {cat: Decimal("0.00") for cat in CATEGORIES}

    curr_total = Decimal("0.00")
    for tx in curr_txs:
        cat = tx.category.capitalize() if tx.category else "Other"
        if cat not in by_category:
            cat = "Other"
        amt = abs(Decimal(str(tx.amount)))
        by_category[cat] = (by_category[cat] + amt).quantize(Decimal("0.01"))
        curr_total = (curr_total + amt).quantize(Decimal("0.01"))

    prev_total = Decimal("0.00")
    for tx in prev_txs:
        cat = tx.category.capitalize() if tx.category else "Other"
        if cat not in prev_by_category:
            cat = "Other"
        amt = abs(Decimal(str(tx.amount)))
        prev_by_category[cat] = (prev_by_category[cat] + amt).quantize(Decimal("0.01"))
        prev_total = (prev_total + amt).quantize(Decimal("0.01"))

    # Compute vs_last_period_pct for total and each category
    vs_last_period_pct: Dict[str, Decimal] = {}
    if prev_total > Decimal("0.00"):
        vs_last_period_pct["total"] = (
            ((curr_total - prev_total) / prev_total) * Decimal("100")
        ).quantize(Decimal("0.01"))
    else:
        vs_last_period_pct["total"] = Decimal("0.00")

    for cat in CATEGORIES:
        prev_c = prev_by_category[cat]
        curr_c = by_category[cat]
        if prev_c > Decimal("0.00"):
            pct = (((curr_c - prev_c) / prev_c) * Decimal("100")).quantize(Decimal("0.01"))
        else:
            pct = Decimal("0.00")
        vs_last_period_pct[cat] = pct

    return {
        "period": period,
        "total": curr_total,
        "by_category": by_category,
        "vs_last_period_pct": vs_last_period_pct,
    }


def check_affordability(
    user_id: str,
    amount: Any,
    db: Session,
) -> Dict[str, Any]:
    """
    Evaluates whether the user can safely afford a proposed purchase amount.
    The engine decides affordability. The LLM must NEVER independently decide affordability.
    """
    purchase_amt = Decimal(str(amount)).quantize(Decimal("0.01"))
    balance_data = get_balance(user_id, db)
    current_balance = balance_data["balance"]

    # Sum of upcoming unpaid bills
    unpaid_bills_sum = (
        db.query(func.coalesce(func.sum(Bill.amount), 0.0))
        .filter(
            Bill.user_id == str(user_id),
            Bill.is_paid == False,
        )
        .scalar()
    )
    upcoming_bills = Decimal(str(unpaid_bills_sum)).quantize(Decimal("0.01"))

    # Calculate safe balance
    safe_balance = current_balance - upcoming_bills
    can_afford = (current_balance - purchase_amt) >= upcoming_bills

    balance_after = (
        (current_balance - purchase_amt).quantize(Decimal("0.01"))
        if can_afford
        else current_balance
    )

    savings_goal_impact_months = Decimal("0.0")

    if can_afford:
        reasoning_facts = [
            "Purchase leaves sufficient balance",
            "Remaining cushion after purchase exceeds upcoming bills",
        ]
    else:
        reasoning_facts = [
            "Purchase exceeds safe discretionary balance",
            "Upcoming fixed bills would be compromised",
        ]

    return {
        "can_afford": bool(can_afford),
        "balance_after": balance_after,
        "upcoming_bills": upcoming_bills,
        "savings_goal_impact_months": savings_goal_impact_months,
        "reasoning_facts": reasoning_facts,
    }


def project_goal_completion(
    goal_id: Any,
    db: Session,
    hypothetical_contribution: Optional[Any] = None,
) -> Dict[str, Any]:
    """
    Projects savings goal timeline and hypothetical impact.
    The engine calculates the projection.
    """
    goal = db.query(Goal).filter(Goal.id == str(goal_id)).first()
    if not goal:
        return {
            "current_months_remaining": Decimal("0.0"),
            "hypothetical_months_remaining": None,
        }

    target = Decimal(str(goal.target_amount))
    current = Decimal(str(goal.current_amount))
    remaining = max(Decimal("0.0"), target - current)

    base_contrib = (
        Decimal(str(goal.monthly_contribution))
        if goal.monthly_contribution and Decimal(str(goal.monthly_contribution)) > Decimal("0.0")
        else Decimal("10000.00")
    )

    if remaining == Decimal("0.0"):
        current_months = Decimal("0.0")
    else:
        current_months = (remaining / base_contrib).quantize(Decimal("0.1"))

    if hypothetical_contribution is not None and Decimal(str(hypothetical_contribution)) > Decimal("0.0"):
        extra = Decimal(str(hypothetical_contribution))
        total_rate = base_contrib + extra
        if remaining == Decimal("0.0"):
            hypo_months = Decimal("0.0")
        else:
            hypo_months = (remaining / total_rate).quantize(Decimal("0.1"))
    else:
        hypo_months = None

    return {
        "current_months_remaining": current_months,
        "hypothetical_months_remaining": hypo_months,
    }


def get_insights(user_id: str, db: Session) -> List[Dict[str, Any]]:
    """
    Returns structured insights discovered from actual transaction data.
    """
    from backend.engine.insights import generate_insights
    return generate_insights(user_id, db)
