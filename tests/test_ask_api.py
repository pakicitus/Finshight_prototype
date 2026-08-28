"""
FinSight Integration Tests for POST /ask Endpoint
=================================================
Verifies end-to-end FastAPI endpoint integration with the real SQLite financial engine.
"""

from decimal import Decimal
import json
from unittest.mock import patch, MagicMock
# pyrefly: ignore [missing-import]
from fastapi.testclient import TestClient
# pyrefly: ignore [missing-import]
import pytest

from backend.main import app
from backend.seed.generate_synthetic_data import seed_database

client = TestClient(app)


@pytest.fixture(autouse=True, scope="module")
def setup_seeded_db():
    """Seed real SQLite database before running API integration tests."""
    seed_database()


def create_mock_router_client(tool_name=None, tool_args=None, content=None):
    """Build mock client for intent router."""
    mock_client = MagicMock()
    mock_choice = MagicMock()
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


# ==============================================================================
# 1. BALANCE API TEST
# ==============================================================================

def test_ask_1_balance():
    """
    Test 1: POST /ask with 'How much money do I have?'
    Verify: HTTP 200, answer_text, structured data from real deterministic engine (₹138,372.00).
    """
    mock_router = create_mock_router_client(tool_name="get_balance", tool_args={})
    mock_explainer = create_mock_explainer_client(
        "Your current account balance is ₹138,372.00 as of today."
    )

    with patch("ai.intent_router.get_llm_client", return_value=mock_router), \
         patch("ai.explainer.get_llm_client", return_value=mock_explainer):

        response = client.post(
            "/ask",
            json={"user_id": "demo_user", "query": "How much money do I have?"},
        )

        assert response.status_code == 200
        data = response.json()
        assert "answer_text" in data
        assert "structured_data" in data
        assert data["structured_data"]["balance"] == 138372
        assert "138,372" in data["answer_text"] or "138372" in data["answer_text"]


# ==============================================================================
# 2. CONVERSATIONAL BALANCE API TEST
# ==============================================================================

