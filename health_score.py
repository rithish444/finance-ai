"""
health_score.py - 100-Point Financial Health Scoring System for ArthMitra.
Evaluates four core financial pillars:
1. Savings Rate (30 pts)
2. Emergency Cushion (25 pts)
3. Debt Burden (25 pts)
4. Goal Feasibility & Progress (20 pts)
Includes Plotly Gauge chart generator for clean Streamlit rendering.
"""

from dataclasses import dataclass
from typing import Dict, Any, List
import plotly.graph_objects as go

from finance_engine import EngineOutput, FinancialProfile


@dataclass
class HealthPillar:
    name: str
    score: float
    max_score: float
    status: str
    feedback: str


@dataclass
class HealthScoreResult:
    total_score: int  # 0 to 100
    category_label: str  # 'Critical', 'Needs Attention', 'Good', 'Excellent'
    color_hex: str
    summary_sentence: str
    pillars: List[HealthPillar]


def calculate_health_score(profile: FinancialProfile, engine_out: EngineOutput) -> HealthScoreResult:
    """Calculates an objective 100-point Indian personal finance health score."""
    pillars: List[HealthPillar] = []

    # 1. Savings Rate Pillar (Max 30)
    sr = engine_out.savings_rate_percent
    if engine_out.savings_capacity <= 0 or engine_out.monthly_income <= 0:
        sr_score = 0.0
        sr_status = "Deficit"
        sr_feedback = "Living beyond monthly income. Immediate expense reduction required."
    elif sr >= 35.0:
        sr_score = 30.0
        sr_status = "Exceptional"
        sr_feedback = f"Outstanding {sr:.1f}% savings rate! Well above the recommended 20-30%."
    elif sr >= 25.0:
        sr_score = 25.0
        sr_status = "Healthy"
        sr_feedback = f"Solid {sr:.1f}% savings rate. Comfortably exceeds minimum benchmarks."
    elif sr >= 15.0:
        sr_score = 18.0
        sr_status = "Moderate"
        sr_feedback = f"Fair {sr:.1f}% savings rate. Strive to push towards 20%+ via expense audits."
    elif sr > 0:
        sr_score = 10.0
        sr_status = "Low"
        sr_feedback = f"Tight {sr:.1f}% savings rate. Low buffer against price inflation."
    else:
        sr_score = 0.0
        sr_status = "Zero"
        sr_feedback = "No savings recorded this month."

    pillars.append(HealthPillar("Savings Rate", sr_score, 30.0, sr_status, sr_feedback))

    # 2. Emergency Fund Cushion Pillar (Max 25)
    pct_funded = engine_out.emergency_funded_percent
    if pct_funded >= 100.0:
        ef_score = 25.0
        ef_status = "Fully Shielded"
        ef_feedback = f"Full {engine_out.emergency_target_months}-month essential living expenses safeguarded."
    elif pct_funded >= 75.0:
        ef_score = 20.0
        ef_status = "Near Target"
        ef_feedback = f"{pct_funded:.0f}% of safety target accumulated. Keep closing the remaining gap."
    elif pct_funded >= 40.0:
        ef_score = 13.0
        ef_status = "Half Protected"
        ef_feedback = f"{pct_funded:.0f}% funded. High vulnerability if job disruption occurs."
    elif pct_funded > 0:
        ef_score = 6.0
        ef_status = "Underfunded"
        ef_feedback = f"Only {pct_funded:.0f}% of emergency safety net in place."
    else:
        ef_score = 0.0
        ef_status = "Unprotected"
        ef_feedback = "Zero emergency reserves. Any contingency may force predatory debt."

    pillars.append(HealthPillar("Emergency Safety Net", ef_score, 25.0, ef_status, ef_feedback))

    # 3. Debt Burden Pillar (Max 25)
    if not profile.debts or engine_out.total_debt_outstanding == 0:
        debt_score = 25.0
        debt_status = "Debt-Free"
        debt_feedback = "No outstanding debt obligations! 100% of income is at your disposal."
    elif engine_out.high_interest_debt_outstanding > 0:
        # High interest debt (>10%) heavily penalized
        ratio = engine_out.high_interest_debt_outstanding / max(1.0, engine_out.monthly_income)
        if ratio > 2.0:
            debt_score = 2.0
            debt_status = "Severe Risk"
            debt_feedback = f"Heavy high-interest debt (₹{engine_out.high_interest_debt_outstanding:,.0f}). Compound interest trap danger."
        elif ratio > 0.5:
            debt_score = 7.0
            debt_status = "High Stress"
            debt_feedback = f"Carrying ₹{engine_out.high_interest_debt_outstanding:,.0f} in high-interest loans/cards. Prepay priority #1."
        else:
            debt_score = 12.0
            debt_status = "Elevated"
            debt_feedback = f"Carrying ₹{engine_out.high_interest_debt_outstanding:,.0f} in credit card/personal debt. Pay off immediately."
    else:
        # Only low interest debt (home/education loan)
        emi_total = sum(d.monthly_emi for d in profile.debts)
        emi_ratio = (emi_total / max(1.0, engine_out.monthly_income)) * 100
        if emi_ratio <= 30:
            debt_score = 22.0
            debt_status = "Managed"
            debt_feedback = f"Low-interest productive debt only. Healthy EMI-to-income ratio ({emi_ratio:.0f}%)."
        elif emi_ratio <= 50:
            debt_score = 16.0
            debt_status = "Moderate Load"
            debt_feedback = f"Low-interest debt EMIs take {emi_ratio:.0f}% of income. Refrain from fresh debt."
        else:
            debt_score = 10.0
            debt_status = "Overleveraged"
            debt_feedback = f"EMIs consume {emi_ratio:.0f}% of income. Heavy pressure on monthly cashflow."

    pillars.append(HealthPillar("Debt Health", debt_score, 25.0, debt_status, debt_feedback))

    # 4. Goal Feasibility & Progress Pillar (Max 20)
    if not profile.goals:
        goal_score = 12.0
        goal_status = "No Goals Set"
        goal_feedback = "No specific financial goals defined yet. Adding concrete goals focuses your wealth strategy."
    elif engine_out.overall_goals_feasible:
        goal_score = 20.0
        goal_status = "On Track"
        goal_feedback = "All target dates and savings amounts are mathematically achievable with your cashflow."
    else:
        # Partial feasibility
        feasible_count = sum(1 for g in engine_out.goals_analysis if g.is_feasible)
        total_count = len(engine_out.goals_analysis)
        ratio = feasible_count / max(1, total_count)
        if ratio >= 0.5:
            goal_score = 12.0
            goal_status = "Partially Feasible"
            goal_feedback = f"{feasible_count} of {total_count} goals fit current budget. Extend timelines for others."
        else:
            goal_score = 5.0
            goal_status = "Overloaded"
            goal_feedback = "Required goal SIPs significantly outstrip current surplus capacity."

    pillars.append(HealthPillar("Goal Realism", goal_score, 20.0, goal_status, goal_feedback))

    total = int(round(sum(p.score for p in pillars)))
    total = max(0, min(100, total))

    if total >= 80:
        label = "Excellent"
        color = "#059669"  # Emerald
        summary = "Your financial foundation is robust! Maintain discipline and stick to your asset allocation."
    elif total >= 65:
        label = "Good"
        color = "#10B981"  # Mint Green
        summary = "Strong trajectory. Addressing 1 or 2 highlighted gaps will unlock peak financial freedom."
    elif total >= 45:
        label = "Needs Attention"
        color = "#F59E0B"  # Amber
        summary = "Cushion is thin. Prioritize emergency reserves and tackle high-interest debt before aggressive goals."
    else:
        label = "Critical / Vulnerable"
        color = "#DC2626"  # Crimson
        summary = "High financial vulnerability. Stop all equity investing and implement the emergency triage plan."

    return HealthScoreResult(
        total_score=total,
        category_label=label,
        color_hex=color,
        summary_sentence=summary,
        pillars=pillars,
    )


