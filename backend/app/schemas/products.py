from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field, field_serializer, field_validator

ProductType = Literal["deposit", "saving"]


def _optional_decimal(value: object) -> Decimal | None:
    if value in (None, ""):
        return None
    return Decimal(str(value))


class ProductOptionInput(BaseModel):
    saving_term_months: int = Field(..., ge=1, le=120)
    base_rate: Decimal | None = Field(None, ge=0, le=100)
    maximum_rate: Decimal | None = Field(None, ge=0, le=100)
    interest_type: str | None = None
    reserve_type: str | None = None
    minimum_amount: Decimal | None = Field(None, ge=0)
    maximum_amount: Decimal | None = Field(None, ge=0)
    notes: str | None = None

    @field_validator(
        "base_rate",
        "maximum_rate",
        "minimum_amount",
        "maximum_amount",
        mode="before",
    )
    @classmethod
    def normalize_optional_decimal(cls, value: object) -> Decimal | None:
        return _optional_decimal(value)


class ProductOptionResponse(ProductOptionInput):
    id: int

    @field_serializer("base_rate", "maximum_rate")
    def serialize_rate(self, value: Decimal | None) -> float | None:
        return float(value) if value is not None else None

    @field_serializer("minimum_amount", "maximum_amount")
    def serialize_amount(self, value: Decimal | None) -> int | None:
        return int(value) if value is not None else None


class FinancialProductResponse(BaseModel):
    id: int
    product_type: ProductType
    product_name: str
    company_id: int
    company_code: str
    company_name: str
    sector_code: str | None = None
    sector_name: str | None = None
    join_method: str | None = None
    join_member: str | None = None
    special_conditions: str | None = None
    maturity_notes: str | None = None
    product_description: str | None = None
    official_url: str | None = None
    data_source: str
    disclosure_start_date: str | None = None
    disclosure_end_date: str | None = None
    is_manual: bool = False
    last_synced_at: str | None = None
    best_rate: Decimal | None = None
    best_term_months: int | None = None
    options: list[ProductOptionResponse] = Field(default_factory=list)

    @field_serializer("best_rate")
    def serialize_best_rate(self, value: Decimal | None) -> float | None:
        return float(value) if value is not None else None


class ProductListResponse(BaseModel):
    items: list[FinancialProductResponse]
    total: int
    limit: int
    offset: int


class ProductCompareRequest(BaseModel):
    product_ids: list[int] = Field(..., min_length=2, max_length=5)


class ManualProductCreateRequest(BaseModel):
    company_name: str = Field(..., min_length=1, max_length=120)
    company_code: str | None = Field(None, max_length=80)
    sector_code: str | None = Field(None, max_length=20)
    sector_name: str | None = Field(None, max_length=80)
    product_type: ProductType
    product_name: str = Field(..., min_length=1, max_length=160)
    join_method: str | None = None
    join_member: str | None = None
    special_conditions: str | None = None
    maturity_notes: str | None = None
    product_description: str | None = None
    official_url: str | None = None
    option: ProductOptionInput


class ManualProductUpdateRequest(BaseModel):
    product_name: str | None = Field(None, min_length=1, max_length=160)
    join_method: str | None = None
    join_member: str | None = None
    special_conditions: str | None = None
    maturity_notes: str | None = None
    product_description: str | None = None
    official_url: str | None = None
    is_active: bool | None = None
    options: list[ProductOptionInput] | None = None


class CompanyResponse(BaseModel):
    id: int
    company_code: str
    company_name: str
    sector_code: str | None = None
    sector_name: str | None = None


class FinlifeSyncRequest(BaseModel):
    product_types: list[ProductType] = Field(default_factory=lambda: ["deposit", "saving"])
    sector_codes: list[str] = Field(default_factory=lambda: ["020000", "030300"])


class FinlifeSyncResponse(BaseModel):
    source: str
    status: str
    products_seen: int
    products_upserted: int
    options_upserted: int
    message: str | None = None


class SyncLogResponse(BaseModel):
    id: int
    source: str
    status: str
    product_type: str | None = None
    requested_at: str
    completed_at: str | None = None
    products_seen: int
    products_upserted: int
    options_upserted: int
    message: str | None = None