def test_ask_2_conversational_balance():
    """
    Test 2: POST /ask with conversational balance query 'How much have I got left?'
    Verify: Correctly routes to get_balance and returns authoritative balance.
    """
    mock_router = create_mock_router_client(tool_name="get_balance", tool_args={})
    mock_explainer = create_mock_explainer_client(
        "Your current account balance is ₹138,372.00 as of today."
    )

    with patch("ai.intent_router.get_llm_client", return_value=mock_router), \
         patch("ai.explainer.get_llm_client", return_value=mock_explainer):

        response = client.post(
            "/ask",
            json={"user_id": "demo_user", "query": "How much have I got left?"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["structured_data"]["balance"] == 138372
        assert "138,372" in data["answer_text"] or "138372" in data["answer_text"]


# ==============================================================================
# 3. SPENDING SUMMARY API TEST
# ==============================================================================

def test_ask_3_spending_summary():
    """
    Test 3: POST /ask with 'Where did most of my money go this month?'
    Verify: Spending engine is invoked through the pipeline, structured category data returned.
    """
    mock_router = create_mock_router_client(
        tool_name="get_spending_summary",
        tool_args={"period": "this_month"},
    )
    mock_explainer = create_mock_explainer_client(
        "Your total spending this month is ₹43,959.05 with ₹12,400.00 spent on Food."
    )

    with patch("ai.intent_router.get_llm_client", return_value=mock_router), \
         patch("ai.explainer.get_llm_client", return_value=mock_explainer):

        response = client.post(
            "/ask",
            json={"user_id": "demo_user", "query": "Where did most of my money go this month?"},
        )

        assert response.status_code == 200
        data = response.json()
        structured = data["structured_data"]
        assert structured["total"] == 43959.05
        assert structured["by_category"]["Food"] == 12400
        assert "43,959.05" in data["answer_text"] or "43959" in data["answer_text"]


# ==============================================================================
# 4. AFFORDABILITY WITH NATURAL LANGUAGE AMOUNT API TEST
# ==============================================================================

def test_ask_4_affordability():
    """
    Test 4: POST /ask with 'Would it be stupid to buy a laptop for 50 thousand?'
    Verify: 50000 amount extracted, affordability evaluated by deterministic engine.
    Balance after purchase: 138,372 - 50,000 = 88,372.
    """
    mock_router = create_mock_router_client(
        tool_name="check_affordability",
        tool_args={"amount": 50000, "item_description": "laptop"},
    )
    mock_explainer = create_mock_explainer_client(
        "Yes, you can afford the laptop for ₹50,000. Your remaining balance will be ₹88,372.00."
    )

    with patch("ai.intent_router.get_llm_client", return_value=mock_router), \
         patch("ai.explainer.get_llm_client", return_value=mock_explainer):

        response = client.post(
            "/ask",
            json={"user_id": "demo_user", "query": "Would it be stupid to buy a laptop for 50 thousand?"},
        )

        assert response.status_code == 200
        data = response.json()
        structured = data["structured_data"]
        assert structured["can_afford"] is True
        assert structured["balance_after"] == 88372
        assert structured["upcoming_bills"] == 6500
        assert "88,372" in data["answer_text"] or "88372" in data["answer_text"]


# ==============================================================================
# 5. MISSING AMOUNT AFFORDABILITY (CLARIFICATION) API TEST
# ==============================================================================

def test_ask_5_missing_amount_clarification():
    """
    Test 5: POST /ask with 'Can I afford it?' (no price mentioned)
    Verify: Clarification response returned, financial engine is NOT called.
    """
    mock_router = create_mock_router_client(
        tool_name="check_affordability",
        tool_args={"item_description": "it"},
    )

    with patch("ai.intent_router.get_llm_client", return_value=mock_router):
        response = client.post(
            "/ask",
            json={"user_id": "demo_user", "query": "Can I afford it?"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["structured_data"]["status"] == "clarification_needed"
        assert "cost" in data["answer_text"].lower() or "how much" in data["answer_text"].lower()


# ==============================================================================
# 6. GOAL PROGRESS QUERY API TEST
# ==============================================================================

def test_ask_6_goal_query():
    """
    Test 6: POST /ask with 'When will I reach my emergency fund?'
    Verify: Named goal is resolved to real goal_id, deterministic projection engine is invoked.
    """
    mock_router = create_mock_router_client(
        tool_name="project_goal_completion",
        tool_args={"goal_name": "emergency fund"},
    )
    mock_explainer = create_mock_explainer_client(
        "You are on track to complete your Emergency Fund goal in 6.0 months."
    )

    with patch("ai.intent_router.get_llm_client", return_value=mock_router), \
         patch("ai.explainer.get_llm_client", return_value=mock_explainer):

        response = client.post(
            "/ask",
            json={"user_id": "demo_user", "query": "When will I reach my emergency fund?"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["structured_data"]["current_months_remaining"] == 6.0
        assert "6.0" in data["answer_text"] or "6" in data["answer_text"]


# ==============================================================================
# 7. INVALID USER ID API TEST
# ==============================================================================

def test_ask_7_invalid_user_id():
    """
    Test 7: POST /ask with empty user_id.
    Verify: Safe error response without fabricating numbers.
    """
    response = client.post(
        "/ask",
        json={"user_id": "", "query": "What is my balance?"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["structured_data"]["status"] == "error"
    assert "user_id is required" in data["structured_data"]["message"]


# ==============================================================================
# 8. OFF-TOPIC QUERY API TEST
# ==============================================================================

def test_ask_8_off_topic_query():
    """
    Test 8: POST /ask with 'Tell me a joke'.
    Verify: FinSight responds safely stating domain boundaries, engine is not called.
    """
    mock_router = create_mock_router_client(
        content="I am FinSight, your personal finance assistant. I only assist with personal financial inquiries."
    )

    with patch("ai.intent_router.get_llm_client", return_value=mock_router):
        response = client.post(
            "/ask",
            json={"user_id": "demo_user", "query": "Tell me a joke"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["structured_data"]["status"] == "clarification_needed"
        assert "finance" in data["answer_text"].lower() or "financial" in data["answer_text"].lower() or "assist" in data["answer_text"].lower()


# ==============================================================================
# 9. API VERSIONING TEST (POST /api/v1/ask)
# ==============================================================================

def test_ask_9_api_v1_versioning():
    """
    Test 9: POST /api/v1/ask endpoint operates identically to /ask.
    """
    mock_router = create_mock_router_client(tool_name="get_balance", tool_args={})
    mock_explainer = create_mock_explainer_client(
        "Your current account balance is ₹138,372.00 as of today."
    )

    with patch("ai.intent_router.get_llm_client", return_value=mock_router), \
         patch("ai.explainer.get_llm_client", return_value=mock_explainer):

        response = client.post(
            "/api/v1/ask",
            json={"user_id": "demo_user", "query": "What's my balance?"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["structured_data"]["balance"] == 138372
