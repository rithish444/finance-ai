"""
app.py - ArthMitra (अर्थमित्र / அர்த்தமித்ரா)
AI Personal Finance Coach for India.
Full-stack Streamlit Application.
"""

import os
import json
from datetime import date
from typing import List, Dict, Any
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from dotenv import load_dotenv

# Load local environment variables if available
load_dotenv()

from config import (
    DEFAULT_ASSUMPTIONS,
    DISCLAIMER_TEXT,
    HIGH_INTEREST_DEBT_THRESHOLD_PERCENT,
    THEME,
)
from finance_engine import (
    FinancialProfile,
    DebtItem,
    GoalItem,
    analyze_finances,
    calculate_months_between,
    calculate_sip_required,
    calculate_future_value_sip,
    calculate_future_value_lumpsum,
)
from recommender import (
    compute_risk_profile,
    generate_recommendations,
)
from health_score import (
    calculate_health_score,
    create_health_gauge_chart,
)
from sms_parser import parse_sms_text_block
from llm_client import generate_plan_explanation, answer_faq
from report import generate_markdown_report

# Streamlit Page Config
st.set_page_config(
    page_title="ArthMitra - AI Personal Finance Coach",
    page_icon="🪙",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS for polished, accessible hackathon UI
st.markdown(
    """
    <style>
    .main-header {
        font-size: 2.2rem;
        font-weight: 800;
        color: #1E3A8A;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        font-size: 1.05rem;
        color: #475569;
        margin-bottom: 1.2rem;
    }
    .action-card {
        background: linear-gradient(135deg, #EFF6FF 0%, #FFFFFF 100%);
        border: 1px solid #BFDBFE;
        border-radius: 12px;
        padding: 16px 20px;
        margin-bottom: 12px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.02);
    }
    .action-badge {
        display: inline-block;
        padding: 4px 10px;
        font-size: 0.75rem;
        font-weight: 700;
        border-radius: 6px;
        text-transform: uppercase;
        margin-bottom: 6px;
    }
    .badge-emergency { background-color: #FEE2E2; color: #991B1B; }
    .badge-debt { background-color: #FEF3C7; color: #92400E; }
    .badge-investment { background-color: #D1FAE5; color: #065F46; }
    .badge-budget { background-color: #E0E7FF; color: #3730A3; }
    .disclaimer-banner {
        background-color: #F1F5F9;
        border-left: 4px solid #64748B;
        padding: 10px 14px;
        font-size: 0.82rem;
        color: #475569;
        border-radius: 4px;
        margin-top: 15px;
        margin-bottom: 15px;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 48px;
        white-space: pre-wrap;
        background-color: #F8FAFC;
        border-radius: 8px 8px 0px 0px;
        font-weight: 600;
    }
    .metric-pill {
        background: #F8FAFC;
        border: 1px solid #E2E8F0;
        border-radius: 8px;
        padding: 12px;
        text-align: center;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def load_personas() -> List[Dict[str, Any]]:
    """Loads bundled sample personas from data/personas.json."""
    try:
        p_path = os.path.join(os.path.dirname(__file__), "data", "personas.json")
        with open(p_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data.get("personas", [])
    except Exception:
        return []


# Initialize Session State
if "profile_loaded" not in st.session_state:
    st.session_state.profile_loaded = False
    st.session_state.monthly_income = 50000.0
    st.session_state.fixed_expenses = 20000.0
    st.session_state.variable_expenses = 12000.0
    st.session_state.existing_savings = 40000.0
    st.session_state.desired_monthly_savings = 15000.0
    st.session_state.dependents = 0
    st.session_state.salary_day = 5
    st.session_state.is_variable_income = False
    st.session_state.debts = [
        {"name": "Credit Card", "outstanding_amount": 35000.0, "interest_rate_percent": 38.0, "monthly_emi": 3500.0}
    ]
    st.session_state.goals = [
        {"name": "Emergency Fund Buffer", "target_amount": 100000.0, "target_date": "2027-06-01", "current_saved": 40000.0},
        {"name": "Laptop Upgrade", "target_amount": 80000.0, "target_date": "2028-01-01", "current_saved": 0.0},
    ]
    st.session_state.quiz_answers = [2, 2, 2, 2, 2]
    st.session_state.language = "English"


def set_persona(p: Dict[str, Any]):
    """Loads a persona into the current session state."""
    st.session_state.monthly_income = float(p.get("monthly_income", 50000))
    st.session_state.fixed_expenses = float(p.get("fixed_expenses", 20000))
    st.session_state.variable_expenses = float(p.get("variable_expenses", 12000))
    st.session_state.existing_savings = float(p.get("existing_savings", 30000))
    st.session_state.desired_monthly_savings = float(p.get("desired_monthly_savings", 10000))
    st.session_state.dependents = int(p.get("dependents", 0))
    st.session_state.salary_day = int(p.get("salary_day", 5))
    st.session_state.is_variable_income = bool(p.get("is_variable_income", False))
    st.session_state.debts = list(p.get("debts", []))
    st.session_state.goals = list(p.get("goals", []))
    st.session_state.quiz_answers = list(p.get("quiz_answers", [2, 2, 2, 2, 2]))
    st.session_state.persona_name = p.get("name", "Custom")


# ==================== SIDEBAR ====================
with st.sidebar:
    st.image(
        "https://raw.githubusercontent.com/google/material-design-icons/master/png/action/account_balance/materialicons/48dp/1x/baseline_account_balance_black_48dp.png",
        width=50,
    )
    st.title("🪙 ArthMitra")
    st.caption("AI Personal Finance Coach for India")

    # Language Toggle (English, Hindi, Tamil)
    selected_lang = st.selectbox(
        "🌐 Language / भाषा / மொழி",
        ["English", "Hindi", "Tamil"],
        index=["English", "Hindi", "Tamil"].index(st.session_state.get("language", "English")),
    )
    st.session_state.language = selected_lang

    st.markdown("---")
    st.subheader("⚡ 1-Click Demo Personas")
    st.caption("Select a real Indian persona to instantly populate financial profile and test all features:")
    personas = load_personas()
    for p in personas:
        btn_label = f"👤 {p['name']} ({p['role']})"
        if st.button(btn_label, use_container_width=True, key=f"btn_p_{p['id']}"):
            set_persona(p)
            st.rerun()

    st.markdown("---")
    with st.expander("⚙️ Editable Market Assumptions", expanded=False):
        st.caption("Conservative baseline annualized returns for projections:")
        fd_rate = st.slider("Fixed Deposit / RD (%)", 4.0, 9.0, DEFAULT_ASSUMPTIONS["fixed_deposit"], 0.5)
        sip_rate = st.slider("Index Fund SIP (%)", 8.0, 16.0, DEFAULT_ASSUMPTIONS["index_fund_sip"], 0.5)
        gold_rate = st.slider("Gold SGB / ETF (%)", 5.0, 12.0, DEFAULT_ASSUMPTIONS["gold"], 0.5)
        inflation_rate = st.slider("Assumed Inflation (%)", 4.0, 9.0, DEFAULT_ASSUMPTIONS["inflation"], 0.5)

    st.markdown("---")
    st.info(
        "🔒 **Privacy Guarantee**: No data is uploaded or stored. All computations run in-session inside your local browser memory."
    )
    st.caption(DISCLAIMER_TEXT)


# ==================== MAIN APP HEADER ====================
col_title, col_stat = st.columns([3, 1])
with col_title:
    st.markdown("<div class='main-header'>ArthMitra • अर्थमित्र</div>", unsafe_allow_html=True)
    st.markdown(
        "<div class='sub-header'>Clear, unbiased, category-based personal finance advice for Indian first-time investors.</div>",
        unsafe_allow_html=True,
    )
with col_stat:
    if "persona_name" in st.session_state and st.session_state.persona_name:
        st.success(f"Active Persona: **{st.session_state.persona_name}**")

# Mandatory SEBI disclaimer banner visible on page
st.markdown(f"<div class='disclaimer-banner'>⚠️ {DISCLAIMER_TEXT}</div>", unsafe_allow_html=True)


# ==================== TABS ====================
tab_onboarding, tab_quiz, tab_health, tab_plan, tab_simulator = st.tabs([
    "1️⃣ Onboarding & Cashflow",
    "2️⃣ Risk Profile Quiz",
    "3️⃣ Health Score & Diagnosis",
    "4️⃣ Recommendations & Actions",
    "5️⃣ What-If & Growth Charts",
])


# ==================== TAB 1: ONBOARDING ====================
with tab_onboarding:
    st.subheader("📋 Step 1: Your Monthly Financial Situation")
    st.caption("Tell ArthMitra about your monthly income, living expenses, existing safety reserves, and debts.")

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("##### 💵 Inflows & Living Costs")
        monthly_income = st.number_input(
            "Monthly Take-Home Income (₹)",
            min_value=0.0,
            value=float(st.session_state.monthly_income),
            step=2000.0,
            help="Your net in-hand monthly salary, profit, or stipend after taxes.",
        )
        st.session_state.monthly_income = monthly_income

        fixed_expenses = st.number_input(
            "Fixed Essential Expenses (₹)",
            min_value=0.0,
            value=float(st.session_state.fixed_expenses),
            step=1000.0,
            help="Rent, existing loan EMIs, electricity, school fees, insurance premiums that cannot be skipped.",
        )
        st.session_state.fixed_expenses = fixed_expenses

        variable_expenses = st.number_input(
            "Variable / Discretionary Expenses (₹)",
            min_value=0.0,
            value=float(st.session_state.variable_expenses),
            step=1000.0,
            help="Groceries, dining out, Swiggy/Zomato, weekend shopping, cab fares, entertainment.",
        )
        st.session_state.variable_expenses = variable_expenses

        # STANDOUT FEATURE: SMS PARSER EXPANDER
        with st.expander("📱 Auto-fill Variable Expenses by Pasting Bank / UPI SMS", expanded=False):
            st.caption("Paste multi-line transaction SMS messages from SBI, HDFC, ICICI, Axis, GPay, PhonePe, etc.")
            sample_sms_demo = (
                "Dear SBI User, your A/c X1234 debited by Rs 450.00 on 12-Nov by UPI to Swiggy.\n"
                "HDFC Bank: Rs 1,450.00 debited from a/c **4321 on 15-Nov to BLINKIT.\n"
                "Paid Rs 380.00 to Uber India via Google Pay UPI.\n"
                "Debited INR 899.00 on 02-Nov for NETFLIX subscription."
            )
            sms_input = st.text_area("Paste SMS text here:", value="", placeholder=sample_sms_demo, height=110)
            if st.button("🔍 Parse & Pre-Fill Variable Expenses"):
                if sms_input.strip():
                    txns, cat_totals, total_debit = parse_sms_text_block(sms_input)
                    if txns:
                        st.session_state.variable_expenses = total_debit
                        st.success(f"Extracted {len(txns)} transactions totaling ₹{total_debit:,.2f} across categories!")
                        st.json(cat_totals)
                        st.rerun()
                    else:
                        st.warning("Could not identify debit transactions in the pasted text. Please check format.")

    with col2:
        st.markdown("##### 🛡️ Cushion, Dependents & Salary Timing")
        existing_savings = st.number_input(
            "Existing Liquid Savings (₹)",
            min_value=0.0,
            value=float(st.session_state.existing_savings),
            step=5000.0,
            help="Money readily accessible in savings accounts, liquid funds, or accessible FDs.",
        )
        st.session_state.existing_savings = existing_savings

        desired_monthly_savings = st.number_input(
            "Desired Monthly Savings Target (₹)",
            min_value=0.0,
            value=float(st.session_state.desired_monthly_savings),
            step=1000.0,
            help="How much you aspire to invest or save every month.",
        )
        st.session_state.desired_monthly_savings = desired_monthly_savings

        col_dep, col_sal = st.columns(2)
        with col_dep:
            dependents = st.number_input(
                "Family Dependents",
                min_value=0,
                max_value=10,
                value=int(st.session_state.dependents),
                help="Spouse, children, or elderly parents who depend on your income.",
            )
            st.session_state.dependents = dependents
        with col_sal:
            salary_day = st.number_input(
                "Monthly Salary Day (1-28)",
                min_value=1,
                max_value=28,
                value=int(st.session_state.salary_day),
                help="Day of month your earnings arrive, for disciplined SIP timing.",
            )
            st.session_state.salary_day = salary_day

        is_var = st.checkbox(
            "Income is Variable / Business / Freelance (Requires 12-month emergency cushion)",
            value=bool(st.session_state.is_variable_income),
        )
        st.session_state.is_variable_income = is_var

    st.markdown("---")
    st.markdown("##### 💳 Outstanding Debts & Loans")
    st.caption("Credit cards or personal loans charging high interest will be prioritized for payoff before equity investing.")

    # Debts editor in session state
    current_debts = st.session_state.debts
    num_debts = len(current_debts)
    new_debts = []
    
    for i in range(num_debts):
        d = current_debts[i]
        dcol1, dcol2, dcol3, dcol4 = st.columns([3, 2, 2, 2])
        with dcol1:
            d_name = st.text_input(f"Debt #{i+1} Name", value=d.get("name", "Loan"), key=f"d_name_{i}")
        with dcol2:
            d_amt = st.number_input(f"Outstanding (₹)", min_value=0.0, value=float(d.get("outstanding_amount", 0)), step=5000.0, key=f"d_amt_{i}")
        with dcol3:
            d_rate = st.number_input(f"Interest Rate (% APR)", min_value=0.0, max_value=60.0, value=float(d.get("interest_rate_percent", 12.0)), step=0.5, key=f"d_rate_{i}")
        with dcol4:
            d_emi = st.number_input(f"Monthly EMI (₹)", min_value=0.0, value=float(d.get("monthly_emi", 0)), step=500.0, key=f"d_emi_{i}")
        
        if d_amt > 0:
            new_debts.append({"name": d_name, "outstanding_amount": d_amt, "interest_rate_percent": d_rate, "monthly_emi": d_emi})

    c_btn1, c_btn2 = st.columns([1, 4])
    with c_btn1:
        if st.button("➕ Add Debt"):
            new_debts.append({"name": "Credit Card / Loan", "outstanding_amount": 25000.0, "interest_rate_percent": 36.0, "monthly_emi": 2500.0})
            st.session_state.debts = new_debts
            st.rerun()
    with c_btn2:
        if num_debts > 0 and st.button("🗑️ Clear All Debts"):
            st.session_state.debts = []
            st.rerun()

    st.session_state.debts = new_debts

    st.markdown("---")
    st.markdown("##### 🎯 Financial Goals")
    st.caption("Add targets with target amount and date. ArthMitra automatically calculates required monthly SIPs.")

    current_goals = st.session_state.goals
    num_goals = len(current_goals)
    new_goals = []

    for j in range(num_goals):
        g = current_goals[j]
        gcol1, gcol2, gcol3, gcol4 = st.columns([3, 2, 2, 2])
        with gcol1:
            g_name = st.text_input(f"Goal #{j+1} Name", value=g.get("name", f"Goal {j+1}"), key=f"g_name_{j}")
        with gcol2:
            g_amt = st.number_input(f"Target (₹)", min_value=1000.0, value=float(g.get("target_amount", 50000)), step=5000.0, key=f"g_amt_{j}")
        with gcol3:
            g_date = st.text_input(f"Target Date (YYYY-MM)", value=g.get("target_date", "2028-12-01"), key=f"g_date_{j}")
        with gcol4:
            g_saved = st.number_input(f"Already Saved (₹)", min_value=0.0, value=float(g.get("current_saved", 0)), step=2000.0, key=f"g_saved_{j}")
        
        new_goals.append({"name": g_name, "target_amount": g_amt, "target_date": g_date, "current_saved": g_saved})

    g_btn1, g_btn2 = st.columns([1, 4])
    with g_btn1:
        if st.button("➕ Add Goal"):
            new_goals.append({"name": "Higher Education / Trip", "target_amount": 100000.0, "target_date": "2028-06-01", "current_saved": 0.0})
            st.session_state.goals = new_goals
            st.rerun()
    with g_btn2:
        if num_goals > 0 and st.button("🗑️ Reset Goals"):
            st.session_state.goals = []
            st.rerun()

    st.session_state.goals = new_goals


# ==================== TAB 2: RISK QUIZ ====================
with tab_quiz:
    st.subheader("🧠 Step 2: 5-Question Risk Tolerance Quiz")
    st.caption("Evaluates your capacity and psychological comfort with financial volatility to recommend the right asset mix.")

    q_answers = list(st.session_state.get("quiz_answers", [2, 2, 2, 2, 2]))

    q1 = st.radio(
        "1. **Investment Horizon:** How long can you leave your invested money untouched without needing to withdraw?",
        [
            "Less than 1 to 2 years (Need liquidity soon) [1 pt]",
            "3 to 5 years (Medium term goals) [2 pts]",
            "5+ years or more (Long term wealth compounding) [3 pts]",
        ],
        index=q_answers[0] - 1,
    )
    ans1 = 1 if "1 pt" in q1 else (2 if "2 pts" in q1 else 3)

    q2 = st.radio(
        "2. **Reaction to Market Corrections:** If your investment drops by 15% during a temporary economic dip, what would you do?",
        [
            "Panic and immediately withdraw everything into bank savings [1 pt]",
            "Feel uneasy, but wait for the market to recover [2 pts]",
            "Celebrate discounted prices and invest more through disciplined SIP [3 pts]",
        ],
        index=q_answers[1] - 1,
    )
    ans2 = 1 if "1 pt" in q2 else (2 if "2 pts" in q2 else 3)

    q3 = st.radio(
        "3. **Income Stability:** How predictable is your monthly household earning?",
        [
            "Variable, seasonal, or uncertain earnings [1 pt]",
            "Reasonably steady salary with standard job security [2 pts]",
            "Highly secure income / government job / multi-income household [3 pts]",
        ],
        index=q_answers[2] - 1,
    )
    ans3 = 1 if "1 pt" in q3 else (2 if "2 pts" in q3 else 3)

    q4 = st.radio(
        "4. **Financial Experience:** How familiar are you with mutual funds, inflation, and market volatility?",
        [
            "First-time beginner; only used bank savings and post office FDs [1 pt]",
            "Basic understanding; have heard about SIPs or index funds [2 pts]",
            "Experienced; comfortable with equity drawdowns and compounding [3 pts]",
        ],
        index=q_answers[3] - 1,
    )
    ans4 = 1 if "1 pt" in q4 else (2 if "2 pts" in q4 else 3)

    q5 = st.radio(
        "5. **Primary Investment Objective:** What matters most to you?",
        [
            "100% Capital safety: I cannot tolerate losing even 1 rupee of principal [1 pt]",
            "Balanced growth: Moderate capital appreciation beating inflation [2 pts]",
            "Aggressive wealth creation: Maximizing long-term compounding [3 pts]",
        ],
        index=q_answers[4] - 1,
    )
    ans5 = 1 if "1 pt" in q5 else (2 if "2 pts" in q5 else 3)

    new_quiz_answers = [ans1, ans2, ans3, ans4, ans5]
    st.session_state.quiz_answers = new_quiz_answers

    risk_label, risk_score = compute_risk_profile(new_quiz_answers)
    st.markdown("---")
    r_col1, r_col2 = st.columns([1, 3])
    with r_col1:
        st.metric("Computed Risk Score", f"{risk_score} / 15")
    with r_col2:
        if risk_label == "Low":
            st.warning("🛡️ **Risk Profile: Conservative (Low)** — Emphasis on capital preservation, bank FDs, and debt funds.")
        elif risk_label == "Medium":
            st.info("⚖️ **Risk Profile: Balanced (Medium)** — Balanced hybrid funds, index funds, and safe debt anchors.")
        else:
            st.success("🚀 **Risk Profile: Growth / Aggressive (High)** — High equity index fund SIP allocation for maximum 5+ year compounding.")


# ==================== RUN ENGINE ANALYSIS ====================
# Build profile dataclass
profile_debts = [
    DebtItem(
        name=d["name"],
        outstanding_amount=d["outstanding_amount"],
        interest_rate_percent=d["interest_rate_percent"],
        monthly_emi=d.get("monthly_emi", 0.0),
    )
    for d in st.session_state.debts
]

profile_goals = [
    GoalItem(
        name=g["name"],
        target_amount=g["target_amount"],
        target_date=g["target_date"],
        current_saved=g.get("current_saved", 0.0),
    )
    for g in st.session_state.goals
]

user_profile = FinancialProfile(
    monthly_income=st.session_state.monthly_income,
    fixed_expenses=st.session_state.fixed_expenses,
    variable_expenses=st.session_state.variable_expenses,
    existing_savings=st.session_state.existing_savings,
    desired_monthly_savings=st.session_state.desired_monthly_savings,
    dependents=st.session_state.dependents,
    is_variable_income=st.session_state.is_variable_income,
    salary_day=st.session_state.salary_day,
    debts=profile_debts,
    goals=profile_goals,
)

# Deterministic engine execution
engine_output = analyze_finances(user_profile)
health_score_res = calculate_health_score(user_profile, engine_output)
risk_profile_str, _ = compute_risk_profile(st.session_state.quiz_answers)
recommendations_plan = generate_recommendations(user_profile, engine_output, risk_level=risk_profile_str)


# ==================== TAB 3: HEALTH SCORE & DIAGNOSIS ====================
with tab_health:
    st.subheader("📊 Financial Health Diagnosis")
    st.caption("Comprehensive analysis of your savings rate, emergency buffer, debt liabilities, and goal feasibility.")

    # Top Row: Health Score Gauge & Executive Metrics
    g_col1, g_col2 = st.columns([1, 1])
    with g_col1:
        gauge_fig = create_health_gauge_chart(
            health_score_res.total_score,
            health_score_res.category_label,
            health_score_res.color_hex,
        )
        st.plotly_chart(gauge_fig, use_container_width=True)
        st.markdown(f"**Assessment:** {health_score_res.summary_sentence}")

    with g_col2:
        st.markdown("##### 📌 Key Monthly Financial Ratios")
        m1, m2 = st.columns(2)
        with m1:
            st.metric("Monthly Income", f"₹{engine_output.monthly_income:,.0f}")
            st.metric("Total Expenses", f"₹{engine_output.total_expenses:,.0f}")
        with m2:
            st.metric(
                "Savings Capacity",
                f"₹{engine_output.savings_capacity:,.0f}",
                delta=f"{engine_output.savings_rate_percent:.1f}% Rate",
                delta_color="normal" if engine_output.savings_capacity > 0 else "inverse",
            )
            st.metric("Target Realism", engine_output.target_realism.title())

    # Pillar Breakdown Cards
    st.markdown("##### 🏛️ The 4 Financial Health Pillars")
    pcols = st.columns(4)
    for idx, pil in enumerate(health_score_res.pillars):
        with pcols[idx]:
            st.markdown(
                f"""
                <div class='metric-pill'>
                    <div style='font-size:0.8rem; color:#64748B; font-weight:600;'>{pil.name.upper()}</div>
                    <div style='font-size:1.6rem; font-weight:800; color:#1E3A8A; margin:4px 0;'>{pil.score:.0f} <span style='font-size:0.9rem; color:#94A3B8;'>/ {pil.max_score:.0f}</span></div>
                    <div style='font-size:0.85rem; font-weight:700; color:#059669;'>{pil.status}</div>
                    <div style='font-size:0.75rem; color:#475569; margin-top:4px;'>{pil.feedback}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.markdown("---")

    # Second Section: Cashflow Breakdown & Emergency Cushion
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("##### 🥧 Monthly Budget Distribution")
        budget_df = pd.DataFrame([
            {"Category": "Fixed Essentials", "Amount": user_profile.fixed_expenses},
            {"Category": "Variable Spends", "Amount": user_profile.variable_expenses},
            {"Category": "Net Surplus Capacity", "Amount": max(0.0, engine_output.savings_capacity)},
        ])
        if engine_output.savings_capacity < 0:
            budget_df = pd.DataFrame([
                {"Category": "Fixed Essentials", "Amount": user_profile.fixed_expenses},
                {"Category": "Variable Spends", "Amount": user_profile.variable_expenses},
                {"Category": "Monthly Deficit", "Amount": abs(engine_output.savings_capacity)},
            ])

        pie_fig = px.pie(
            budget_df,
            values="Amount",
            names="Category",
            color_discrete_sequence=["#1E3A8A", "#F59E0B", "#059669" if engine_output.savings_capacity >= 0 else "#DC2626"],
            hole=0.45,
        )
        pie_fig.update_layout(height=280, margin=dict(l=10, r=10, t=20, b=10))
        st.plotly_chart(pie_fig, use_container_width=True)

    with c2:
        st.markdown("##### 🛡️ Emergency Cushion Progress")
        st.write(
            f"Target: **₹{engine_output.emergency_target_amount:,.0f}** "
            f"({engine_output.emergency_target_months} months of survival expenses)"
        )
        st.progress(engine_output.emergency_funded_percent / 100.0)
        
        ec_col1, ec_col2 = st.columns(2)
        with ec_col1:
            st.metric("Current Savings", f"₹{engine_output.emergency_current_amount:,.0f}")
        with ec_col2:
            st.metric("Funding Gap", f"₹{engine_output.emergency_gap:,.0f}")

        if engine_output.emergency_gap > 0:
            st.warning(
                f"⏳ At your current monthly capacity of ₹{engine_output.savings_capacity:,.0f}, "
                f"it will take **{engine_output.months_to_fund_emergency:.1f} months** of dedicated saving to fully fund this safety shield."
            )
        else:
            st.success("✅ Fully funded emergency cushion! Your downside is protected.")

    # Third Section: Debt Audit (Avalanche Waterfall)
    if engine_output.debts_sorted_by_priority:
        st.markdown("---")
        st.markdown("##### 💳 Debt Avalanche Analysis (Sorted by Interest Rate)")
        st.caption("Mathematically, paying the highest interest rate debt first saves the most money.")
        
        debt_rows = []
        for d in engine_output.debts_sorted_by_priority:
            debt_rows.append({
                "Liability Name": d["name"],
                "Outstanding (₹)": f"₹{d['outstanding']:,.0f}",
                "Interest Rate (% APR)": f"{d['interest_rate']}%",
                "Monthly Interest Drain": f"₹{d['monthly_interest_drain']:,.0f}",
                "Type": "High-Risk Debt" if d["is_high_interest"] else "Standard Debt",
                "Action Required": d["action"],
            })
        st.dataframe(pd.DataFrame(debt_rows), use_container_width=True, hide_index=True)


# ==================== TAB 4: RECOMMENDATIONS & ACTIONS ====================
with tab_plan:
    st.subheader("🎯 Step 4: Your Clear, Explained Action Plan")
    st.caption("Category-based asset allocation strictly following the Indian financial priority hierarchy.")

    # STANDOUT FEATURE: YOUR FIRST 3 ACTIONS THIS MONTH
    st.markdown("### 🏆 Your First 3 Actions This Month")
    for act in recommendations_plan.top_3_actions:
        badge_class = f"badge-{act.category.lower()}"
        st.markdown(
            f"""
            <div class='action-card'>
                <span class='action-badge {badge_class}'>{act.category} • STEP {act.step}</span>
                <div style='font-size:1.15rem; font-weight:700; color:#1E293B;'>{act.title}</div>
                <div style='font-size:0.95rem; color:#475569; margin: 6px 0;'>{act.description}</div>
                <div style='font-size:0.85rem; font-weight:600; color:#0369A1;'>⏰ Timing / Deadline: {act.deadline_or_timing}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("---")
    st.markdown("### 📋 Complete Allocation Waterfall (Priority Ordered)")
    st.caption("1. Emergency Fund ➡️ 2. High-Interest Debt Prepayment ➡️ 3. Goals by Horizon & Risk")

    for item in recommendations_plan.priority_items:
        priority_icon = "🛡️" if item.priority_level == 1 else ("💳" if item.priority_level == 2 else "🎯")
        with st.expander(f"{priority_icon} Priority #{item.priority_level}: {item.category_title} — ₹{item.allocation_amount_monthly:,.0f}/month", expanded=True):
            rcol1, rcol2 = st.columns([2, 1])
            with rcol1:
                st.markdown(f"**Target:** {item.target_name}")
                st.markdown(f"**Rationale:** {item.rationale}")
                st.markdown(f"**Recommended Asset Vehicles:**")
                for v in item.recommended_vehicles:
                    st.markdown(f"- {v}")
                st.info(f"🗓️ **Timing Action:** {item.timing_action}")

            with rcol2:
                st.markdown(f"**Risk Profile Alignment:**")
                st.caption(item.risk_alignment)
                st.markdown(f"**Why this advice? (The Numbers):**")
                st.caption(item.why_this_rule)

    # Cash Flow Timing Guidance
    if recommendations_plan.timing_guidance:
        st.markdown("---")
        st.markdown("### 🗓️ Smart Cash Flow & Horizon Timing")
        for tg in recommendations_plan.timing_guidance:
            st.markdown(f"- {tg}")

    # Real Estate & Gold Guidance (Mandatory Hackathon Requirements)
    st.markdown("---")
    g_col1, g_col2 = st.columns(2)
    with g_col1:
        st.markdown("#### 🏢 Real Estate & Land Advisory")
        st.caption(recommendations_plan.real_estate_guidance)
    with g_col2:
        st.markdown("#### 🥇 Gold Allocation Guidelines")
        st.caption(recommendations_plan.gold_guidance)

    # AI Explanation Layer (Feature 9)
    st.markdown("---")
    st.markdown("### 🤖 AI Financial Coach Explanation")
    st.caption(f"Explains your computed plan in simple {st.session_state.language} without hallucinating numbers.")

    with st.spinner("Generating personalized AI financial explanation..."):
        ai_explanation = generate_plan_explanation(
            user_profile,
            engine_output,
            recommendations_plan,
            language=st.session_state.language,
        )
        st.markdown(ai_explanation)


# ==================== TAB 5: WHAT-IF & GROWTH CHARTS ====================
with tab_simulator:
    st.subheader("🔮 What-If Simulator & Long-Term Compounding")
    st.caption("See how small adjustments in monthly savings and asset choices dramatically impact your financial future.")

    sim_col1, sim_col2 = st.columns([1, 2])
    with sim_col1:
        st.markdown("##### 🎛️ Simulation Controls")
        extra_monthly = st.slider(
            "Extra Monthly Savings (₹)",
            min_value=0,
            max_value=25000,
            value=3000,
            step=500,
            help="Additional savings from trimming dining out, subscriptions, or side income.",
        )
        sim_years = st.slider(
            "Investment Horizon (Years)",
            min_value=1,
            max_value=25,
            value=10,
            step=1,
        )
        base_monthly = max(0.0, engine_output.savings_capacity)
        total_monthly_sim = base_monthly + extra_monthly

        st.metric("Total Monthly Invested", f"₹{total_monthly_sim:,.0f}")
        st.metric("Total Principal Injected", f"₹{total_monthly_sim * sim_years * 12:,.0f}")

    with sim_col2:
        st.markdown("##### 📈 Growth Comparison: Bank FD vs Index SIP vs Gold")
        st.caption("Returns based on editable assumptions in config: FD (7.0%), Index SIP (12.0%), Gold SGB (9.0%).")

        months = sim_years * 12
        year_points = list(range(1, sim_years + 1))
        fd_curve = []
        sip_curve = []
        gold_curve = []
        principal_curve = []

        for y in year_points:
            m = y * 12
            principal_curve.append(total_monthly_sim * m)
            fd_curve.append(calculate_future_value_sip(total_monthly_sim, m, DEFAULT_ASSUMPTIONS["fixed_deposit"]))
            sip_curve.append(calculate_future_value_sip(total_monthly_sim, m, DEFAULT_ASSUMPTIONS["index_fund_sip"]))
            gold_curve.append(calculate_future_value_sip(total_monthly_sim, m, DEFAULT_ASSUMPTIONS["gold"]))

        chart_df = pd.DataFrame({
            "Years": year_points,
            "Total Principal Invested": principal_curve,
            "Bank FD (7%)": fd_curve,
            "Gold SGB / ETF (9%)": gold_curve,
            "Index Fund SIP (12%)": sip_curve,
        })

        growth_fig = px.line(
            chart_df,
            x="Years",
            y=["Total Principal Invested", "Bank FD (7%)", "Gold SGB / ETF (9%)", "Index Fund SIP (12%)"],
            color_discrete_map={
                "Total Principal Invested": "#94A3B8",
                "Bank FD (7%)": "#3B82F6",
                "Gold SGB / ETF (9%)": "#F59E0B",
                "Index Fund SIP (12%)": "#059669",
            },
            markers=True,
        )
        growth_fig.update_layout(
            height=320,
            yaxis_title="Future Accumulated Value (₹)",
            xaxis_title="Investment Horizon (Years)",
            margin=dict(l=10, r=10, t=10, b=10),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        )
        st.plotly_chart(growth_fig, use_container_width=True)

        wealth_delta = sip_curve[-1] - fd_curve[-1]
        st.success(
            f"💡 In {sim_years} years, choosing a disciplined **Index Fund SIP (12%)** over a traditional **Fixed Deposit (7%)** "
            f"creates an extra **₹{wealth_delta:,.0f}** in pure compounding wealth on the exact same monthly savings!"
        )

    st.markdown("---")
    st.markdown("### ❓ First-Time Investor FAQs (Why This Advice?)")
    fcol1, fcol2, fcol3 = st.columns(3)
    with fcol1:
        with st.expander("Why not single stocks or crypto?", expanded=False):
            st.write(answer_faq("why_not_stocks", language=st.session_state.language))
    with fcol2:
        with st.expander("Why not buy land right away?", expanded=False):
            st.write(answer_faq("why_not_land", language=st.session_state.language))
    with fcol3:
        with st.expander("What if markets crash after I start?", expanded=False):
            st.write(answer_faq("market_crash", language=st.session_state.language))

    st.markdown("---")
    st.markdown("### 📥 Download Your Financial BluePrint")
    st.caption("Generate a complete, personalized report as Markdown for offline reading and records.")
    
    rep_md = generate_markdown_report(
        user_profile,
        engine_output,
        health_score_res,
        recommendations_plan,
        user_name=st.session_state.get("persona_name", "Investor"),
    )
    st.download_button(
        label="📄 Download Plan as Markdown (.md)",
        data=rep_md,
        file_name=f"ArthMitra_Plan_{date.today().isoformat()}.md",
        mime="text/markdown",
        use_container_width=True,
    )
