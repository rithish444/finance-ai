# 🪙 ArthMitra (अर्थमित्र / அர்த்தமித்ரா)
### AI Personal Finance Coach for India • Arthaton Hackathon Project

> **"Clear, unbiased, category-based personal finance advice for Indian first-time investors."**

ArthMitra is a demo-ready, full-stack financial intelligence application built with Python and Streamlit. It solves the widespread problem of financial illiteracy among first-time earners in India by translating chaotic incomes, debts, and life goals into an actionable, mathematical, and explained financial roadmap.

---

## 🚀 Quickstart (One Command Run)

### 1. Prerequisites
- Python 3.11+ installed.

### 2. Installation & Launch
```bash
# Clone or navigate to the repository
cd "finance AI"

# Install dependencies
pip install -r requirements.txt

# Run the application
streamlit run app.py
```
Open your browser at `http://localhost:8501`.

---

## 🌟 Key Features

### 1. 📋 Comprehensive Indian Financial Onboarding
- Inflows, fixed obligations, variable expenses, and existing emergency savings.
- Family dependents consideration (automatically calibrates safety cushion duration).
- Debt liabilities tracking with interest rate APR and EMI drain.
- **SMS Parser (Standout Feature)**: Paste multi-line transaction SMS messages from Indian banks (SBI, HDFC, ICICI, Axis) and UPI apps (GPay, PhonePe, Paytm) to automatically categorize discretionary spending into Food & Dining, Groceries/Quick Commerce, Fuel, etc.

### 2. 🧠 5-Question Indian Risk Profile Quiz
- Evaluates investment horizon, reaction to market drawdowns, income stability, and capital preservation mindset.
- Outputs **Conservative (Low)**, **Balanced (Medium)**, or **Aggressive (High)** risk profiles.

### 3. 📊 100-Point Financial Health Score
- Real-time Plotly indicator gauge scoring overall financial health (0 to 100).
- 4 Pillar Breakdown:
  1. **Savings Rate** (30 pts)
  2. **Emergency Safety Net** (25 pts)
  3. **Debt Health & Avalanche** (25 pts)
  4. **Goal Feasibility & Realism** (20 pts)

### 4. 🎯 Category-Based Asset Recommendations & Priority Waterfall
- **Never recommends individual stocks or crypto**; recommends broad asset categories (Liquid Funds, Bank FDs, Hybrid Funds, Index SIPs, PPF, NPS, Gold SGB).
- Strict Indian financial priority order:
  1. **Emergency Cushion** (6–12 months of survival expenses).
  2. **High-Interest Debt Eradication** (Avalanche method on liabilities ≥ 10% APR).
  3. **Horizon-Matched Goals** (Under 1 yr, 1–3 yrs, 3–5 yrs, 5+ yrs).
- **"Your First 3 Actions This Month"** card on the results page.
- **"Why this advice?"** expanders displaying the mathematical rule behind each recommendation.
- **Cultural Guidance**: Sensible advisory on direct physical land/property illiquidity and a 5–10% cap on gold via Sovereign Gold Bonds (SGB).

### 5. 🗓️ Cash Flow Timing & De-risking Guidance
- Schedules automated monthly SIPs 2–3 days following the user's monthly salary arrival date.
- Proactive de-risking alerts when any goal enters the final 12-month window.

### 6. 🔮 Interactive What-If Simulator & Growth Chart
- Sliders for extra monthly savings and investment horizons.
- Interactive multi-asset compounding chart comparing **Bank FD (7%) vs Gold SGB (9%) vs Index Fund SIP (12%)**.

### 7. 🤖 Grounded AI Explanation Layer & Multilingual Support
- Grounded on local knowledge base (`knowledge/*.md`).
- Strictly references computed figures without mathematical hallucinations.
- Instant language toggle for **English, Hindi (हिन्दी), and Tamil (தமிழ்)**.
- Robust deterministic fallback when running offline or without an API key.

### 8. 📄 Export & Reporting
- One-click downloadable personalized **Markdown BluePrint** for offline review.

---

## 👤 Bundled 1-Click Demo Personas

On the sidebar, click any persona to test the entire application instantly:
1. **Aarav Sharma (Student/Intern in Bengaluru)**: Earning ₹18,000 stipend, starting small with zero debt, building initial investment discipline.
2. **Priya Venkatesh (Salaried Software Engineer in Chennai)**: Earning ₹85,000, supporting parents, carrying high-interest credit card debt that requires immediate avalanche payoff.
3. **Rajesh Patel (Kirana Store Owner in Ahmedabad)**: Variable ₹65,000 monthly income with 3 dependents, needing a 12-month emergency shield and conservative wealth accumulation.

---

## 🏛️ Project Architecture

```
finance AI/
├── app.py                      # Main Streamlit web application
├── finance_engine.py           # Pure deterministic financial math engine (100% test coverage)
├── recommender.py              # Category asset recommender & timing logic
├── health_score.py             # 100-point scoring algorithm & gauge visualization
├── sms_parser.py               # Regex & rule-based bank/UPI SMS expense extractor
├── llm_client.py               # Grounded AI explanation layer with fallback templates
├── report.py                   # Markdown report generator
├── config.py                   # Financial constants, assumptions, and color themes
├── ASSUMPTIONS.md              # Autonomous design decisions & rationale
├── DEMO_SCRIPT.md              # 2-minute judge pitch script + 5 Q&A answers
├── requirements.txt            # Python dependencies
├── .env.example                # LLM environment configuration template
├── data/
│   └── personas.json           # Bundled demo personas
├── knowledge/                  # Local financial knowledge base
│   ├── sip.md
│   ├── fd.md
│   ├── ppf.md
│   ├── nps.md
│   ├── index_funds.md
│   ├── gold.md
│   └── emergency_fund.md
└── tests/                      # Automated unit test suite (22 passed tests)
    ├── test_finance_engine.py
    ├── test_recommender.py
    ├── test_health_score.py
    ├── test_sms_parser.py
    └── test_personas_and_report.py
```

---

## 🧪 Running the Unit Tests

Execute the comprehensive test suite with `pytest`:
```bash
python -m pytest tests/
```
Output:
```
============================= 22 passed in 0.34s ==============================
```

---

## ⚖️ Mandatory Disclaimer

*Disclaimer: This application provides educational guidance and financial literacy tools, not registered investment advice. Please consult a SEBI-registered investment advisor before making financial investments.*
