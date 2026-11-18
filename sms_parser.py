"""
sms_parser.py - Rule-Based Indian Banking & UPI SMS Parser for ArthMitra.
Parses multi-line pasted transaction SMS messages into structured expense categories
to pre-fill monthly variable expenses.
"""

import re
from dataclasses import dataclass
from typing import List, Dict, Tuple, Optional


@dataclass
class ParsedTransaction:
    amount: float
    txn_type: str  # 'DEBIT' or 'CREDIT'
    merchant: str
    category: str
    original_text: str


CATEGORY_KEYWORDS: Dict[str, List[str]] = {
    "Food & Dining": [
        "swiggy", "zomato", "mcdonald", "starbucks", "domino", "kfc",
        "cafe", "restaurant", "burger", "pizza", "dine", "eatclub", "chai"
    ],
    "Groceries & Quick Commerce": [
        "blinkit", "zepto", "instamart", "bigbasket", "dmart", "reliance fresh",
        "spencers", "kirana", "supermarket", "provision", "country delight"
    ],
    "Transport & Fuel": [
        "uber", "ola", "rapido", "metro", "shell", "petrol", "fuel", "hpcl",
        "bpcl", "ioc", "indian oil", "fastag", "irctc", "redbus", "flight"
    ],
    "Shopping & E-Commerce": [
        "amazon", "flipkart", "myntra", "ajio", "meesho", "nykaa", "tata cliq",
        "zara", "h&m", "retail", "decathlon", "lifestyle"
    ],
    "Bills, OTT & Entertainment": [
        "netflix", "spotify", "prime", "hotstar", "youtube", "bookmyshow",
        "pvr", "inox", "airtel", "jio", "vi", "bescom", "tneb", "electricity", "broadband"
    ],
    "Healthcare & Medical": [
        "apollo", "1mg", "pharmeasy", "medplus", "hospital", "clinic", "pharmacy", "doctor"
    ],
}


def _clean_amount(amt_str: str) -> float:
    """Cleans commas and converts string to float."""
    try:
        clean = amt_str.replace(",", "").strip()
        return round(float(clean), 2)
    except Exception:
        return 0.0


def parse_sms_line(line: str) -> Optional[ParsedTransaction]:
    """Parses a single SMS message string."""
    line_clean = line.strip()
    if not line_clean:
        return None

    # Detect Debit vs Credit
    lower_line = line_clean.lower()
    is_credit = any(w in lower_line for w in ["credited", "received", "deposited", "refund"])
    is_debit = any(w in lower_line for w in ["debited", "spent", "paid", "deducted", "withdrawn", "sent", "vpa"])

    # If neither explicit, assume debit if it has merchant words or UPI
    if not is_credit and not is_debit:
        if "upi" in lower_line or "bal" in lower_line or "txn" in lower_line:
            is_debit = True
        else:
            return None

    txn_type = "CREDIT" if is_credit else "DEBIT"

    # Extract Amount: Rs. / INR / INR. / Rs
    amt_match = re.search(r"(?:rs\.?|inr\.?|inr|\u20B9)\s*([0-9,]+(?:\.[0-9]{1,2})?)", line_clean, re.IGNORECASE)
    if not amt_match:
        # Fallback: check standalone digits with decimal e.g. 450.00
        amt_match = re.search(r"\b([0-9,]{2,}\.[0-9]{2})\b", line_clean)
        if not amt_match:
            return None

    amount = _clean_amount(amt_match.group(1))
    if amount <= 0:
        return None

    # Extract Merchant / Payee
    merchant = "Unknown Merchant"
    # Patterns like "to <merchant>", "at <merchant>", "for <merchant>", "info: <merchant>", "VPA <merchant>"
    merchant_match = re.search(
        r"(?:to|at|for|info:|vpa)\s+([A-Za-z0-9*_\-&.\s]{3,25})(?:\s+on|\s+ref|\s+bal|\s+via|\.|$)",
        line_clean,
        re.IGNORECASE,
    )
    if merchant_match:
        cand = merchant_match.group(1).strip()
        # Clean noise words
        cand = re.sub(r"(ref|bal|avl|upi|a/c|acct|dated).*", "", cand, flags=re.IGNORECASE).strip()
        if len(cand) >= 2:
            merchant = cand

    # Categorize
    category = "Other Expenses"
    merchant_search = f"{merchant} {lower_line}".lower()
    for cat, keywords in CATEGORY_KEYWORDS.items():
        if any(kw in merchant_search for kw in keywords):
            category = cat
            break

    return ParsedTransaction(
        amount=amount,
        txn_type=txn_type,
        merchant=merchant.strip(" .*-"),
        category=category,
        original_text=line_clean,
    )


def parse_sms_text_block(text: str) -> Tuple[List[ParsedTransaction], Dict[str, float], float]:
    """
    Parses a multi-line pasted string of Indian banking/UPI SMS notifications.
    Returns:
    - List of ParsedTransaction objects
    - Dictionary mapping categories to total spend
    - Total debited variable expenses
    """
    transactions: List[ParsedTransaction] = []
    category_totals: Dict[str, float] = {cat: 0.0 for cat in CATEGORY_KEYWORDS.keys()}
    category_totals["Other Expenses"] = 0.0
    total_debit = 0.0

    lines = [line.strip() for line in text.split("\n") if line.strip()]
    for line in lines:
        parsed = parse_sms_line(line)
        if parsed and parsed.txn_type == "DEBIT":
            transactions.append(parsed)
            category_totals[parsed.category] = round(category_totals[parsed.category] + parsed.amount, 2)
            total_debit += parsed.amount

    # Remove zero categories
    active_categories = {k: v for k, v in category_totals.items() if v > 0}

    return transactions, active_categories, round(total_debit, 2)
