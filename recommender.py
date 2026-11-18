"""
recommender.py - Category-Based Recommendation and Timing Guidance Engine for ArthMitra.
Generates asset category allocations, priority waterfall, timing guidance,
and "Your first 3 actions this month" without specific stock/fund names.
"""

from dataclasses import dataclass
from typing import List, Dict, Any, Optional, Tuple
from datetime import date

from finance_engine import EngineOutput, FinancialProfile, GoalAnalysis


@dataclass
class RecommendationItem:
    priority_level: int
    category_title: str
    target_name: str
    allocation_amount_monthly: float
    recommended_vehicles: List[str]
    rationale: str
    why_this_rule: str
    risk_alignment: str
    timing_action: str


@dataclass
class ActionItem:
    step: int
    title: str
    description: str
    deadline_or_timing: str
    category: str  # 'Emergency', 'Debt', 'Investment', 'Budget'


@dataclass
class RecommendationPlan:
    risk_level: str  # 'Low', 'Medium', 'High'
    priority_items: List[RecommendationItem]
    top_3_actions: List[ActionItem]
    timing_guidance: List[str]
    real_estate_guidance: str
    gold_guidance: str


def compute_risk_profile(answers: List[int]) -> Tuple[str, int]:
    """
    Computes risk profile from a 5-question quiz.
    Each answer is an integer score (1 = Conservative, 2 = Moderate, 3 = Aggressive).
    Total score: 5 to 15.
    - 5 to 8: Low (Conservative)
    - 9 to 12: Medium (Balanced)
    - 13 to 15: High (Growth/Aggressive)
    """
    if not answers:
        return "Medium", 10

    total = sum(answers)
    if total <= 8:
        return "Low", total
    elif total <= 12:
        return "Medium", total
    else:
        return "High", total


