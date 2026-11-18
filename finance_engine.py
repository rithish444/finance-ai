"""
finance_engine.py - Core Deterministic Financial Engine for ArthMitra.
Pure Python implementations of financial ratios, emergency funds, debt waterfall,
goal SIP math, and what-if simulation.
Zero external dependencies (pure Python math).
"""

from dataclasses import dataclass, field
from datetime import date, datetime
from typing import List, Dict, Optional, Tuple, Any
import math

from config import (
    DEFAULT_ASSUMPTIONS,
    HIGH_INTEREST_DEBT_THRESHOLD_PERCENT,
    EMERGENCY_MONTHS_BASE,
    EMERGENCY_MONTHS_WITH_DEPENDENTS,
    EMERGENCY_MONTHS_VARIABLE_INCOME,
)


@dataclass
class DebtItem:
    name: str
    outstanding_amount: float
    interest_rate_percent: float
    monthly_emi: float = 0.0

    @property
    def is_high_interest(self) -> bool:
        return self.interest_rate_percent >= HIGH_INTEREST_DEBT_THRESHOLD_PERCENT


@dataclass
class GoalItem:
    name: str
    target_amount: float
    target_date: str  # YYYY-MM or YYYY-MM-DD
    current_saved: float = 0.0


@dataclass
class GoalAnalysis:
    name: str
    target_amount: float
    target_date: str
    months_remaining: int
    horizon_category: str  # 'ultra_short' (<1y), 'short' (1-3y), 'medium' (3-5y), 'long' (5y+)
    recommended_asset_category: str
    assumed_annual_return_percent: float
    required_monthly_saving: float
    is_feasible: bool
    status_note: str


@dataclass
class FinancialProfile:
    monthly_income: float
    fixed_expenses: float
    variable_expenses: float
    existing_savings: float
    desired_monthly_savings: float = 0.0
    dependents: int = 0
    is_variable_income: bool = False
    salary_day: int = 1
    debts: List[DebtItem] = field(default_factory=list)
    goals: List[GoalItem] = field(default_factory=list)


@dataclass
class EngineOutput:
    monthly_income: float
    total_expenses: float
    savings_capacity: float
    savings_rate_percent: float
    target_realism: str  # 'realistic', 'ambitious', 'unrealistic', 'deficit'
    target_deficit_or_surplus: float
    emergency_target_months: int
    emergency_target_amount: float
    emergency_current_amount: float
    emergency_gap: float
    emergency_funded_percent: float
    months_to_fund_emergency: float
    total_debt_outstanding: float
    high_interest_debt_outstanding: float
    total_monthly_interest_drain: float
    debts_sorted_by_priority: List[Dict[str, Any]]
    goals_analysis: List[GoalAnalysis]
    total_required_goal_monthly: float
    overall_goals_feasible: bool
    unallocated_monthly_cash: float
    warnings: List[str]


def calculate_months_between(target_date_str: str, from_date: Optional[date] = None) -> int:
    """Calculates full months remaining from from_date to target_date_str (YYYY-MM or YYYY-MM-DD)."""
    if from_date is None:
        from_date = date.today()

    try:
        parts = target_date_str.strip().split("-")
        year = int(parts[0])
        month = int(parts[1])
        # Use first of target month for consistent month diff
        target = date(year, month, 1)
        months = (target.year - from_date.year) * 12 + (target.month - from_date.month)
        return max(0, months)
    except Exception:
        return 0


def calculate_sip_required(
    target_amount: float,
    months: int,
    annual_rate_percent: float,
    current_saved: float = 0.0,
) -> float:
    """
    Computes required monthly investment (beginning of month annuity formula)
    to achieve target_amount given months and annual return rate.
    Handles current lump-sum already saved compound growth.
    """
    if months <= 0:
        return max(0.0, target_amount - current_saved)

    target_needed = max(0.0, target_amount)

    # Grow existing savings at annual_rate_percent
    monthly_rate = (annual_rate_percent / 100.0) / 12.0
    if monthly_rate > 0 and current_saved > 0:
        fv_existing = current_saved * math.pow(1.0 + monthly_rate, months)
        target_needed = max(0.0, target_needed - fv_existing)

    if target_needed <= 0:
        return 0.0

    if monthly_rate <= 0:
        return round(target_needed / months, 2)

    # Annuity due SIP formula: FV = P * [((1+r)^n - 1) / r] * (1+r)
    # P = FV / ( [((1+r)^n - 1) / r] * (1+r) )
    compound_factor = math.pow(1.0 + monthly_rate, months)
    annuity_mult = ((compound_factor - 1.0) / monthly_rate) * (1.0 + monthly_rate)

    if annuity_mult <= 0:
        return round(target_needed / months, 2)

    required_p = target_needed / annuity_mult
    return round(max(0.0, required_p), 2)


def calculate_future_value_sip(monthly_saving: float, months: int, annual_rate_percent: float) -> float:
    """Computes future value of monthly recurring saving."""
    if months <= 0 or monthly_saving <= 0:
        return 0.0
    monthly_rate = (annual_rate_percent / 100.0) / 12.0
    if monthly_rate <= 0:
        return round(monthly_saving * months, 2)
    compound_factor = math.pow(1.0 + monthly_rate, months)
    fv = monthly_saving * ((compound_factor - 1.0) / monthly_rate) * (1.0 + monthly_rate)
    return round(fv, 2)


