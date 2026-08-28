"""
Unit tests for FinSight AI Orchestration Pipeline.
Verifies end-to-end orchestration across router, real financial engine, and explainer.
All LLM API calls are strictly mocked.
"""

from decimal import Decimal
import json
from unittest.mock import MagicMock
# pyrefly: ignore [missing-import]
import pytest

from ai.pipeline import run_finSight_pipeline
from backend.db import SessionLocal
from backend.seed.generate_synthetic_data import seed_database


@pytest.fixture(autouse=True, scope="module")
def setup_test_database():
    """Ensure seeded database exists before running pipeline tests."""
    seed_database()


def build_mock_router_client(tool_name=None, tool_args=None, content=None):
    """Construct mock client for intent router."""
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


def build_mock_explainer_client(explanation_text):
    """Construct mock client for explainer."""
    mock_client = MagicMock()
    mock_choice = MagicMock()
    mock_choice.message.content = explanation_text
    mock_response = MagicMock()
    mock_response.choices = [mock_choice]
    mock_client.chat.completions.create.return_value = mock_response
    return mock_client


def test_1_balance_question():
    """
    Test 1: Balance inquiry pipeline flow.
    Query: 'What is my balance?'
    Expected: Engine returns balance data from real database, explainer explains it.
    """
    router_client = build_mock_router_client(tool_name="get_balance", tool_args={})
    explainer_client = build_mock_explainer_client("Your current balance is ₹138,372 as of today.")

    result = run_finSight_pipeline(
        user_id="demo_user",
        query="What is my balance?",
        router_client=router_client,
        explainer_client=explainer_client,
    )

    assert "answer_text" in result
    assert "structured_data" in result
    assert "138,372" in result["answer_text"] or "138372" in result["answer_text"]
    assert result["structured_data"]["balance"] == Decimal("138372.00")
    assert "as_of" in result["structured_data"]


def test_2_affordability_question():
    """
    Test 2: Affordability evaluation pipeline flow.
    Query: 'Can I afford a phone for ₹10000?'
    Expected: Real engine evaluates affordability, explainer articulates the result.
    """
    router_client = build_mock_router_client(
        tool_name="check_affordability",
        tool_args={"amount": 10000, "item_description": "phone"},
    )
    explainer_client = build_mock_explainer_client(
        "Yes, you can afford the phone for ₹10,000. Your remaining balance will be ₹128,372."
    )

    result = run_finSight_pipeline(
        user_id="demo_user",
        query="Can I afford a phone for ₹10000?",
        router_client=router_client,
        explainer_client=explainer_client,
    )

    assert "answer_text" in result
    assert "structured_data" in result
    assert result["structured_data"]["can_afford"] is True
    assert result["structured_data"]["balance_after"] == Decimal("128372.00")
    assert result["structured_data"]["upcoming_bills"] == Decimal("6500.00")
    assert "afford" in result["answer_text"].lower()


def test_3_spending_question():
    """
    Test 3: Spending breakdown inquiry pipeline flow.
    Query: 'How much did I spend on food this month?'
    Expected: Engine returns category spending, explainer narrates.
    """
    router_client = build_mock_router_client(
        tool_name="get_spending_summary",
        tool_args={"period": "this_month", "category": "food"},
    )
    explainer_client = build_mock_explainer_client(
        "You spent a total of ₹12,400 on Food this month."
    )

    result = run_finSight_pipeline(
        user_id="demo_user",
        query="How much did I spend on food this month?",
        router_client=router_client,
        explainer_client=explainer_client,
    )

    assert "answer_text" in result
    assert "structured_data" in result
    assert result["structured_data"]["by_category"]["Food"] == Decimal("12400.00")
    assert "12,400" in result["answer_text"] or "12400" in result["answer_text"]
    assert "Food" in result["answer_text"]


def test_4_missing_affordability_amount():
    """
    Test 4: Clarification triggered when purchase amount is omitted.
    Query: 'Can I afford it?'
    Expected: Router detects missing amount and requests clarification without invoking engine.
    """
    router_client = build_mock_router_client(
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
    assert "how much" in result["answer_text"].lower() or "cost" in result["answer_text"].lower()


def test_5_engine_error_handling():
    """
    Test 5: Graceful error handling when the financial engine raises an exception.
    """
    router_client = build_mock_router_client(tool_name="get_balance", tool_args={})

    def failing_engine(**kwargs):
        raise RuntimeError("Database connection pool exhausted")

    result = run_finSight_pipeline(
        user_id="demo_user",
        query="What is my balance?",
        engine_registry={"get_balance": failing_engine},
        router_client=router_client,
    )

    assert "answer_text" in result
    assert "structured_data" in result
    assert result["structured_data"]["status"] == "error"
    assert "Database connection pool exhausted" in result["structured_data"]["message"]
    assert "try again" in result["answer_text"].lower() or "issue" in result["answer_text"].lower() or "couldn't" in result["answer_text"].lower()


def test_6_missing_user_id():
    """
    Test 6: Validation when user_id is missing or empty.
    """
    result = run_finSight_pipeline(user_id="", query="What is my balance?")
    assert result["structured_data"]["status"] == "error"
    assert "user_id" in result["structured_data"]["message"]


def test_7_explainer_validation_failure_handling():
    """
    Test 7: When explainer generates a hallucinated number, the pipeline
    safely returns the fallback without crashing.
    """
    router_client = build_mock_router_client(
        tool_name="check_affordability",
        tool_args={"amount": 10000, "item_description": "phone"},
    )
    # Explainer attempts to return 99999 which is not in engine result
    explainer_client = build_mock_explainer_client(
        "You can afford this. Your balance will be ₹99999."
    )

    result = run_finSight_pipeline(
        user_id="demo_user",
        query="Can I afford a phone for ₹10000?",
        router_client=router_client,
        explainer_client=explainer_client,
    )

    assert "answer_text" in result
    assert "structured_data" in result
    # Must reject 99999 and provide safe fallback
    assert "99999" not in result["answer_text"]
    assert result["answer_text"] == "I don't have that information available."
    assert result["structured_data"]["can_afford"] is True