def generate_recommendations(
    profile: FinancialProfile,
    engine_output: EngineOutput,
    risk_level: str = "Medium",
    reference_date: Optional[date] = None,
) -> RecommendationPlan:
    """
    Builds the structured recommendation plan strictly following the canonical hierarchy:
    1. Emergency Fund Safety Net
    2. High-Interest Debt Liquidation (Avalanche)
    3. Goals (Allocated strictly by horizon & risk tolerance)
    4. Surplus Wealth Accumulation
    """
    if reference_date is None:
        reference_date = date.today()

    priority_items: List[RecommendationItem] = []
    top_3_actions: List[ActionItem] = []
    timing_guidance: List[str] = []

    available_cash = max(0.0, engine_output.savings_capacity)
    salary_day = profile.salary_day if 1 <= profile.salary_day <= 28 else 5
    invest_day = min(28, salary_day + 3)  # 3 days after salary credited

    # 1. EMERGENCY FUND FIRST
    if engine_output.emergency_gap > 0:
        # Allocate up to 50% of available cash or entire gap towards emergency
        alloc = min(available_cash, round(engine_output.emergency_gap / max(1.0, min(6.0, engine_output.months_to_fund_emergency)), 2))
        if alloc <= 0 and available_cash > 0:
            alloc = round(available_cash * 0.5, 2)
        
        priority_items.append(RecommendationItem(
            priority_level=1,
            category_title="Emergency Safety Net (Mandatory)",
            target_name="Liquid Emergency Fund",
            allocation_amount_monthly=alloc,
            recommended_vehicles=[
                "High-yield Savings Bank Account (sweep-in enabled)",
                "Overnight / Liquid Mutual Fund (instant redemption)",
                "Short-term Fixed Deposit (auto-renewing)",
            ],
            rationale=(
                f"Your safety net has a gap of ₹{engine_output.emergency_gap:,.0f} to reach the "
                f"{engine_output.emergency_target_months}-month survival target of ₹{engine_output.emergency_target_amount:,.0f}."
            ),
            why_this_rule=(
                f"Rule: Never invest in equity or locked products without {engine_output.emergency_target_months} months "
                f"of essential living costs (Fixed: ₹{profile.fixed_expenses:,.0f} + 50% Var: ₹{profile.variable_expenses*0.5:,.0f} = ₹{engine_output.emergency_target_amount/engine_output.emergency_target_months:,.0f}/mo). "
                "Protects you against medical contingencies and sudden job loss without liquidating investments at a loss."
            ),
            risk_alignment="Low Risk (Zero volatility, 100% capital preservation)",
            timing_action=f"Automate transfer of ₹{alloc:,.0f} on the {invest_day}th of every month, right after salary.",
        ))

        top_3_actions.append(ActionItem(
            step=1,
            title="Automate Emergency Fund Transfer",
            description=f"Set up an auto-debit of ₹{alloc:,.0f} into a liquid fund or separate sweep-in savings account.",
            deadline_or_timing=f"{invest_day}th of this month (post-salary)",
            category="Emergency",
        ))
        available_cash = max(0.0, available_cash - alloc)
    else:
        priority_items.append(RecommendationItem(
            priority_level=1,
            category_title="Emergency Safety Net (Complete)",
            target_name="Emergency Reserve Maintained",
            allocation_amount_monthly=0.0,
            recommended_vehicles=["Maintain existing liquid savings"],
            rationale=f"Your emergency cushion is 100% funded (₹{engine_output.emergency_current_amount:,.0f} vs ₹{engine_output.emergency_target_amount:,.0f} target).",
            why_this_rule="Existing liquid savings adequately cover your family's essential living costs for the recommended horizon.",
            risk_alignment="Maintained",
            timing_action="Review emergency balance annually or when fixed expenses increase.",
        ))

    # 2. HIGH-INTEREST DEBT PAYOFF
    high_debts = [d for d in engine_output.debts_sorted_by_priority if d["is_high_interest"]]
    if high_debts:
        top_debt = high_debts[0]
        debt_alloc = min(available_cash, top_debt["outstanding"])
        
        priority_items.append(RecommendationItem(
            priority_level=2,
            category_title="High-Interest Debt Eradication",
            target_name=f"Pay off {top_debt['name']} ({top_debt['interest_rate']}% APR)",
            allocation_amount_monthly=debt_alloc,
            recommended_vehicles=["Direct bank prepayment / UPI lump sum"],
            rationale=(
                f"Paying off {top_debt['name']} at {top_debt['interest_rate']}% interest gives an immediate, "
                f"guaranteed risk-free return of {top_debt['interest_rate']}%, which outperforms any market investment."
            ),
            why_this_rule=(
                f"Rule: Debt Avalanche. Any debt charging >= 10% interest burns ₹{top_debt['monthly_interest_drain']:,.0f}/mo "
                f"in pure interest. Investing in mutual funds (assumed 12%) while paying 36-40% on credit cards results in guaranteed net wealth loss."
            ),
            risk_alignment="Highest ROI Action (Guaranteed return)",
            timing_action="Prepay immediately upon salary receipt before discretionary spending.",
        ))

        if len(top_3_actions) < 3:
            top_3_actions.append(ActionItem(
                step=len(top_3_actions) + 1,
                title=f"Attack High-Interest Debt ({top_debt['name']})",
                description=f"Allocate ₹{debt_alloc:,.0f} towards prepaying your {top_debt['name']} to stop the {top_debt['interest_rate']}% APR drain.",
                deadline_or_timing="Immediate (within 48 hours of salary)",
                category="Debt",
            ))
        available_cash = max(0.0, available_cash - debt_alloc)

    # 3. GOALS ALLOCATION
    for g in engine_output.goals_analysis:
        req = g.required_monthly_saving
        alloc = min(available_cash, req) if available_cash > 0 else 0.0

        # Adjust vehicle guidance by risk level
        vehicles = _get_vehicles_for_horizon_and_risk(g.horizon_category, risk_level)
        
        priority_items.append(RecommendationItem(
            priority_level=3,
            category_title=f"Goal: {g.name} ({g.horizon_category.replace('_', ' ').title()})",
            target_name=g.name,
            allocation_amount_monthly=alloc,
            recommended_vehicles=vehicles,
            rationale=(
                f"Target: ₹{g.target_amount:,.0f} in {g.months_remaining} months. "
                f"Requires ₹{req:,.0f}/mo at {g.assumed_annual_return_percent}% assumed return."
            ),
            why_this_rule=(
                f"Rule: Horizon Matching. Goals under 3 years must NOT be invested in pure equity due to sequence-of-returns risk. "
                f"For {g.months_remaining} months horizon, {g.recommended_asset_category} offers the required balance of liquidity and real returns."
            ),
            risk_alignment=f"Aligned with {risk_level} risk appetite and {g.months_remaining}-month horizon.",
            timing_action=f"Schedule automated monthly transfer/SIP for the {invest_day}th of every month.",
        ))

        # Timing alert if goal is approaching (<= 12 months)
        if 0 < g.months_remaining <= 12:
            timing_guidance.append(
                f"⚠️ Action for '{g.name}': Target is in {g.months_remaining} months. "
                "Keep strictly in liquid funds or short FDs; de-risk and shift away from market volatility to safeguard principal."
            )
        else:
            timing_guidance.append(
                f"🗓️ Cash flow timing for '{g.name}': Schedule monthly SIP on the {invest_day}th, exactly 3 days after salary credit on day {salary_day}."
            )

        if len(top_3_actions) < 3 and alloc > 0:
            top_3_actions.append(ActionItem(
                step=len(top_3_actions) + 1,
                title=f"Start Auto-Saving for '{g.name}'",
                description=f"Set up a recurring monthly investment of ₹{alloc:,.0f} in {vehicles[0]}.",
                deadline_or_timing=f"{invest_day}th of every month",
                category="Investment",
            ))
        available_cash = max(0.0, available_cash - alloc)

    # Fill remaining action if fewer than 3
    if len(top_3_actions) < 3:
        if profile.variable_expenses > (0.4 * profile.monthly_income) and profile.monthly_income > 0:
            top_3_actions.append(ActionItem(
                step=len(top_3_actions) + 1,
                title="Optimize Discretionary Expenses",
                description=f"Variable expenses are currently ₹{profile.variable_expenses:,.0f} ({round(profile.variable_expenses/profile.monthly_income*100)}% of income). Aim to trim dining out and impulse UPI spends by 15%.",
                deadline_or_timing="This weekend",
                category="Budget",
            ))
        else:
            top_3_actions.append(ActionItem(
                step=len(top_3_actions) + 1,
                title="Review Pure Term Life & Health Insurance",
                description="Ensure you have adequate pure term cover (10-15x annual income) and standalone family health insurance outside employer policy.",
                deadline_or_timing="By end of month",
                category="Protection",
            ))

    # Real Estate & Land Guidance (Strict Hackathon Requirement)
    real_estate_guidance = (
        "Real Estate & Land Guidance: Physical real estate and plot purchases require large upfront capital "
        "(high ticket size), incur significant stamp duty/registration costs, and are highly illiquid (cannot sell in days or months). "
        "For beginner or low-to-moderate monthly savers, direct physical land is UNFAVORABLE. "
        "Alternative: If you desire commercial real estate exposure, consider SEBI-regulated REITs (Real Estate Investment Trusts) "
        "which offer fractional liquidity starting at ₹300-₹400 per unit without debt burden."
    )

    # Gold Guidance (Strict Hackathon Requirement)
    gold_guidance = (
        "Gold Allocation Guidance: Gold acts as a portfolio hedge against currency depreciation and geopolitical shock, "
        "not a high-growth wealth compounding engine. Limit gold exposure to 5% to 10% of total portfolio. "
        "Prefer Sovereign Gold Bonds (SGB - 2.5% annual interest + tax-free redemption) or Gold ETFs / Digital Gold over physical jewelry "
        "to eliminate making charges (10-25%) and storage risks."
    )

    return RecommendationPlan(
        risk_level=risk_level,
        priority_items=priority_items,
        top_3_actions=top_3_actions[:3],
        timing_guidance=timing_guidance,
        real_estate_guidance=real_estate_guidance,
        gold_guidance=gold_guidance,
    )