def calculate_future_value_lumpsum(principal: float, years: float, annual_rate_percent: float) -> float:
    """Computes compound future value for lumpsum deposit (e.g. FD)."""
    if principal <= 0 or years <= 0:
        return max(0.0, principal)
    return round(principal * math.pow(1.0 + (annual_rate_percent / 100.0), years), 2)


def classify_goal_horizon(months: int) -> Tuple[str, str, float]:
    """
    Classifies goal horizon into:
    - under 12 months: Ultra-short (Liquid fund / Short FD)
    - 12 to 36 months: Short (FD / RD / Debt funds)
    - 36 to 60 months: Medium (Hybrid funds + conservative hedge)
    - 60+ months: Long (Equity Index Fund SIP + PPF/NPS)
    Returns: (horizon_category, recommended_asset_category, assumed_return_percent)
    """
    if months < 12:
        return (
            "under_1_year",
            "Liquid Fund / Savings Account / Short FD",
            DEFAULT_ASSUMPTIONS["liquid_fund"],
        )
    elif months <= 36:
        return (
            "1_to_3_years",
            "Fixed Deposit (FD) / Recurring Deposit (RD) / Low Duration Debt Fund",
            DEFAULT_ASSUMPTIONS["fixed_deposit"],
        )
    elif months <= 60:
        return (
            "3_to_5_years",
            "Conservative or Aggressive Hybrid Mutual Fund",
            DEFAULT_ASSUMPTIONS["hybrid_fund"],
        )
    else:
        return (
            "5_plus_years",
            "Broad Market Index Fund SIP (Nifty 50) + PPF / NPS",
            DEFAULT_ASSUMPTIONS["index_fund_sip"],
        )


