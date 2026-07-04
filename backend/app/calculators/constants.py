from decimal import Decimal

YOUTH_LEAP_MONTHS = 60
YOUTH_LEAP_MAX_MONTHLY_AMOUNT = Decimal("700000")

YOUTH_FUTURE_MONTHS = 36
YOUTH_FUTURE_MAX_MONTHLY_AMOUNT = Decimal("500000")
YOUTH_FUTURE_MATCHING_RATES = {
    "general": Decimal("0.06"),
    "preferred": Decimal("0.12"),
}
YOUTH_FUTURE_NAMES = {
    "general": "청년미래적금 일반형",
    "preferred": "청년미래적금 우대형",
}