def _get_vehicles_for_horizon_and_risk(horizon: str, risk: str) -> List[str]:
    """Returns asset categories tailored to horizon and risk without naming specific funds."""
    if horizon == "under_1_year":
        return [
            "Overnight or Liquid Mutual Funds",
            "High-Yield Bank Savings Account with Auto-Sweep",
            "Short-term Fixed Deposit (3 to 6 months)",
        ]
    elif horizon == "1_to_3_years":
        if risk == "High":
            return [
                "Low Duration & Short Duration Debt Funds",
                "Banking & PSU Debt Funds",
                "1-to-3 Year Bank Fixed Deposit / Post Office Time Deposit",
            ]
        else:
            return [
                "Bank Fixed Deposit (FD) / Recurring Deposit (RD)",
                "Corporate Bond Funds (AAA rated)",
                "Target Maturity Debt Index Funds",
            ]
    elif horizon == "3_to_5_years":
        if risk == "Low":
            return [
                "Conservative Hybrid Mutual Funds (75-90% Debt, 10-25% Equity)",
                "Multi-Asset Allocation Funds (predominantly fixed income)",
                "Fixed Maturity Plans (FMP)",
            ]
        elif risk == "Medium":
            return [
                "Balanced Advantage / Dynamic Asset Allocation Funds",
                "Aggressive Hybrid Mutual Funds (65-80% Equity, 20-35% Debt)",
                "Sovereign Gold Bonds / Gold ETF (5-10% hedge)",
            ]
        else:
            return [
                "Aggressive Hybrid Mutual Funds",
                "Large Cap Index Funds (Nifty 50) + Balanced Hybrid mix",
                "Gold ETF (5% allocation)",
            ]
    else:  # 5+ years
        if risk == "Low":
            return [
                "Public Provident Fund (PPF - 15 yr tax-exempt)",
                "Large Cap Index Funds (Nifty 50 Index Fund SIP)",
                "National Pension System (NPS - Corporate/Active Choice)",
                "Sovereign Gold Bonds (SGB)",
            ]
        elif risk == "Medium":
            return [
                "Broad Market Index Funds SIP (Nifty 50 & Nifty Next 50)",
                "Public Provident Fund (PPF) for fixed income cushion",
                "National Pension System (NPS - 50% Equity / 50% Debt)",
                "Gold ETF (5-10% portfolio hedge)",
            ]
        else:
            return [
                "Nifty 50 Index Fund + Midcap 150 Index Fund SIP",
                "National Pension System (NPS - 75% Equity Allocation)",
                "PPF (voluntary risk-free foundation)",
                "Gold ETF (5% tactical hedge)",
            ]
