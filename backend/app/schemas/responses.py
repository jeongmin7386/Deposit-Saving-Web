from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_serializer


class CalculationResult(BaseModel):
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "product_type": "youth-future-general",
            "product_name": "청년미래적금 일반형",
            "months": 36,
            "principal": 18000000,
            "bank_interest": 1387500,
            "government_contribution": 1080000,
            "maturity_amount": 20467500,
            "notices": [
                "청년미래적금은 36개월, 월 최대 500,000원 납입 기준입니다."
            ],
        }
    })

    product_type: str
    product_name: str
    months: int
    principal: Decimal
    bank_interest: Decimal
    government_contribution: Decimal
    maturity_amount: Decimal
    notices: list[str] = Field(default_factory=list)

    @field_serializer(
        "principal",
        "bank_interest",
        "government_contribution",
        "maturity_amount",
    )
    def serialize_krw(self, value: Decimal) -> int:
        return int(value)


class YouthFutureResponse(CalculationResult):
    comparison: list[CalculationResult]
