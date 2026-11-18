"""
report.py - Export and Report Generator for ArthMitra.
Generates comprehensive, professional Markdown and printable HTML reports
summarizing financial health, debt triage, goal roadmaps, and action items.
"""

from datetime import datetime
from typing import Dict, Any

from finance_engine import EngineOutput, FinancialProfile
from recommender import RecommendationPlan
from health_score import HealthScoreResult
from config import DISCLAIMER_TEXT


def generate_markdown_report(
    profile: FinancialProfile,
    engine_out: EngineOutput,
    health: HealthScoreResult,
    plan: RecommendationPlan,
    user_name: str = "Investor",
) -> str:
    """Generates a structured, clean Markdown financial report."""
    now_str = datetime.now().strftime("%d %B %Y, %I:%M %p")

    md = []
    md.append(f"# ArthMitra Personal Financial BluePrint")
    md.append(f"**Prepared for:** {user_name}  ")
    md.append(f"**Generated on:** {now_str}  ")
    md.append(f"**Financial Health Score:** {health.total_score}/100 ({health.category_label})  \n")
    md.append(f"---\n")

    md.append(f"## 1. Cashflow & Monthly Diagnosis")
    md.append(f"- **Monthly Income:** ₹{engine_out.monthly_income:,.0f}")
    md.append(f"- **Fixed Expenses:** ₹{profile.fixed_expenses:,.0f}")
    md.append(f"- **Variable Expenses:** ₹{profile.variable_expenses:,.0f}")
    md.append(f"- **Total Monthly Outflows:** ₹{engine_out.total_expenses:,.0f}")
    md.append(f"- **Net Monthly Savings Capacity:** ₹{engine_out.savings_capacity:,.0f}")
    md.append(f"- **Savings Rate:** {engine_out.savings_rate_percent:.1f}%")
    md.append(f"- **Target Realism Assessment:** {engine_out.target_realism.title()}\n")

    md.append(f"## 2. Emergency Safety Cushion")
    md.append(f"- **Target Duration:** {engine_out.emergency_target_months} Months")
    md.append(f"- **Target Fund Sizing:** ₹{engine_out.emergency_target_amount:,.0f}")
    md.append(f"- **Current Reserves:** ₹{engine_out.emergency_current_amount:,.0f}")
    md.append(f"- **Emergency Gap:** ₹{engine_out.emergency_gap:,.0f} ({engine_out.emergency_funded_percent:.0f}% Funded)")
    if engine_out.emergency_gap > 0:
        md.append(f"- **Estimated Time to Full Coverage:** {engine_out.months_to_fund_emergency:.1f} months\n")
    else:
        md.append(f"- **Status:** Fully Protected\n")

    md.append(f"## 3. Debt Audit & Payoff Strategy (Avalanche Order)")
    if engine_out.debts_sorted_by_priority:
        md.append("| Debt Name | Balance | APR % | Monthly EMI | Action |")
        md.append("| :--- | :--- | :--- | :--- | :--- |")
        for d in engine_out.debts_sorted_by_priority:
            md.append(f"| {d['name']} | ₹{d['outstanding']:,.0f} | {d['interest_rate']}% | ₹{d['monthly_emi']:,.0f} | {d['action']} |")
        md.append(f"\n- **High-Interest Debt Total:** ₹{engine_out.high_interest_debt_outstanding:,.0f}")
        md.append(f"- **Total Monthly Interest Drain:** ₹{engine_out.total_monthly_interest_drain:,.0f}/month\n")
    else:
        md.append("No active debts recorded. Zero monthly interest liability.\n")

    md.append(f"## 4. Goal Roadmap & Required SIP")
    if engine_out.goals_analysis:
        md.append("| Goal Name | Target Amount | Target Date | Months Left | Assumed Return | Required SIP | Feasible? |")
        md.append("| :--- | :--- | :--- | :--- | :--- | :--- | :--- |")
        for g in engine_out.goals_analysis:
            feasible_sym = "✅ Yes" if g.is_feasible else "⚠️ Deficit"
            md.append(f"| {g.name} | ₹{g.target_amount:,.0f} | {g.target_date} | {g.months_remaining} | {g.assumed_annual_return_percent}% | ₹{g.required_monthly_saving:,.0f}/mo | {feasible_sym} |")
        md.append(f"\n- **Total Goal Monthly Requirement:** ₹{engine_out.total_required_goal_monthly:,.0f}/month\n")
    else:
        md.append("No specific goals recorded.\n")

    md.append(f"## 5. Your First 3 Actions This Month")
    for act in plan.top_3_actions:
        md.append(f"{act.step}. **{act.title}** ({act.category})")
        md.append(f"   - {act.description}")
        md.append(f"   - **Timeline:** {act.deadline_or_timing}\n")

    md.append(f"## 6. Strategic Asset Guidance")
    md.append(f"### Real Estate & Land")
    md.append(f"{plan.real_estate_guidance}\n")
    md.append(f"### Gold Allocation")
    md.append(f"{plan.gold_guidance}\n")

    md.append(f"---\n")
    md.append(f"*{DISCLAIMER_TEXT}*")

    return "\n".join(md)
