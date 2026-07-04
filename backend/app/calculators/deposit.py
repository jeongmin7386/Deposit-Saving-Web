from decimal import Decimal

from app.calculators.common import lump_sum_interest
from app.schemas.requests import DepositRequest
from app.schemas.responses import CalculationResult


def calculate_deposit(request: DepositRequest) -> CalculationResult:
    principal = request.monthly_amount
    bank_interest = lump_sum_interest(
        principal=principal,
        annual_rate_percent=request.annual_rate,
        months=request.months,
    )

    return CalculationResult(
        product_type="deposit",
        product_name="예금",
        months=request.months,
        principal=principal,
        bank_interest=bank_interest,
        government_contribution=Decimal("0"),
        maturity_amount=principal + bank_interest,
        notices=["예금 계산은 입력 금액을 일시 예치 원금으로 간주합니다."],
    )