def analyze_finances(profile: FinancialProfile, reference_date: Optional[date] = None) -> EngineOutput:
    """
    Primary financial analysis pipeline.
    Pure deterministic logic with comprehensive bounds checks and edge-case protection.
    """
    if reference_date is None:
        reference_date = date.today()

    warnings: List[str] = []

    income = max(0.0, float(profile.monthly_income))
    fixed = max(0.0, float(profile.fixed_expenses))
    variable = max(0.0, float(profile.variable_expenses))
    savings = max(0.0, float(profile.existing_savings))
    desired = max(0.0, float(profile.desired_monthly_savings))

    # 1. Savings Capacity & Rate
    total_expenses = fixed + variable
    savings_capacity = income - total_expenses
    
    if income > 0:
        savings_rate_percent = round((max(0.0, savings_capacity) / income) * 100.0, 2)
    else:
        savings_rate_percent = 0.0
        warnings.append("Monthly income is zero. Financial stability requires cash inflows.")

    if savings_capacity < 0:
        warnings.append(
            f"Monthly expenses (₹{total_expenses:,.0f}) exceed monthly income (₹{income:,.0f}) by ₹{abs(savings_capacity):,.0f}. Immediate expense rationalization required."
        )

    # 2. Target Realism
    if savings_capacity <= 0:
        target_realism = "deficit"
        target_deficit_or_surplus = -abs(desired)
    elif desired <= 0:
        target_realism = "realistic"
        target_deficit_or_surplus = savings_capacity
    elif desired <= savings_capacity * 0.85:
        target_realism = "realistic"
        target_deficit_or_surplus = savings_capacity - desired
    elif desired <= savings_capacity:
        target_realism = "ambitious"
        target_deficit_or_surplus = savings_capacity - desired
    else:
        target_realism = "unrealistic"
        target_deficit_or_surplus = savings_capacity - desired
        warnings.append(
            f"Your desired monthly saving (₹{desired:,.0f}) exceeds your current surplus capacity (₹{savings_capacity:,.0f}) by ₹{abs(target_deficit_or_surplus):,.0f}."
        )

    # 3. Emergency Fund Targets
    # Essential monthly burn = Fixed expenses + 50% of variable expenses (survival budget)
    essential_burn = fixed + (0.5 * variable)
    if essential_burn <= 0:
        essential_burn = max(1000.0, income * 0.5)

    if profile.is_variable_income:
        emergency_months = EMERGENCY_MONTHS_VARIABLE_INCOME
    elif profile.dependents > 0:
        emergency_months = EMERGENCY_MONTHS_WITH_DEPENDENTS
    else:
        emergency_months = EMERGENCY_MONTHS_BASE

    emergency_target_amount = round(essential_burn * emergency_months, 2)
    emergency_gap = max(0.0, emergency_target_amount - savings)
    
    if emergency_target_amount > 0:
        emergency_funded_percent = min(100.0, round((savings / emergency_target_amount) * 100.0, 1))
    else:
        emergency_funded_percent = 100.0

    if savings_capacity > 0 and emergency_gap > 0:
        months_to_fund_emergency = round(emergency_gap / savings_capacity, 1)
    elif emergency_gap <= 0:
        months_to_fund_emergency = 0.0
    else:
        months_to_fund_emergency = 999.0  # Infinite if capacity <= 0

    if emergency_gap > 0:
        warnings.append(
            f"Emergency safety net is underfunded. Gap of ₹{emergency_gap:,.0f} ({emergency_months} months target: ₹{emergency_target_amount:,.0f})."
        )

    # 4. Debt Analysis & Avalanche Priority
    total_debt_outstanding = 0.0
    high_interest_debt_outstanding = 0.0
    total_monthly_interest_drain = 0.0
    sorted_debts: List[Dict[str, Any]] = []

    if profile.debts:
        # Sort by interest rate descending (Debt Avalanche - highest ROI)
        sorted_raw = sorted(profile.debts, key=lambda d: d.interest_rate_percent, reverse=True)
        for d in sorted_raw:
            bal = max(0.0, d.outstanding_amount)
            rate = max(0.0, d.interest_rate_percent)
            monthly_interest = bal * (rate / 100.0) / 12.0
            total_debt_outstanding += bal
            total_monthly_interest_drain += monthly_interest
            if rate >= HIGH_INTEREST_DEBT_THRESHOLD_PERCENT:
                high_interest_debt_outstanding += bal
            
            sorted_debts.append({
                "name": d.name,
                "outstanding": bal,
                "interest_rate": rate,
                "monthly_emi": d.monthly_emi,
                "monthly_interest_drain": round(monthly_interest, 2),
                "is_high_interest": rate >= HIGH_INTEREST_DEBT_THRESHOLD_PERCENT,
                "action": "Immediate prepay priority (Avalanche)" if rate >= HIGH_INTEREST_DEBT_THRESHOLD_PERCENT else "Continue scheduled EMIs"
            })

    if high_interest_debt_outstanding > 0:
        warnings.append(
            f"You carry ₹{high_interest_debt_outstanding:,.0f} in high-interest debt (>= {HIGH_INTEREST_DEBT_THRESHOLD_PERCENT}%). Paying this yields a guaranteed return."
        )

    # 5. Goals Analysis
    goals_analysis: List[GoalAnalysis] = []
    total_required_goal_monthly = 0.0

    effective_capacity = max(0.0, savings_capacity)
    
    for g in profile.goals:
        months_left = calculate_months_between(g.target_date, reference_date)
        horizon_cat, asset_cat, assumed_ret = classify_goal_horizon(months_left)
        
        req_sip = calculate_sip_required(
            target_amount=g.target_amount,
            months=months_left,
            annual_rate_percent=assumed_ret,
            current_saved=g.current_saved,
        )
        total_required_goal_monthly += req_sip

        is_feasible = (req_sip <= effective_capacity) if effective_capacity > 0 else False
        
        if months_left <= 0:
            status_note = "Target date has passed or is this month. Revisit target timeline."
            warnings.append(f"Goal '{g.name}' target date ({g.target_date}) has already passed or is this month.")
        elif req_sip <= effective_capacity:
            status_note = f"Feasible: Requires ₹{req_sip:,.0f}/mo at {assumed_ret}% assumed return."
        else:
            status_note = f"Deficit: Requires ₹{req_sip:,.0f}/mo, which exceeds available monthly capacity (₹{effective_capacity:,.0f})."

        goals_analysis.append(GoalAnalysis(
            name=g.name,
            target_amount=g.target_amount,
            target_date=g.target_date,
            months_remaining=months_left,
            horizon_category=horizon_cat,
            recommended_asset_category=asset_cat,
            assumed_annual_return_percent=assumed_ret,
            required_monthly_saving=req_sip,
            is_feasible=is_feasible,
            status_note=status_note,
        ))

    overall_goals_feasible = (total_required_goal_monthly <= effective_capacity) if profile.goals else True
    unallocated_monthly_cash = round(effective_capacity - total_required_goal_monthly, 2)

    return EngineOutput(
        monthly_income=round(income, 2),
        total_expenses=round(total_expenses, 2),
        savings_capacity=round(savings_capacity, 2),
        savings_rate_percent=savings_rate_percent,
        target_realism=target_realism,
        target_deficit_or_surplus=round(target_deficit_or_surplus, 2),
        emergency_target_months=emergency_months,
        emergency_target_amount=round(emergency_target_amount, 2),
        emergency_current_amount=round(savings, 2),
        emergency_gap=round(emergency_gap, 2),
        emergency_funded_percent=emergency_funded_percent,
        months_to_fund_emergency=months_to_fund_emergency,
        total_debt_outstanding=round(total_debt_outstanding, 2),
        high_interest_debt_outstanding=round(high_interest_debt_outstanding, 2),
        total_monthly_interest_drain=round(total_monthly_interest_drain, 2),
        debts_sorted_by_priority=sorted_debts,
        goals_analysis=goals_analysis,
        total_required_goal_monthly=round(total_required_goal_monthly, 2),
        overall_goals_feasible=overall_goals_feasible,
        unallocated_monthly_cash=unallocated_monthly_cash,
        warnings=warnings,
    )
