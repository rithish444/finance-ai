"""
Unit tests for finance_engine.py.
Verifies pure deterministic financial calculations and edge cases.
"""

import pytest
from datetime import date
from finance_engine import (
    FinancialProfile,
    DebtItem,
    GoalItem,
    analyze_finances,
    calculate_sip_required,
    calculate_months_between,
    classify_goal_horizon,
    calculate_future_value_sip,
)


def test_calculate_sip_required_standard():
    # Target 1,00,000 in 12 months at 6% p.a.
    sip = calculate_sip_required(target_amount=100000, months=12, annual_rate_percent=6.0)
    assert sip > 0
    # At 0%, monthly is 100000/12 = 8333.33. With interest it should be slightly less
    assert sip < 8334
    assert sip > 7800


def test_calculate_sip_zero_interest():
    sip = calculate_sip_required(target_amount=12000, months=12, annual_rate_percent=0.0)
    assert round(sip, 2) == 1000.0


def test_calculate_sip_zero_months():
    sip = calculate_sip_required(target_amount=50000, months=0, annual_rate_percent=10.0)
    assert sip == 50000.0


def test_calculate_sip_with_existing_savings():
    # If already saved 50,000, required SIP should be significantly lower
    sip_full = calculate_sip_required(target_amount=100000, months=24, annual_rate_percent=10.0, current_saved=0)
    sip_partial = calculate_sip_required(target_amount=100000, months=24, annual_rate_percent=10.0, current_saved=50000)
    assert sip_partial < sip_full


def test_calculate_months_between():
    ref = date(2026, 1, 1)
    assert calculate_months_between("2026-07-01", ref) == 6
    assert calculate_months_between("2025-01-01", ref) == 0  # Past date clamps to 0
    assert calculate_months_between("invalid-date", ref) == 0


def test_classify_goal_horizon():
    cat1, asset1, _ = classify_goal_horizon(6)
    assert cat1 == "under_1_year"
    assert "Liquid" in asset1 or "Savings" in asset1

    cat2, asset2, _ = classify_goal_horizon(24)
    assert cat2 == "1_to_3_years"
    assert "Fixed Deposit" in asset2

    cat3, asset3, _ = classify_goal_horizon(48)
    assert cat3 == "3_to_5_years"
    assert "Hybrid" in asset3

    cat4, asset4, _ = classify_goal_horizon(72)
    assert cat4 == "5_plus_years"
    assert "Index Fund" in asset4


def test_standard_salaried_profile():
    profile = FinancialProfile(
        monthly_income=60000,
        fixed_expenses=25000,
        variable_expenses=15000,
        existing_savings=50000,
        desired_monthly_savings=15000,
        dependents=1,
        salary_day=5,
        debts=[
            DebtItem("Credit Card", 40000, 38.0, 4000),
            DebtItem("Education Loan", 150000, 8.5, 3000),
        ],
        goals=[
            GoalItem("Laptop", 75000, "2027-01-01"),
        ],
    )
    result = analyze_finances(profile, reference_date=date(2026, 1, 1))

    assert result.monthly_income == 60000
    assert result.total_expenses == 40000
    assert result.savings_capacity == 20000
    assert result.savings_rate_percent == pytest.approx(33.33, rel=1e-2)
    assert result.target_realism == "realistic"
    assert result.high_interest_debt_outstanding == 40000
    assert len(result.debts_sorted_by_priority) == 2
    # First debt should be credit card (38% > 8.5%)
    assert result.debts_sorted_by_priority[0]["name"] == "Credit Card"
    assert result.debts_sorted_by_priority[0]["is_high_interest"] is True
    # Emergency target for 1 dependent should be 9 months
    assert result.emergency_target_months == 9
    assert result.emergency_gap > 0


def test_negative_savings_capacity_edge_case():
    profile = FinancialProfile(
        monthly_income=30000,
        fixed_expenses=25000,
        variable_expenses=10000,
        existing_savings=5000,
        desired_monthly_savings=5000,
    )
    result = analyze_finances(profile)
    assert result.savings_capacity == -5000
    assert result.target_realism == "deficit"
    assert any("exceed" in w.lower() for w in result.warnings)


def test_zero_income_edge_case():
    profile = FinancialProfile(
        monthly_income=0,
        fixed_expenses=10000,
        variable_expenses=5000,
        existing_savings=20000,
    )
    result = analyze_finances(profile)
    assert result.monthly_income == 0
    assert result.savings_rate_percent == 0.0
    assert result.savings_capacity == -15000
    assert any("zero" in w.lower() for w in result.warnings)


def test_past_goal_date_handling():
    profile = FinancialProfile(
        monthly_income=50000,
        fixed_expenses=20000,
        variable_expenses=10000,
        existing_savings=30000,
        goals=[GoalItem("Old Goal", 50000, "2020-01-01")],
    )
    result = analyze_finances(profile, reference_date=date(2026, 1, 1))
    assert len(result.goals_analysis) == 1
    assert result.goals_analysis[0].months_remaining == 0
    assert "passed" in result.goals_analysis[0].status_note.lower()
