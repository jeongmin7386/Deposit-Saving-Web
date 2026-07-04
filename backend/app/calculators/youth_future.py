from decimal import Decimal

from app.calculators.common import installment_interest, round_krw
from app.calculators.constants import (
    YOUTH_FUTURE_MATCHING_RATES,
    YOUTH_FUTURE_MONTHS,
    YOUTH_FUTURE_NAMES,
)
from app.schemas.requests import YouthFutureRequest
from app.schemas.responses import CalculationResult, YouthFutureResponse


def _calculate_result(request: YouthFutureRequest, benefit_type: str) -> CalculationResult:
    matching_rate = YOUTH_FUTURE_MATCHING_RATES[benefit_type]
    principal = request.monthly_amount * Decimal(YOUTH_FUTURE_MONTHS)
    bank_interest = installment_interest(
        monthly_amount=request.monthly_amount,
        annual_rate_percent=request.annual_rate,
        months=YOUTH_FUTURE_MONTHS,
        tax_free=True,
    )
    government_contribution = round_krw(principal * matching_rate)

    return CalculationResult(
        product_type=f"youth-future-{benefit_type}",
        product_name=YOUTH_FUTURE_NAMES[benefit_type],
        months=YOUTH_FUTURE_MONTHS,
        principal=principal,
        bank_interest=bank_interest,
        government_contribution=government_contribution,
        maturity_amount=principal + bank_interest + government_contribution,
        notices=[
            "청년미래적금은 36개월, 월 최대 500,000원 납입 기준입니다.",
            "정부기여금은 원금 기준으로 별도 계산되며 이자소득은 비과세로 처리했습니다.",
        ],
    )


def calculate_youth_future(request: YouthFutureRequest) -> YouthFutureResponse:
    selected = _calculate_result(request, request.benefit_type)
    comparison = [
        _calculate_result(request, "general"),
        _calculate_result(request, "preferred"),
    ]
    response_data = selected.model_dump()
    response_data["notices"] = [
        *selected.notices,
        "중소기업 우대형 요건을 충족하지 못하면 일반형 혜택으로 지급될 수 있습니다.",
        "실제 가입 가능 여부는 금융기관 심사 기준에 따라 달라질 수 있습니다.",
    ]

    return YouthFutureResponse(
        **response_data,
        comparison=comparison,
    )
