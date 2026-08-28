"""
Unit tests for FinSight AI Intent Router.
Tests realistic conversational variations, slang, speech-like phrasing,
parameter extraction, ambiguous requests, and safety boundaries.
All LLM API calls are strictly mocked.
"""

from decimal import Decimal
import json
from unittest.mock import MagicMock
# pyrefly: ignore [missing-import]
import pytest
from ai.intent_router import route_query


def create_mock_openai_client(tool_name=None, tool_args=None, content=None, raises_exception=None):
    """Helper to construct a mock OpenAI client returning specified tool calls or content."""
    mock_client = MagicMock()

    if raises_exception:
        mock_client.chat.completions.create.side_effect = raises_exception
        return mock_client

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


# ==============================================================================
# 1. BALANCE CONVERSATIONAL VARIATIONS
# ==============================================================================

def test_balance_standard():
    """'What's my balance?' -> get_balance"""
    client = create_mock_openai_client(tool_name="get_balance", tool_args={})
    res = route_query("What's my balance?", user_id="demo_user", client=client)
    assert res["status"] == "success"
    assert res["function_name"] == "get_balance"
    assert res["arguments"]["user_id"] == "demo_user"


def test_balance_slang_bro():
    """'bro how much money do i have' -> get_balance"""
    client = create_mock_openai_client(tool_name="get_balance", tool_args={})
    res = route_query("bro how much money do i have", user_id="demo_user", client=client)
    assert res["status"] == "success"
    assert res["function_name"] == "get_balance"


def test_balance_how_much_have_i_got_left():
    """'how much have I got left?' -> get_balance"""
    client = create_mock_openai_client(tool_name="get_balance", tool_args={})
    res = route_query("how much have I got left?", user_id="demo_user", client=client)
    assert res["status"] == "success"
    assert res["function_name"] == "get_balance"


def test_balance_whats_sitting_in_my_account():
    """'what\'s sitting in my account?' -> get_balance"""
    client = create_mock_openai_client(tool_name="get_balance", tool_args={})
    res = route_query("what's sitting in my account?", user_id="demo_user", client=client)
    assert res["status"] == "success"
    assert res["function_name"] == "get_balance"


def test_balance_how_much_money_is_mine():
    """'how much money is mine right now?' -> get_balance"""
    client = create_mock_openai_client(tool_name="get_balance", tool_args={})
    res = route_query("how much money is mine right now?", user_id="demo_user", client=client)
    assert res["status"] == "success"
    assert res["function_name"] == "get_balance"


def test_balance_bro_am_i_low_on_money():
    """'Bro, am I low on money right now?' -> get_balance"""
    client = create_mock_openai_client(tool_name="get_balance", tool_args={})
    res = route_query("Bro, am I low on money right now?", user_id="demo_user", client=client)
    assert res["status"] == "success"
    assert res["function_name"] == "get_balance"


def test_balance_available_now():
    """'what do I have available right now?' -> get_balance"""
    client = create_mock_openai_client(tool_name="get_balance", tool_args={})
    res = route_query("what do I have available right now?", user_id="demo_user", client=client)
    assert res["status"] == "success"
    assert res["function_name"] == "get_balance"


def test_balance_how_much_cash():
    """'how much cash do I have?' -> get_balance"""
    client = create_mock_openai_client(tool_name="get_balance", tool_args={})
    res = route_query("how much cash do I have?", user_id="demo_user", client=client)
    assert res["status"] == "success"
    assert res["function_name"] == "get_balance"


def test_balance_what_left_bank():
    """'what\'s left in my bank?' -> get_balance"""
    client = create_mock_openai_client(tool_name="get_balance", tool_args={})
    res = route_query("what's left in my bank?", user_id="demo_user", client=client)
    assert res["status"] == "success"
    assert res["function_name"] == "get_balance"


