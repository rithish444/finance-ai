"""
Unit tests for sms_parser.py.
Verifies bank/UPI SMS regex parsing, amount extraction, and category assignment.
"""

from sms_parser import parse_sms_line, parse_sms_text_block


def test_parse_swiggy_upi_sms():
    sms = "Dear SBI User, your A/c X1234 debited by Rs 450.00 on 12-Nov-26 by UPI to Swiggy ref 987654321."
    res = parse_sms_line(sms)
    assert res is not None
    assert res.amount == 450.0
    assert res.txn_type == "DEBIT"
    assert "swiggy" in res.merchant.lower()
    assert res.category == "Food & Dining"


def test_parse_blinkit_groceries_sms():
    sms = "HDFC Bank: Rs 1,250.00 debited from a/c **4321 on 15-11-26 to BLINKIT. Bal: Rs 45,200.00."
    res = parse_sms_line(sms)
    assert res is not None
    assert res.amount == 1250.0
    assert res.txn_type == "DEBIT"
    assert res.category == "Groceries & Quick Commerce"


def test_parse_uber_transport_sms():
    sms = "Paid Rs 350.00 to Uber India via Google Pay UPI."
    res = parse_sms_line(sms)
    assert res is not None
    assert res.amount == 350.0
    assert res.category == "Transport & Fuel"


def test_parse_credit_sms_ignored_for_expenses():
    sms = "Salary credited: INR 65,000.00 in your A/c 1234 on 01-Nov-26 by INFOSYS LTD."
    res = parse_sms_line(sms)
    assert res is not None
    assert res.txn_type == "CREDIT"


def test_parse_sms_text_block_aggregation():
    sample_block = """
    Dear SBI User, your A/c X1234 debited by Rs 450.00 on 12-Nov by UPI to Swiggy.
    HDFC Bank: Rs 1,250.00 debited from a/c **4321 to BLINKIT.
    Paid Rs 350.00 to Uber India via Google Pay UPI.
    Salary credited: INR 50,000 in your A/c 1234.
    """
    txns, cat_totals, total = parse_sms_text_block(sample_block)
    assert len(txns) == 3  # 3 debits, salary credit ignored from expense total
    assert total == 2050.0  # 450 + 1250 + 350
    assert "Food & Dining" in cat_totals
    assert cat_totals["Food & Dining"] == 450.0
    assert cat_totals["Groceries & Quick Commerce"] == 1250.0
    assert cat_totals["Transport & Fuel"] == 350.0
