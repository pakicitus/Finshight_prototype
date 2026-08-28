"""
FinSight AI ↔ Real Financial Engine End-to-End Integration Tests
================================================================
Verifies all 6 real data flows against the real SQLite database and real financial engine.
"""

from decimal import Decimal
import json
from unittest.mock import MagicMock
# pyrefly: ignore [missing-import]
import pytest

from ai.pipeline import run_finSight_pipeline
from backend.db import SessionLocal
from backend.engine.financial_engine import (
    get_balance,
    get_spending_summary,
    check_affordability,
    project_goal_completion,
    get_insights,
)
from backend.seed.generate_synthetic_data import seed_database


@pytest.fixture(autouse=True, scope="module")
def setup_seeded_db():
    """Seed real SQLite database before running integration tests."""
    seed_database()


def create_mock_router_client(tool_name=None, tool_args=None, content=None):
    """Build mock client for intent router."""
    mock_client = MagicMock()
    mock_message = MagicMock()

    if tool_name:
        mock_tool_call = MagicMock()
        mock_tool_call.function.name = tool_name
        mock_tool_call.function.arguments = json.dumps(tool_args or {})
        mock_message.tool_calls = [mock_tool_call]
        mock_message.content = None
    else:
        mock_message.tool_calls = None
        mock_message.content = content or ""

    mock_choice = MagicMock()
    mock_choice.message = mock_message
    mock_response = MagicMock()
    mock_response.choices = [mock_choice]
    mock_client.chat.completions.create.return_value = mock_response
    return mock_client


def create_mock_explainer_client(explanation_text):
    """Build mock client for explainer."""
    mock_client = MagicMock()
    mock_choice = MagicMock()
    mock_choice.message.content = explanation_text
    mock_response = MagicMock()
    mock_response.choices = [mock_choice]
    mock_client.chat.completions.create.return_value = mock_response
    return mock_client


def test_real_flow_1_balance():
    """
    Flow 1: 'What's my balance?'
    Expected:
    router -> get_balance -> real SQLite data -> explainer.
    The authoritative seeded balance is ₹138,372.00.
    """
    db = SessionLocal()
    try:
        router_client = create_mock_router_client(tool_name="get_balance", tool_args={})
        explainer_client = create_mock_explainer_client(
            "Your current account balance is ₹138,372.00 as of today."
        )

        result = run_finSight_pipeline(
            user_id="demo_user",
            query="What's my balance?",
            db=db,
            router_client=router_client,
            explainer_client=explainer_client,
        )

        assert "answer_text" in result
        assert "structured_data" in result
        assert result["structured_data"]["balance"] == Decimal("138372.00")
        assert "138,372" in result["answer_text"] or "138372" in result["answer_text"]
    finally:
        db.close()


def test_real_flow_2_food_spending():
    """
    Flow 2: 'How much did I spend on food this month?'
    Expected:
    router -> get_spending_summary (no category arg passed to real engine) -> real transaction data -> explainer.
    Food spending this month is ₹12,400.00.
    """
    db = SessionLocal()
    try:
        router_client = create_mock_router_client(
            tool_name="get_spending_summary",
            tool_args={"period": "this_month", "category": "food"},
        )
        explainer_client = create_mock_explainer_client(
            "You have spent a total of ₹12,400.00 on Food this month."
        )

        result = run_finSight_pipeline(
            user_id="demo_user",
            query="How much did I spend on food this month?",
            db=db,
            router_client=router_client,
            explainer_client=explainer_client,
        )

        assert "answer_text" in result
        assert "structured_data" in result
        assert result["structured_data"]["by_category"]["Food"] == Decimal("12400.00")
        assert "12,400" in result["answer_text"] or "12400" in result["answer_text"]
    finally:
        db.close()


def test_real_flow_3_affordability_safe_purchase():
    """
    Flow 3: 'Can I afford a phone for ₹10000?'
    Expected:
    router -> check_affordability (user_id, amount, db) -> real engine -> explainer.
    Balance after purchase is ₹128,372.00.
    """
    db = SessionLocal()
    try:
        router_client = create_mock_router_client(
            tool_name="check_affordability",
            tool_args={"amount": 10000, "item_description": "phone"},
        )
        explainer_client = create_mock_explainer_client(
            "Yes, you can afford the phone for ₹10,000. Your remaining balance will be ₹128,372.00."
        )

        result = run_finSight_pipeline(
            user_id="demo_user",
            query="Can I afford a phone for ₹10000?",
            db=db,
            router_client=router_client,
            explainer_client=explainer_client,
        )

        assert "answer_text" in result
        assert "structured_data" in result
        assert result["structured_data"]["can_afford"] is True
        assert result["structured_data"]["balance_after"] == Decimal("128372.00")
        assert result["structured_data"]["upcoming_bills"] == Decimal("6500.00")
        assert "128,372" in result["answer_text"] or "128372" in result["answer_text"]
    finally:
        db.close()