def test_balance_tell_me_what_ive_got():
    """'tell me what I\'ve got' -> get_balance"""
    client = create_mock_openai_client(tool_name="get_balance", tool_args={})
    res = route_query("tell me what I've got", user_id="demo_user", client=client)
    assert res["status"] == "success"
    assert res["function_name"] == "get_balance"


# ==============================================================================
# 2. SPENDING SUMMARY CONVERSATIONAL VARIATIONS
# ==============================================================================

def test_spending_where_is_money_disappearing():
    """'where is all my money disappearing?' -> get_spending_summary"""
    client = create_mock_openai_client(
        tool_name="get_spending_summary",
        tool_args={"period": "this_month"},
    )
    res = route_query("where is all my money disappearing?", user_id="demo_user", client=client)
    assert res["status"] == "success"
    assert res["function_name"] == "get_spending_summary"
    assert res["arguments"]["period"] == "this_month"


def test_spending_what_have_i_been_spending_on():
    """'what have I been spending on?' -> get_spending_summary"""
    client = create_mock_openai_client(
        tool_name="get_spending_summary",
        tool_args={"period": "this_month"},
    )
    res = route_query("what have I been spending on?", user_id="demo_user", client=client)
    assert res["status"] == "success"
    assert res["function_name"] == "get_spending_summary"


def test_spending_where_did_my_money_go():
    """'where did my money go?' -> get_spending_summary"""
    client = create_mock_openai_client(
        tool_name="get_spending_summary",
        tool_args={"period": "this_month"},
    )
    res = route_query("where did my money go?", user_id="demo_user", client=client)
    assert res["status"] == "success"
    assert res["function_name"] == "get_spending_summary"


def test_spending_how_much_have_i_blown():
    """'how much have I blown recently?' -> get_spending_summary"""
    client = create_mock_openai_client(
        tool_name="get_spending_summary",
        tool_args={"period": "this_month"},
    )
    res = route_query("how much have I blown recently?", user_id="demo_user", client=client)
    assert res["status"] == "success"
    assert res["function_name"] == "get_spending_summary"


def test_spending_last_month():
    """'how much did I spend last month?' -> get_spending_summary (period=last_month)"""
    client = create_mock_openai_client(
        tool_name="get_spending_summary",
        tool_args={"period": "last_month"},
    )
    res = route_query("how much did I spend last month?", user_id="demo_user", client=client)
    assert res["status"] == "success"
    assert res["arguments"]["period"] == "last_month"


def test_spending_food_last_month():
    """'how much did I spend on food last month?' -> get_spending_summary (period=last_month, category=food)"""
    client = create_mock_openai_client(
        tool_name="get_spending_summary",
        tool_args={"period": "last_month", "category": "food"},
    )
    res = route_query("how much did I spend on food last month?", user_id="demo_user", client=client)
    assert res["status"] == "success"
    assert res["arguments"]["period"] == "last_month"
    assert res["arguments"]["category"] == "food"


# ==============================================================================
# 3. AFFORDABILITY CONVERSATIONAL VARIATIONS
# ==============================================================================

def test_affordability_do_you_think_headphones_8k():
    """'Do you think I can get these headphones for 8k?' -> check_affordability (amount=8000)"""
    client = create_mock_openai_client(
        tool_name="check_affordability",
        tool_args={"amount": "8k", "item_description": "headphones"},
    )
    res = route_query("Do you think I can get these headphones for 8k?", user_id="demo_user", client=client)
    assert res["status"] == "success"
    assert res["function_name"] == "check_affordability"
    assert res["arguments"]["amount"] == 8000.0


def test_affordability_20_grand():
    """'would a 20 grand laptop be okay?' -> check_affordability (amount=20000)"""
    client = create_mock_openai_client(
        tool_name="check_affordability",
        tool_args={"amount": "20 grand", "item_description": "laptop"},
    )
    res = route_query("would a 20 grand laptop be okay?", user_id="demo_user", client=client)
    assert res["status"] == "success"
    assert res["arguments"]["amount"] == 20000.0


