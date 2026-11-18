"""
Unit tests for recommender.py.
Verifies risk quiz scoring, canonical recommendation hierarchy,
and timing guidance generation.
"""

from datetime import date
from finance_engine import FinancialProfile, DebtItem, GoalItem, analyze_finances
from recommender import compute_risk_profile, generate_recommendations


def test_compute_risk_profile():
    # 5 ones = 5 (Low)
    risk_low, score_low = compute_risk_profile([1, 1, 1, 1, 1])
    assert risk_low == "Low"
    assert score_low == 5

    # 5 twos = 10 (Medium)
    risk_med, score_med = compute_risk_profile([2, 2, 2, 2, 2])
    assert risk_med == "Medium"
    assert score_med == 10

    # 5 threes = 15 (High)
    risk_high, score_high = compute_risk_profile([3, 3, 3, 3, 3])
    assert risk_high == "High"
    assert score_high == 15


def test_recommender_hierarchy_emergency_first():
    # Profile with high emergency gap and credit card debt
    profile = FinancialProfile(
        monthly_income=50000,
        fixed_expenses=20000,
        variable_expenses=10000,
        existing_savings=10000,  # low savings, emergency gap
        salary_day=1,
        debts=[DebtItem("Credit Card", 30000, 42.0)],
        goals=[GoalItem("Europe Trip", 200000, "2028-01-01")],
    )
    engine_out = analyze_finances(profile, reference_date=date(2026, 1, 1))
    plan = generate_recommendations(profile, engine_out, risk_level="Medium")

    assert len(plan.priority_items) >= 3
    # Priority 1 must be Emergency
    assert plan.priority_items[0].priority_level == 1
    assert "Emergency" in plan.priority_items[0].category_title

    # Priority 2 must be High-Interest Debt
    assert plan.priority_items[1].priority_level == 2
    assert "Credit Card" in plan.priority_items[1].target_name

    # Priority 3 must be Goal
    assert plan.priority_items[2].priority_level == 3
    assert "Europe Trip" in plan.priority_items[2].target_name

    # Check top 3 actions generated
    assert len(plan.top_3_actions) == 3
    assert any(a.category == "Emergency" for a in plan.top_3_actions)
    assert any(a.category == "Debt" for a in plan.top_3_actions)

    # Check Real estate guidance warns about illiquidity
    assert "illiquid" in plan.real_estate_guidance.lower()
    assert "reit" in plan.real_estate_guidance.lower()

    # Check Gold guidance caps at 5-10%
    assert "5%" in plan.gold_guidance or "10%" in plan.gold_guidance


def test_recommender_near_term_goal_warning():
    # Goal in 6 months should trigger de-risking timing guidance
    profile = FinancialProfile(
        monthly_income=80000,
        fixed_expenses=30000,
        variable_expenses=15000,
        existing_savings=250000,  # fully funded emergency
        salary_day=5,
        goals=[GoalItem("Bike Purchase", 100000, "2026-07-01")],
    )
    engine_out = analyze_finances(profile, reference_date=date(2026, 1, 1))
    plan = generate_recommendations(profile, engine_out, risk_level="High")

    # Should have timing guidance regarding 6 months
    assert any("bike purchase" in t.lower() for t in plan.timing_guidance)
    assert any("shift" in t.lower() or "safe" in t.lower() or "de-risk" in t.lower() for t in plan.timing_guidance)
