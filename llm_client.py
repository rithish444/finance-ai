"""
llm_client.py - Grounded AI Explanation Layer for ArthMitra.
Explains computed financial plans in simple, jargon-free Indian language.
Strictly grounded on computed engine numbers and local knowledge files.
Features automatic fallback to rich deterministic templates if no API key is set.
"""

import os
import glob
import json
from typing import Dict, Any, Optional
import urllib.request
import urllib.error

from finance_engine import EngineOutput, FinancialProfile
from recommender import RecommendationPlan


def load_knowledge_base() -> str:
    """Loads all markdown files from the local knowledge/ folder."""
    knowledge_dir = os.path.join(os.path.dirname(__file__), "knowledge")
    md_files = glob.glob(os.path.join(knowledge_dir, "*.md"))
    chunks = []
    for fpath in md_files:
        try:
            with open(fpath, "r", encoding="utf-8") as f:
                chunks.append(f.read())
        except Exception:
            pass
    return "\n\n---\n\n".join(chunks)


def _call_gemini_api(api_key: str, prompt: str, model: str = "gemini-1.5-flash") -> Optional[str]:
    """Invokes Gemini API via standard urllib without external heavy SDK dependencies."""
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
    headers = {"Content-Type": "application/json"}
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.2, "maxOutputTokens": 1000},
    }

    try:
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(url, data=data, headers=headers, method="POST")
        with urllib.request.urlopen(req, timeout=12) as response:
            res_body = response.read().decode("utf-8")
            res_json = json.loads(res_body)
            candidates = res_json.get("candidates", [])
            if candidates:
                parts = candidates[0].get("content", {}).get("parts", [])
                if parts:
                    return parts[0].get("text", "").strip()
    except Exception:
        pass
    return None


def generate_plan_explanation(
    profile: FinancialProfile,
    engine_out: EngineOutput,
    plan: RecommendationPlan,
    language: str = "English",
) -> str:
    """
    Generates a clear explanation of the computed plan.
    Attempts live LLM call if configured; seamlessly falls back to rich templates.
    """
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    provider = os.getenv("LLM_PROVIDER", "gemini").lower()

    if api_key and provider == "gemini":
        knowledge_text = load_knowledge_base()
        context_data = {
            "monthly_income": engine_out.monthly_income,
            "savings_capacity": engine_out.savings_capacity,
            "savings_rate_percent": engine_out.savings_rate_percent,
            "emergency_target_months": engine_out.emergency_target_months,
            "emergency_target_amount": engine_out.emergency_target_amount,
            "emergency_gap": engine_out.emergency_gap,
            "high_interest_debt": engine_out.high_interest_debt_outstanding,
            "top_actions": [a.title for a in plan.top_3_actions],
            "language": language,
        }

        prompt = f"""
You are ArthMitra, an empathetic and highly practical personal finance coach for Indian first-time investors.
Explain this user's computed financial plan clearly in {language}.

GROUNDING RULES:
1. ONLY reference the exact numbers provided in CONTEXT DATA below. NEVER modify, invent, or hallucinate different figures.
2. Ground explanations strictly in this knowledge base:
{knowledge_text[:2000]}

CONTEXT DATA:
{json.dumps(context_data, indent=2)}

Format with:
- 💡 **Executive Summary**: 2 sentences on their current standing.
- 🛡️ **Why Emergency Fund & High-Debt Come First**: Explain the rationale behind the priority ordering.
- 📈 **Why Category Index/FD Investing over Single Stocks**: Explain diversification and peace of mind.
- 🎯 **Your Golden Rule This Month**: One encouraging closing sentence.
"""
        response = _call_gemini_api(api_key, prompt)
        if response:
            return response

    # Fallback: High Quality Deterministic Templates
    return _generate_template_explanation(profile, engine_out, plan, language)


