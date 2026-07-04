from decimal import Decimal, ROUND_HALF_UP

KRW = Decimal("1")
PERCENT = Decimal("100")
TAX_RATE = Decimal("0.154")


def percent_to_rate(percent: Decimal) -> Decimal:
    return percent / PERCENT


def round_krw(amount: Decimal) -> Decimal:
    return amount.quantize(KRW, rounding=ROUND_HALF_UP)


def installment_interest(
    monthly_amount: Decimal,
    annual_rate_percent: Decimal,
    months: int,
    tax_free: bool = False,
) -> Decimal:
    rate = percent_to_rate(annual_rate_percent)
    weighted_months = Decimal(months * (months + 1)) / Decimal("2")
    gross_interest = monthly_amount * (rate / Decimal("12")) * weighted_months
    if tax_free:
        return round_krw(gross_interest)
    return round_krw(gross_interest * (Decimal("1") - TAX_RATE))


def lump_sum_interest(
    principal: Decimal,
    annual_rate_percent: Decimal,
    months: int,
    tax_free: bool = False,
) -> Decimal:
    rate = percent_to_rate(annual_rate_percent)
    gross_interest = principal * rate * (Decimal(months) / Decimal("12"))
    if tax_free:
        return round_krw(gross_interest)
    return round_krw(gross_interest * (Decimal("1") - TAX_RATE))

