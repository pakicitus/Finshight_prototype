"""
Unit tests for FinSight Fake Financial Engine (Mock).
Verifies that all mock functions return valid, JSON-serializable structures
matching expected schemas.
"""

import json
import pytest
from ai.fake_engine import (
    get_balance,
    get_spending_summary,
    check_affordability,
    project_goal_completion,
    get_insights,
)


def test_get_balance():
    """Verify get_balance returns valid JSON with balance and as_of date."""
    result = get_balance(user_id="demo_user")
    json_str = json.dumps(result)
    data = json.loads(json_str)

    assert isinstance(data, dict)
    assert "balance" in data
    assert isinstance(data["balance"], (int, float))
    assert "as_of" in data
    assert data["balance"] == 42000


def test_get_spending_summary_default():
    """Verify get_spending_summary default period and category breakdown."""
    result = get_spending_summary(user_id="demo_user")
    json_str = json.dumps(result)
    data = json.loads(json_str)

    assert isinstance(data, dict)
    assert data["total"] == 25000
    assert "by_category" in data
    assert data["by_category"]["Food"] == 8000
    assert data["by_category"]["Transport"] == 3000
    assert data["vs_last_period_pct"] == 15


def test_get_spending_summary_with_category():
    """Verify get_spending_summary when category is specified."""
    result = get_spending_summary(user_id="demo_user", period="this_month", category="food")
    json_str = json.dumps(result)
    data = json.loads(json_str)

    assert isinstance(data, dict)
    assert data["total"] == 8000
    assert "Food" in data["by_category"]
    assert data["vs_last_period_pct"] == 15


def test_check_affordability_affordable():
    """Verify check_affordability when purchase is within budget."""
    result = check_affordability(user_id="demo_user", amount=12000, item_description="phone")
    json_str = json.dumps(result)
    data = json.loads(json_str)

    assert isinstance(data, dict)
    assert data["can_afford"] is True
    assert data["balance_after"] == 30000
    assert data["upcoming_bills"] == 5000
    assert isinstance(data["reasoning_facts"], list)
    assert len(data["reasoning_facts"]) > 0


def test_check_affordability_not_affordable():
    """Verify check_affordability when purchase exceeds safe balance."""
    result = check_affordability(user_id="demo_user", amount=50000, item_description="luxury trip")
    json_str = json.dumps(result)
    data = json.loads(json_str)

    assert isinstance(data, dict)
    assert data["can_afford"] is False
    assert data["balance_after"] == 42000
    assert data["upcoming_bills"] == 5000


def test_project_goal_completion_without_hypothetical():
    """Verify project_goal_completion without extra contributions."""
    result = project_goal_completion(user_id="demo_user", goal_id="goal_efund_001")
    json_str = json.dumps(result)
    data = json.loads(json_str)

    assert isinstance(data, dict)
    assert data["goal_name"] == "Emergency Fund"
    assert data["current_months_remaining"] == 6
    assert data["hypothetical_months_remaining"] == 6


def test_project_goal_completion_with_hypothetical():
    """Verify project_goal_completion with hypothetical contribution."""
    result = project_goal_completion(
        user_id="demo_user",
        goal_id="goal_efund_001",
        hypothetical_contribution=2000,
    )
    json_str = json.dumps(result)
    data = json.loads(json_str)

    assert isinstance(data, dict)
    assert data["goal_name"] == "Emergency Fund"
    assert data["current_months_remaining"] == 6
    assert data["hypothetical_months_remaining"] == 4


def test_get_insights():
    """Verify get_insights returns valid list of insight JSON objects."""
    result = get_insights(user_id="demo_user")
    json_str = json.dumps(result)
    data = json.loads(json_str)

    assert isinstance(data, list)
    assert len(data) >= 1
    first_insight = data[0]
    assert first_insight["type"] == "spending_increase"
    assert first_insight["category"] == "Food"
    assert first_insight["percentage"] == 22
    assert first_insight["period"] == "3 months"