def _generate_template_explanation(
    profile: FinancialProfile,
    engine_out: EngineOutput,
    plan: RecommendationPlan,
    language: str = "English",
) -> str:
    """Rich deterministic explanation in English, Hindi, or Tamil."""
    inc = f"₹{engine_out.monthly_income:,.0f}"
    surplus = f"₹{engine_out.savings_capacity:,.0f}"
    sr = f"{engine_out.savings_rate_percent:.1f}%"
    gap = f"₹{engine_out.emergency_gap:,.0f}"
    em_target = f"₹{engine_out.emergency_target_amount:,.0f}"

    if language == "Hindi":
        summary = (
            f"### 💡 वित्तीय सारांश (Financial Summary)\n"
            f"आपकी मासिक आय **{inc}** है, जिसमें से सभी आवश्यक खर्चों के बाद आपके पास प्रति माह **{surplus}** की बचत क्षमता है (बचत दर: **{sr}**)।\n\n"
            f"### 🛡️ आपातकालीन कोष और कर्ज को प्राथमिकता क्यों?\n"
            f"- **आपातकालीन सुरक्षा कवच**: आपके पास **{engine_out.emergency_target_months} महीनों** का आपातकालीन लक्ष्य **{em_target}** है। वर्तमान में इसमें **{gap}** की कमी है। जब तक यह फंड तैयार नहीं होता, शेयर बाजार में पैसा लगाना जोखिम भरा हो सकता है।\n"
        )
        if engine_out.high_interest_debt_outstanding > 0:
            summary += (
                f"- **उच्च ब्याज वाले कर्ज से मुक्ति**: आपके ऊपर **₹{engine_out.high_interest_debt_outstanding:,.0f}** का उच्च ब्याज वाला कर्ज (क्रेडिट कार्ड/पर्सनल लोन) है। इस कर्ज को चुकाने से मिलने वाला लाभ किसी भी म्यूचुअल फंड से अधिक सुरक्षित और गारंटीड है।\n"
            )
        summary += (
            f"\n### 📈 विशिष्ट शेयरों के बजाय एसेट कैटेगरी क्यों?\n"
            f"एक नए निवेशक के लिए किसी एक शेयर को चुनना जोखिम भरा होता है। निफ्टी 50 इंडेक्स फंड और एफडी आपको भारत की शीर्ष 50 कंपनियों में बिना किसी तनाव के विविधता प्रदान करते हैं।\n\n"
            f"### 🎯 इस महीने का स्वर्णिम नियम\n"
            f"वेतन मिलने के 3 दिनों के भीतर ऑटो-डेबिट सेट करें और आपातकालीन फंड को प्राथमिकता दें।"
        )
        return summary

    elif language == "Tamil":
        summary = (
            f"### 💡 நிதி சுருக்கம் (Financial Summary)\n"
            f"உங்கள் மாதாந்திர வருமானம் **{inc}**. அனைத்து செலவுகளுக்கும் பிறகு, உங்கள் மாதாந்திர சேமிப்பு திறன் **{surplus}** (சேமிப்பு விகிதம்: **{sr}**).\n\n"
            f"### 🛡️ அவசரகால நிதி மற்றும் கடனுக்கு ஏன் முதல் முன்னுரிமை?\n"
            f"- **அவசரகால நிதி**: உங்கள் குடும்பத்திற்கு **{engine_out.emergency_target_months} மாத** அவசர இலக்கு **{em_target}**. இதில் இன்னும் **{gap}** பற்றாக்குறை உள்ளது. இந்த பாதுகாப்பு இல்லாமல் பங்குச்சந்தையில் முதலீடு செய்வது ஆபத்தானது.\n"
        )
        if engine_out.high_interest_debt_outstanding > 0:
            summary += (
                f"- **அதிக வட்டி கடன் அடைப்பு**: உங்களிடம் **₹{engine_out.high_interest_debt_outstanding:,.0f}** அதிக வட்டி கடன் உள்ளது. இதை உடனே அடைப்பது எந்த முதலீட்டையும் விட சிறந்த உத்தரவாதமான லாபமாகும்.\n"
            )
        summary += (
            f"\n### 📈 தனி பங்குகளுக்கு பதிலாக சொத்து பிரிவுகள் ஏன்?\n"
            f"புதிய முதலீட்டாளர்கள் தனி பங்குகளை கணிப்பது கடினம். நிஃப்டி 50 இன்டெக்ஸ் ஃபண்டுகள் மற்றும் எஃப்.டி ஆகியவை ஆபத்து குறைந்த சீரான வளர்ச்சியைத் தரும்.\n\n"
            f"### 🎯 இந்த மாதத்தின் முக்கிய குறிக்கோள்\n"
            f"சம்பளம் வந்த 3 நாட்களுக்குள் அவசரகால நிதிக்கான ஆட்டோ-டெபிட் அமைத்து உங்கள் சேமிப்பைத் தொடங்குங்கள்."
        )
        return summary

    # Default English
    summary = (
        f"### 💡 Executive Summary\n"
        f"With a monthly take-home income of **{inc}** and living expenses of **₹{engine_out.total_expenses:,.0f}**, "
        f"you retain an investable monthly surplus of **{surplus}** (Savings Rate: **{sr}**).\n\n"
        f"### 🛡️ Why Emergency Shield & Debt Eradication Come First\n"
        f"1. **Emergency Buffer**: Your target is **{em_target}** ({engine_out.emergency_target_months} months of core living expenses). "
    )
    if engine_out.emergency_gap > 0:
        summary += (
            f"You currently have a gap of **{gap}**. Investing aggressively in stocks without this safety net forces panic selling if unexpected hospital or family expenses strike.\n"
        )
    else:
        summary += "Your emergency cushion is 100% funded! You have established a strong financial shield.\n"

    if engine_out.high_interest_debt_outstanding > 0:
        summary += (
            f"2. **The 36%+ Interest Leak**: You carry **₹{engine_out.high_interest_debt_outstanding:,.0f}** in high-interest liabilities. "
            f"Paying off credit card debt yields an immediate risk-free return of 36-42%, which easily outperforms any market asset class.\n"
        )

    summary += (
        f"\n### 📈 Why Asset Categories (Index Funds & FDs) Rather Than Single Stocks?\n"
        f"- **No Stock-Picking Anxiety**: Picking individual stocks requires accounting knowledge and continuous tracking. Over 75% of active funds in India fail to beat the Nifty 50 Index over 7+ years.\n"
        f"- **Horizon Matching**: Money required in under 3 years is safeguarded in FDs or liquid funds, while money needed after 5+ years compounds through broad-market index SIPs.\n\n"
        f"### 🎯 Your Golden Rule This Month\n"
        f"Automate your savings 3 days after salary day before lifestyle inflation takes over. Consistency beats market timing."
    )
    return summary


