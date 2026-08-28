"""
Unit tests for FinSight Grounded AI Explainer.
All LLM API calls are strictly mocked.
"""

from unittest.mock import MagicMock
# pyrefly: ignore [missing-import]
import pytest
from ai.explainer import (
    EXPLAINER_SYSTEM_PROMPT,
    SAFE_FALLBACK_TEXT,
    explain_result,
    validate_explanation_grounding,
)


def create_mock_openai_client(response_text=None, raises_exception=None):
    """Helper to construct a mock OpenAI client returning specified text content."""
    mock_client = MagicMock()

    if raises_exception:
        mock_client.chat.completions.create.side_effect = raises_exception
        return mock_client

    mock_choice = MagicMock()
    mock_choice.message.content = response_text or ""

    mock_response = MagicMock()
    mock_response.choices = [mock_choice]

    mock_client.chat.completions.create.return_value = mock_response
    return mock_client


def test_1_affordability_explanation():
    """
    Test 1: Affordability explanation with full data.
    Input: {"can_afford": True, "balance_after": 30000}
    Expected: Mentions affordability, does not invent additional numbers.
    """
    engine_result = {"can_afford": True, "balance_after": 30000}
    mock_text = "Yes, you can afford this purchase. Your remaining balance will be 30,000."
    mock_client = create_mock_openai_client(response_text=mock_text)

    result = explain_result(
        engine_result=engine_result,
        user_question="Can I afford to buy this?",
        client=mock_client,
    )

    assert "answer_text" in result
    answer = result["answer_text"]
    assert "afford" in answer.lower()
    assert "30,000" in answer or "30000" in answer

    # Verify LLM was called with grounding instructions and engine data
    call_args = mock_client.chat.completions.create.call_args[1]
    messages = call_args["messages"]
    system_msg = messages[0]["content"]
    user_msg = messages[1]["content"]

    assert "You are only a narrator. The JSON provided is authoritative. Do not add facts." in system_msg
    assert "30000" in user_msg


def test_2_spending_summary_explanation():
    """
    Test 2: Spending summary explanation.
    Input: {"total": 25000, "by_category": {"Food": 8000}}
    Expected: Mentions only provided numbers (25000 and 8000).
    """
    engine_result = {"total": 25000, "by_category": {"Food": 8000}}
    mock_text = "Your total spending is 25,000, with 8,000 spent on Food."
    mock_client = create_mock_openai_client(response_text=mock_text)

    result = explain_result(
        engine_result=engine_result,
        user_question="How much did I spend?",
        client=mock_client,
    )

    assert "answer_text" in result
    answer = result["answer_text"]
    assert "25,000" in answer or "25000" in answer
    assert "8,000" in answer or "8000" in answer
    assert "Food" in answer


def test_3_missing_information():
    """
    Test 3: Missing information in engine result.
    Input: {"can_afford": True} (no balance_after)
    Expected: Does not invent balance_after.
    """
    engine_result = {"can_afford": True}
    mock_text = "Yes, you can afford this purchase. I don't have your updated balance information available."
    mock_client = create_mock_openai_client(response_text=mock_text)

    result = explain_result(
        engine_result=engine_result,
        user_question="Can I afford this and what will be my balance?",
        client=mock_client,
    )

    assert "answer_text" in result
    answer = result["answer_text"]
    assert "afford" in answer.lower()
    assert "balance_after" not in answer
    assert "30000" not in answer
    assert "42000" not in answer


def test_4_empty_json_graceful_response():
    """
    Test 4: Empty JSON input.
    Expected: Returns graceful fallback message without crashing.
    """
    result_empty_dict = explain_result(engine_result={}, user_question="What is my balance?")
    assert "answer_text" in result_empty_dict
    assert result_empty_dict["answer_text"] == SAFE_FALLBACK_TEXT

    result_none = explain_result(engine_result=None, user_question="What is my balance?")
    assert "answer_text" in result_none
    assert result_none["answer_text"] == SAFE_FALLBACK_TEXT


