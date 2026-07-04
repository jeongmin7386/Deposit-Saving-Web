from decimal import Decimal

from app.calculators.common import installment_interest
from app.calculators.constants import (
    YOUTH_LEAP_MAX_MONTHLY_AMOUNT,
    YOUTH_LEAP_MONTHS,
)
from app.schemas.requests import YouthLeapRequest
from app.schemas.responses import CalculationResult


def _monthly_government_contribution(annual_income: Decimal | None) -> Decimal:
    if annual_income is None:
        return Decimal("0")
    if annual_income <= Decimal("24000000"):
        return Decimal("33000")
    if annual_income <= Decimal("36000000"):
        return Decimal("25000")
    if annual_income <= Decimal("48000000"):
        return Decimal("20000")
    if annual_income <= Decimal("60000000"):
        return Decimal("16000")
    return Decimal("0")


def calculate_youth_leap(request: YouthLeapRequest) -> CalculationResult:
    principal = request.monthly_amount * Decimal(YOUTH_LEAP_MONTHS)
    bank_interest = installment_interest(
        monthly_amount=request.monthly_amount,
        annual_rate_percent=request.annual_rate,
        months=YOUTH_LEAP_MONTHS,
        tax_free=True,
    )
    government_contribution = (
        _monthly_government_contribution(request.annual_income)
        * Decimal(YOUTH_LEAP_MONTHS)
    )

    notices = [
        "청년도약계좌는 60개월 납입 기준의 간이 계산입니다.",
        "개인소득을 입력하지 않으면 정부기여금은 0원으로 계산됩니다.",
    ]

    return CalculationResult(
        product_type="youth-leap",
        product_name="청년도약계좌",
        months=YOUTH_LEAP_MONTHS,
        principal=principal,
        bank_interest=bank_interest,
        government_contribution=government_contribution,
        maturity_amount=principal + bank_interest + government_contribution,
        notices=notices,
    )