def answer_faq(question_key: str, language: str = "English") -> str:
    """Answers common investor dilemmas grounded in Indian financial prudence."""
    faqs = {
        "why_not_stocks": {
            "English": (
                "**Why index funds instead of individual stocks or crypto?**\n\n"
                "Individual stocks carry company-specific risk: fraud, competition, or sector downturns can wipe out 50%+ of your capital. "
                "Broad-market index funds (like Nifty 50) automatically own the top 50 engines of the Indian economy. If one company stumbles, "
                "it is replaced. For 95% of retail savers, index investing maximizes long-term compounding with minimal anxiety."
            ),
            "Hindi": (
                "**व्यक्तिगत शेयरों या क्रिप्टो के बजाय इंडेक्स फंड क्यों?**\n\n"
                "व्यक्तिगत शेयरों में कंपनी-विशिष्ट जोखिम होता है। निफ्टी 50 इंडेक्स फंड भारत की शीर्ष 50 कंपनियों में आपका पैसा फैलाता है, "
                "जिससे जोखिम कम और दीर्घकालिक रिटर्न स्थिर रहता है।"
            ),
            "Tamil": (
                "**தனி பங்குகள் அல்லது கிரிப்டோவிற்கு பதிலாக இன்டெக்ஸ் ஃபண்டுகள் ஏன்?**\n\n"
                "தனி பங்குகளில் நஷ்டம் அடையும் ஆபத்து அதிகம். நிஃப்டி 50 இன்டெக்ஸ் ஃபண்டுகள் இந்தியாவின் சிறந்த 50 நிறுவனங்களில் பணத்தை பிரித்து முதலீடு செய்வதால் பாதுகாப்பு அதிகம்."
            ),
        },
        "why_not_land": {
            "English": (
                "**Why not buy physical land or property right away?**\n\n"
                "Physical real estate requires massive upfront capital, hefty stamp duty (5-7%), and is highly illiquid. "
                "If you need emergency money, you cannot sell one square foot of a plot. For early-career investors, locking all cashflow "
                "into heavy home loan EMIs destroys financial flexibility. Consider REITs if you desire liquid commercial real estate exposure."
            ),
            "Hindi": (
                "**तुरंत जमीन या रियल एस्टेट क्यों न खरीदें?**\n\n"
                "जमीन खरीदने के लिए बहुत बड़ी पूंजी की आवश्यकता होती है और इसे आपातकाल में तुरंत बेचा नहीं जा सकता। शुरुआती निवेशकों के लिए होम लोन की ईएमआई में बंधना जोखिम भरा होता है।"
            ),
            "Tamil": (
                "**நிலம் அல்லது ரியல் எஸ்டேட் உடனடியாக ஏன் வாங்கக்கூடாது?**\n\n"
                "நிலம் வாங்க அதிக முன்பணம் தேவை மற்றும் அவசரத்திற்கு உடனே விற்க முடியாது. ஆரம்ப கால முதலீட்டாளர்களுக்கு இது பண நெருக்கடியை ஏற்படுத்தும்."
            ),
        },
        "market_crash": {
            "English": (
                "**What should I do if the stock market crashes right after I start?**\n\n"
                "Celebrate and continue your SIP! During a market dip, your fixed monthly amount buys more units at discounted prices. "
                "Because your goal horizon is 5+ years, corrections are golden accumulation opportunities. Never stop an index SIP in a bear market."
            ),
            "Hindi": (
                "**अगर शुरुआत के बाद शेयर बाजार गिर जाए तो क्या करें?**\n\n"
                "घबराएं नहीं और अपनी एसआईपी (SIP) जारी रखें। बाजार गिरने पर आपके उसी पैसे में अधिक यूनिट्स मिलती हैं, जो भविष्य में बड़ा लाभ देती हैं।"
            ),
            "Tamil": (
                "**முதலீடு செய்த பின் சந்தை சரிந்தால் என்ன செய்வது?**\n\n"
                "பயப்பட வேண்டாம்! உங்கள் SIP முதலீட்டை தொடருங்கள். சந்தை சரியும்போது குறைந்த விலையில் அதிக யூனிட்கள் கிடைக்கும்."
            ),
        },
    }

    item = faqs.get(question_key, faqs["why_not_stocks"])
    return item.get(language, item["English"])