def test_real_flow_4_emergency_fund_goal_resolution():
    """
    Flow 4: 'When will I reach my emergency fund?'
    Expected:
    router -> resolve Emergency Fund goal -> project_goal_completion (goal_id, db) -> explainer.
    Months remaining: 6.0 months.
    """
    db = SessionLocal()
    try:
        router_client = create_mock_router_client(
            tool_name="project_goal_completion",
            tool_args={"goal_name_or_id": "emergency fund"},
        )
        explainer_client = create_mock_explainer_client(
            "You are on track to complete your Emergency Fund in 6.0 months."
        )

        result = run_finSight_pipeline(
            user_id="demo_user",
            query="When will I reach my emergency fund?",
            db=db,
            router_client=router_client,
            explainer_client=explainer_client,
        )

        assert "answer_text" in result
        assert "structured_data" in result
        assert result["structured_data"]["current_months_remaining"] == Decimal("6.0")
        assert "6.0" in result["answer_text"] or "6" in result["answer_text"]
    finally:
        db.close()


def test_real_flow_5_insights():
    """
    Flow 5: 'Why did I spend more this month?'
    Expected:
    router -> get_insights -> real transaction-derived insights -> explainer.
    Food spending increase of 21.94%.
    """
    db = SessionLocal()
    try:
        router_client = create_mock_router_client(
            tool_name="get_insights",
            tool_args={},
        )
        explainer_client = create_mock_explainer_client(
            "Your food spending increased by 21.94% this month."
        )

        result = run_finSight_pipeline(
            user_id="demo_user",
            query="Why did I spend more this month?",
            db=db,
            router_client=router_client,
            explainer_client=explainer_client,
        )

        assert "answer_text" in result
        assert "structured_data" in result
        assert isinstance(result["structured_data"], list)
        assert len(result["structured_data"]) >= 1
        food_insight = next(
            (i for i in result["structured_data"] if i.get("category") == "Food"), None
        )
        assert food_insight is not None
        assert food_insight["pct"] == Decimal("21.94")
        assert "21.94" in result["answer_text"]
    finally:
        db.close()


def test_real_flow_6_missing_affordability_amount_clarification():
    """
    Flow 6: 'Can I afford it?' (no price/amount specified)
    Expected:
    Clarification returned without calling financial engine.
    """
    router_client = create_mock_router_client(
        tool_name="check_affordability",
        tool_args={"item_description": "it"},
    )

    result = run_finSight_pipeline(
        user_id="demo_user",
        query="Can I afford it?",
        router_client=router_client,
    )

    assert "answer_text" in result
    assert "structured_data" in result
    assert result["structured_data"]["status"] == "clarification_needed"
    assert "cost" in result["answer_text"].lower() or "how much" in result["answer_text"].lower()


def test_real_flow_7_invalid_user_id():
    """
    Flow 7: Missing or invalid user ID.
    Expected:
    Safe error response.
    """
    result = run_finSight_pipeline(user_id="", query="What's my balance?")
    assert result["structured_data"]["status"] == "error"
    assert "user_id is required" in result["structured_data"]["message"]


def test_real_flow_8_unresolved_goal_clarification():
    """
    Flow 8: Query about non-existent goal -> clarification needed (never invent goal ID).
    """
    db = SessionLocal()
    try:
        router_client = create_mock_router_client(
            tool_name="project_goal_completion",
            tool_args={"goal_name_or_id": "nonexistent yacht goal"},
        )
        result = run_finSight_pipeline(
            user_id="demo_user",
            query="When will I reach my nonexistent yacht goal?",
            db=db,
            router_client=router_client,
        )

        assert result["structured_data"]["status"] == "clarification_needed"
        assert "savings goal" in result["answer_text"].lower()
    finally:
        db.close()