def test_5_llm_exception_handling():
    """
    Test 5: LLM API error handling.
    Expected: Catches exception gracefully and returns structured error response.
    """
    mock_client = create_mock_openai_client(raises_exception=RuntimeError("LLM service unavailable"))
    result = explain_result(
        engine_result={"balance": 42000},
        user_question="What's my balance?",
        client=mock_client,
    )

    assert "answer_text" in result
    assert "Unable to generate explanation" in result["answer_text"]
    assert "LLM service unavailable" in result["answer_text"]


def test_6_system_prompt_rules():
    """
    Test 6: Verify system prompt contains required grounding constraints.
    """
    assert "You are only a narrator. The JSON provided is authoritative. Do not add facts." in EXPLAINER_SYSTEM_PROMPT
    assert "Copy numerical values exactly from JSON." in EXPLAINER_SYSTEM_PROMPT
    assert "NEVER calculate, estimate, extrapolate, or perform arithmetic" in EXPLAINER_SYSTEM_PROMPT
    assert "Do NOT round numbers." in EXPLAINER_SYSTEM_PROMPT
    assert "Do NOT convert units or currencies." in EXPLAINER_SYSTEM_PROMPT
    assert "Do NOT infer missing values." in EXPLAINER_SYSTEM_PROMPT
    assert "I don't have that information available." in EXPLAINER_SYSTEM_PROMPT
    assert "Temporal & Period Grounding" in EXPLAINER_SYSTEM_PROMPT


def test_7_grounding_rejection_hallucinated_number():
    """
    Test 7: Post-generation validation rejects hallucinated numbers.
    Input engine_result: {"balance_after": 32000}
    Mock LLM response: "The remaining balance is ₹30000."
    Expected: Validation fails because 30000 is not in engine_result -> Safe fallback returned.
    """
    engine_result = {"balance_after": 32000}
    mock_text = "The remaining balance is ₹30000."
    mock_client = create_mock_openai_client(response_text=mock_text)

    result = explain_result(
        engine_result=engine_result,
        user_question="What is my remaining balance?",
        client=mock_client,
    )

    assert "answer_text" in result
    # 30000 must be rejected
    assert "30000" not in result["answer_text"]
    assert "30,000" not in result["answer_text"]
    assert result["answer_text"] == SAFE_FALLBACK_TEXT


def test_8_validate_explanation_grounding_unit_tests():
    """
    Test 8: Direct unit test of validate_explanation_grounding logic.
    """
    engine_result = {
        "balance": 42000,
        "as_of": "2026-08-27",
        "category_breakdown": {"Food": 8000, "Transport": 3000},
        "pct": 15.5,
    }

    # Valid sentences with exact numbers
    assert validate_explanation_grounding("Your balance is 42000.", engine_result) is True
    assert validate_explanation_grounding("You spent ₹8,000 on Food and ₹3,000 on Transport.", engine_result) is True
    assert validate_explanation_grounding("Up by 15.5% as of 2026-08-27.", engine_result) is True

    # Invalid sentences with invented numbers
    assert validate_explanation_grounding("Your balance is 42001.", engine_result) is False
    assert validate_explanation_grounding("You spent 8500.", engine_result) is False
    assert validate_explanation_grounding("You have 500 dollars left.", engine_result) is False


def test_9_period_grounding_last_month():
    """
    Test 9: Spending summary for last_month correctly preserves period grounding.
    """
    engine_result = {
        "period": "last_month",
        "total": 35000,
        "by_category": {"Food": 10000},
    }
    mock_text = "You spent a total of ₹10,000 on Food last month."
    mock_client = create_mock_openai_client(response_text=mock_text)

    result = explain_result(
        engine_result=engine_result,
        user_question="How much did I spend on food last month?",
        client=mock_client,
    )

    assert result["answer_text"] == "You spent a total of ₹10,000 on Food last month."


def test_10_period_grounding_rejection_this_month_contradiction():
    """
    Test 10: If engine data is for last_month but LLM says 'this month', validation rejects it.
    """
    engine_result = {
        "period": "last_month",
        "total": 35000,
        "by_category": {"Food": 10000},
    }
    # LLM incorrectly said 'this month'
    mock_text = "You spent a total of ₹10,000 on Food this month."
    mock_client = create_mock_openai_client(response_text=mock_text)

    result = explain_result(
        engine_result=engine_result,
        user_question="How much did I spend on food last month?",
        client=mock_client,
    )

    assert result["answer_text"] == SAFE_FALLBACK_TEXT
