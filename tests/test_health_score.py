"""
Unit tests for health_score.py.
Verifies scoring boundaries, 4 pillars calculation, and gauge generation.
"""

from finance_engine import FinancialProfile, DebtItem, GoalItem, analyze_finances
from health_score import calculate_health_score, create_health_gauge_chart


def test_excellent_health_score():
    profile = FinancialProfile(
        monthly_income=100000,
        fixed_expenses=30000,
        variable_expenses=20000,
        existing_savings=500000,  # 10 months emergency
        desired_monthly_savings=30000,
        goals=[GoalItem("House Downpayment", 1000000, "2031-01-01")],
    )
    engine_out = analyze_finances(profile)
    res = calculate_health_score(profile, engine_out)

    assert res.total_score >= 80
    assert res.category_label == "Excellent"
    assert len(res.pillars) == 4
    assert res.pillars[0].score == 30.0  # 50% savings rate
    assert res.pillars[1].score == 25.0  # Fully funded emergency
    assert res.pillars[2].score == 25.0  # Zero debt


def test_critical_health_score():
    profile = FinancialProfile(
        monthly_income=40000,
        fixed_expenses=30000,
        variable_expenses=15000,  # deficit -5k
        existing_savings=0,
        debts=[DebtItem("Credit Card Loan", 150000, 40.0, 10000)],
    )
    engine_out = analyze_finances(profile)
    res = calculate_health_score(profile, engine_out)

    assert res.total_score < 45
    assert "Critical" in res.category_label or "Vulnerable" in res.category_label


def test_gauge_chart_generation():
    fig = create_health_gauge_chart(75, "Good", "#10B981")
    assert fig is not None
    assert fig.data[0].value == 75
