"""
Configuration and editable financial assumptions for ArthMitra.
These figures represent conservative Indian financial market estimates for educational planning,
not guaranteed returns or live feeds.
"""

from dataclasses import dataclass
from typing import Dict, Any

# Standard Conservative Asset Class Assumptions (Annualized Return %)
DEFAULT_ASSUMPTIONS: Dict[str, float] = {
    "savings_account": 3.5,
    "liquid_fund": 6.5,
    "short_fd": 6.5,
    "fixed_deposit": 7.0,
    "recurring_deposit": 7.0,
    "debt_fund": 7.5,
    "hybrid_fund": 10.0,
    "index_fund_sip": 12.0,
    "ppf": 7.1,
    "nps": 10.0,
    "gold": 9.0,
    "inflation": 6.0,
}

# High interest debt threshold (% APR). Debts above this must be paid before investing in equities.
HIGH_INTEREST_DEBT_THRESHOLD_PERCENT = 10.0

# Emergency Fund guidelines (number of months of essential expenses)
EMERGENCY_MONTHS_BASE = 6
EMERGENCY_MONTHS_WITH_DEPENDENTS = 9
EMERGENCY_MONTHS_VARIABLE_INCOME = 12

# Mandatory Legal & Educational Disclaimer
DISCLAIMER_TEXT = (
    "Disclaimer: This is educational guidance, not registered investment advice. "
    "Please consult a SEBI-registered investment advisor before investing."
)

# App Theme Colors
THEME = {
    "primary": "#1E3A8A",      # Deep Navy / Trust
    "secondary": "#059669",    # Emerald Green / Growth
    "accent": "#F59E0B",       # Warm Saffron / India Gold
    "warning": "#DC2626",      # Crimson Alert
    "background": "#F8FAFC",   # Clean Slate
    "card_bg": "#FFFFFF",
    "text": "#0F172A",
}
