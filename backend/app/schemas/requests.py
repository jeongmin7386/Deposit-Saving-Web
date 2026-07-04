from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field, field_validator

from app.calculators.constants import (
    YOUTH_FUTURE_MAX_MONTHLY_AMOUNT,
    YOUTH_LEAP_MAX_MONTHLY_AMOUNT,
)


class BaseCalculationRequest(BaseModel):
    monthly_amount: Decimal = Field(..., gt=0, description="납입 또는 예치 금액")
    annual_rate: Decimal = Field(..., ge=0, le=100, description="연 금리(%)")

    @field_validator("monthly_amount", "annual_rate", mode="before")
    @classmethod
    def normalize_decimal(cls, value: object) -> Decimal:
        return Decimal(str(value))


class DepositRequest(BaseCalculationRequest):
    months: int = Field(12, ge=1, le=120, description="예치 개월 수")


class SavingRequest(BaseCalculationRequest):
    months: int = Field(12, ge=1, le=120, description="납입 개월 수")


class YouthLeapRequest(BaseCalculationRequest):
    annual_income: Decimal | None = Field(
        None,
        ge=0,
        description="개인 연소득. 미입력 시 정부기여금은 0원으로 계산합니다.",
    )

    @field_validator("monthly_amount")
    @classmethod
    def validate_monthly_limit(cls, value: Decimal) -> Decimal:
        if value > YOUTH_LEAP_MAX_MONTHLY_AMOUNT:
            raise ValueError("청년도약계좌 월 납입액은 700,000원을 초과할 수 없습니다.")
        return value

    @field_validator("annual_income", mode="before")
    @classmethod
    def normalize_optional_decimal(cls, value: object) -> Decimal | None:
        if value in (None, ""):
            return None
        return Decimal(str(value))


class YouthFutureRequest(BaseCalculationRequest):
    benefit_type: Literal["general", "preferred"] = Field(
        "general",
        description="일반형 또는 우대형",
    )

    @field_validator("monthly_amount")
    @classmethod
    def validate_monthly_limit(cls, value: Decimal) -> Decimal:
        if value > YOUTH_FUTURE_MAX_MONTHLY_AMOUNT:
            raise ValueError("청년미래적금 월 납입액은 500,000원을 초과할 수 없습니다.")
        return value