def create_health_gauge_chart(score: int, label: str, color_hex: str) -> go.Figure:
    """Generates an attractive Plotly indicator gauge chart for the financial health score."""
    fig = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=score,
            number={"suffix": "/100", "font": {"size": 36, "color": "#0F172A", "family": "Arial, sans-serif"}},
            title={"text": f"<b>Financial Health: {label}</b>", "font": {"size": 18, "color": color_hex}},
            gauge={
                "axis": {"range": [0, 100], "tickwidth": 1, "tickcolor": "#94A3B8"},
                "bar": {"color": color_hex, "thickness": 0.28},
                "bgcolor": "#F1F5F9",
                "borderwidth": 1,
                "bordercolor": "#CBD5E1",
                "steps": [
                    {"range": [0, 44], "color": "rgba(220, 38, 38, 0.15)"},
                    {"range": [45, 64], "color": "rgba(245, 158, 11, 0.15)"},
                    {"range": [65, 79], "color": "rgba(16, 185, 129, 0.15)"},
                    {"range": [80, 100], "color": "rgba(5, 150, 105, 0.2)"},
                ],
                "threshold": {
                    "line": {"color": "#1E293B", "width": 3},
                    "thickness": 0.8,
                    "value": score,
                },
            },
        )
    )

    fig.update_layout(
        height=240,
        margin=dict(l=20, r=20, t=40, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        font={"family": "Arial, sans-serif"},
    )
    return fig