def test_affordability_12_thousand_shoes():
    """'I want to spend 12 thousand on shoes, can I?' -> check_affordability (amount=12000)"""
    client = create_mock_openai_client(
        tool_name="check_affordability",
        tool_args={"amount": "12 thousand", "item_description": "shoes"},
    )
    res = route_query("I want to spend 12 thousand on shoes, can I?", user_id="demo_user", client=client)
    assert res["status"] == "success"
    assert res["arguments"]["amount"] == 12000.0


def test_affordability_15k_thing():
    """'do you think I can afford this thing for 15k?' -> check_affordability (amount=15000)"""
    client = create_mock_openai_client(
        tool_name="check_affordability",
        tool_args={"amount": "15k"},
    )
    res = route_query("do you think I can afford this thing for 15k?", user_id="demo_user", client=client)
    assert res["status"] == "success"
    assert res["arguments"]["amount"] == 15000.0


def test_affordability_formatted_currency():
    """'should I buy this thing for ₹12,000?' -> check_affordability (amount=12000)"""
    client = create_mock_openai_client(
        tool_name="check_affordability",
        tool_args={"amount": "₹12,000"},
    )
    res = route_query("should I buy this thing for ₹12,000?", user_id="demo_user", client=client)
    assert res["status"] == "success"
    assert res["arguments"]["amount"] == 12000.0


def test_affordability_missing_price_clarification():
    """'Should I buy this?' -> clarification_needed (no price)"""
    client = create_mock_openai_client(
        content="How much does the item cost?"
    )
    res = route_query("Should I buy this?", user_id="demo_user", client=client)
    assert res["status"] == "clarification_needed"
    assert "cost" in res["question"].lower() or "much" in res["question"].lower()


def test_affordability_can_i_afford_it():
    """'Can I afford it?' -> clarification_needed (no amount)"""
    client = create_mock_openai_client(
        content="How much does the item cost?"
    )
    res = route_query("Can I afford it?", user_id="demo_user", client=client)
    assert res["status"] == "clarification_needed"


# ==============================================================================
# 4. GOAL PROJECTION CONVERSATIONAL VARIATIONS
# ==============================================================================

def test_goal_when_will_i_hit_emergency_fund():
    """'when will I hit my emergency fund?' -> project_goal_completion"""
    client = create_mock_openai_client(
        tool_name="project_goal_completion",
        tool_args={"goal_name": "emergency fund"},
    )
    context = {"goals": {"emergency fund": "goal_efund_001"}}
    res = route_query("when will I hit my emergency fund?", user_id="demo_user", context=context, client=client)
    assert res["status"] == "success"
    assert res["function_name"] == "project_goal_completion"
    assert res["arguments"]["goal_id"] == "goal_efund_001"


def test_goal_how_long_until_savings_complete():
    """'how long until my savings goal is complete?' -> project_goal_completion"""
    client = create_mock_openai_client(
        tool_name="project_goal_completion",
        tool_args={"goal_name": "savings goal"},
    )
    context = {"goals": {"savings goal": "goal_efund_001"}}
    res = route_query("how long until my savings goal is complete?", user_id="demo_user", context=context, client=client)
    assert res["status"] == "success"
    assert res["arguments"]["goal_id"] == "goal_efund_001"


def test_goal_when_can_i_finish_that_emergency_fund():
    """'when can I finish that emergency fund?' -> project_goal_completion"""
    client = create_mock_openai_client(
        tool_name="project_goal_completion",
        tool_args={"goal_name": "emergency fund"},
    )
    context = {"goals": {"emergency fund": "goal_efund_001"}}
    res = route_query("when can I finish that emergency fund?", user_id="demo_user", context=context, client=client)
    assert res["status"] == "success"
    assert res["arguments"]["goal_id"] == "goal_efund_001"


