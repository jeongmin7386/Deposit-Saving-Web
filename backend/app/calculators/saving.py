from decimal import Decimal

from app.calculators.common import installment_interest
from app.schemas.requests import SavingRequest
from app.schemas.responses import CalculationResult


def calculate_saving(request: SavingRequest) -> CalculationResult:
    principal = request.monthly_amount * Decimal(request.months)
    bank_interest = installment_interest(
        monthly_amount=request.monthly_amount,
        annual_rate_percent=request.annual_rate,
        months=request.months,
    )

    return CalculationResult(
        product_type="saving",
        product_name="적금",
        months=request.months,
        principal=principal,
        bank_interest=bank_interest,
        government_contribution=Decimal("0"),
        maturity_amount=principal + bank_interest,
        notices=["적금 이자는 매월 같은 금액을 납입하는 정액 적립식 기준입니다."],
    )

