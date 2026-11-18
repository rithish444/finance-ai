"""
Unit tests for data/personas.json and report.py.
Verifies all 3 personas load cleanly, parse validly through the engine, and generate reports.
"""

import os
import json
from finance_engine import FinancialProfile, DebtItem, GoalItem, analyze_finances
from health_score import calculate_health_score
from recommender import compute_risk_profile, generate_recommendations
from report import generate_markdown_report


def test_personas_validity():
    p_path = os.path.join(os.path.dirname(__file__), "..", "data", "personas.json")
    with open(p_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    personas = data.get("personas", [])
    assert len(personas) >= 3
    expected_ids = {"student", "salaried", "shop_owner"}
    found_ids = {p["id"] for p in personas}
    assert expected_ids.issubset(found_ids)

    # Test that each persona runs through the complete engine without errors
    for p in personas:
        debts = [
            DebtItem(
                name=d["name"],
                outstanding_amount=d["outstanding_amount"],
                interest_rate_percent=d["interest_rate_percent"],
                monthly_emi=d.get("monthly_emi", 0.0),
            )
            for d in p.get("debts", [])
        ]
        goals = [
            GoalItem(
                name=g["name"],
                target_amount=g["target_amount"],
                target_date=g["target_date"],
                current_saved=g.get("current_saved", 0.0),
            )
            for g in p.get("goals", [])
        ]
        profile = FinancialProfile(
            monthly_income=p["monthly_income"],
            fixed_expenses=p["fixed_expenses"],
            variable_expenses=p["variable_expenses"],
            existing_savings=p["existing_savings"],
            desired_monthly_savings=p.get("desired_monthly_savings", 0.0),
            dependents=p.get("dependents", 0),
            is_variable_income=p.get("is_variable_income", False),
            salary_day=p.get("salary_day", 1),
            debts=debts,
            goals=goals,
        )
        engine_out = analyze_finances(profile)
        health = calculate_health_score(profile, engine_out)
        risk, _ = compute_risk_profile(p.get("quiz_answers", [2, 2, 2, 2, 2]))
        plan = generate_recommendations(profile, engine_out, risk_level=risk)

        assert engine_out is not None
        assert 0 <= health.total_score <= 100
        assert len(plan.top_3_actions) >= 1

        # Test markdown report generation
        rep = generate_markdown_report(profile, engine_out, health, plan, user_name=p["name"])
        assert len(rep) > 200
        assert p["name"] in rep
        assert "Disclaimer" in rep