def test_goal_unspecified_how_much_longer_to_save_clarification():
    """'How much longer do I need to save?' (no goal named) -> clarification_needed"""
    client = create_mock_openai_client(
        content="Which savings goal would you like to check?"
    )
    res = route_query("How much longer do I need to save?", user_id="demo_user", context={}, client=client)
    assert res["status"] == "clarification_needed"
    assert "goal" in res["question"].lower()


# ==============================================================================
# 5. INSIGHTS CONVERSATIONAL VARIATIONS
# ==============================================================================

def test_insights_why_am_i_spending_so_much():
    """'why am I spending so much?' -> get_insights"""
    client = create_mock_openai_client(tool_name="get_insights", tool_args={})
    res = route_query("why am I spending so much?", user_id="demo_user", client=client)
    assert res["status"] == "success"
    assert res["function_name"] == "get_insights"


def test_insights_whats_changed():
    """'what\'s changed with my spending?' -> get_insights"""
    client = create_mock_openai_client(tool_name="get_insights", tool_args={})
    res = route_query("what's changed with my spending?", user_id="demo_user", client=client)
    assert res["status"] == "success"
    assert res["function_name"] == "get_insights"


def test_insights_anything_weird():
    """'anything weird going on with my expenses?' -> get_insights"""
    client = create_mock_openai_client(tool_name="get_insights", tool_args={})
    res = route_query("anything weird going on with my expenses?", user_id="demo_user", client=client)
    assert res["status"] == "success"
    assert res["function_name"] == "get_insights"


def test_insights_have_you_noticed_patterns():
    """'have you noticed any patterns?' -> get_insights"""
    client = create_mock_openai_client(tool_name="get_insights", tool_args={})
    res = route_query("have you noticed any patterns?", user_id="demo_user", client=client)
    assert res["status"] == "success"
    assert res["function_name"] == "get_insights"


# ==============================================================================
# 6. AMBIGUOUS, OFF-TOPIC & EDGE SAFETY TESTS
# ==============================================================================

def test_ambiguous_what_about_that():
    """'What about that?' -> clarification_needed"""
    client = create_mock_openai_client(content="Could you please clarify your request?")
    res = route_query("What about that?", user_id="demo_user", client=client)
    assert res["status"] == "clarification_needed"


def test_ambiguous_is_it_okay():
    """'Is it okay?' -> clarification_needed"""
    client = create_mock_openai_client(content="Could you please provide more context?")
    res = route_query("Is it okay?", user_id="demo_user", client=client)
    assert res["status"] == "clarification_needed"


def test_ambiguous_should_i_do_it():
    """'should I do it?' -> clarification_needed"""
    client = create_mock_openai_client(content="What specific financial decision would you like help with?")
    res = route_query("should I do it?", user_id="demo_user", client=client)
    assert res["status"] == "clarification_needed"


def test_unrelated_weather():
    """'What\'s the weather today?' -> clarification / off-topic refusal"""
    client = create_mock_openai_client(
        content="I am FinSight. I can only assist with personal financial questions."
    )
    res = route_query("What's the weather today?", user_id="demo_user", client=client)
    assert res["status"] == "clarification_needed"
    assert "financial" in res["question"].lower() or "assist" in res["question"].lower()


def test_empty_query():
    """Empty query -> clarification needed"""
    res = route_query("", user_id="demo_user")
    assert res["status"] == "clarification_needed"


def test_missing_user_id():
    """Missing user_id -> error"""
    res = route_query("What is my balance?", user_id="")
    assert res["status"] == "error"
    assert "user_id" in res["message"]


def test_llm_exception_handling():
    """LLM API error -> caught and returned gracefully"""
    client = create_mock_openai_client(raises_exception=RuntimeError("Connection timeout"))
    res = route_query("What is my balance?", user_id="demo_user", client=client)
    assert res["status"] == "error"
    assert "Connection timeout" in res["message"]
