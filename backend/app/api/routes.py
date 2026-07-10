from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Response, status

from app.calculators.deposit import calculate_deposit
from app.calculators.saving import calculate_saving
from app.calculators.youth_future import calculate_youth_future
from app.calculators.youth_leap import calculate_youth_leap
from app.repositories.products import (
    compare_products,
    create_manual_product,
    deactivate_product,
    get_product,
    list_companies,
    list_sync_logs,
    search_products,
    update_manual_product,
)
from app.schemas.products import (
    CompanyResponse,
    FinancialProductResponse,
    FinlifeSyncRequest,
    FinlifeSyncResponse,
    ManualProductCreateRequest,
    ManualProductUpdateRequest,
    ProductCompareRequest,
    ProductListResponse,
    ProductType,
    SyncLogResponse,
)
from app.schemas.requests import (
    DepositRequest,
    SavingRequest,
    YouthFutureRequest,
    YouthLeapRequest,
)
from app.schemas.responses import CalculationResult, YouthFutureResponse
from app.services.finlife_client import FinlifeConfigurationError
from app.services.product_sync import sync_finlife_products
from app.settings import get_settings

router = APIRouter()
calculation_router = APIRouter(prefix="/api/calculate", tags=["calculations"])
product_router = APIRouter(prefix="/api", tags=["financial products"])


def require_admin_token(
    x_admin_token: Annotated[str | None, Header(alias="X-Admin-Token")] = None,
) -> None:
    admin_token = get_settings().admin_token
    if admin_token and x_admin_token != admin_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="관리자 토큰이 올바르지 않습니다.",
        )


@calculation_router.post("/deposit", response_model=CalculationResult)
def deposit(request: DepositRequest) -> CalculationResult:
    return calculate_deposit(request)


@calculation_router.post("/saving", response_model=CalculationResult)
def saving(request: SavingRequest) -> CalculationResult:
    return calculate_saving(request)


@calculation_router.post("/youth-leap", response_model=CalculationResult)
def youth_leap(request: YouthLeapRequest) -> CalculationResult:
    return calculate_youth_leap(request)


@calculation_router.post("/youth-future", response_model=YouthFutureResponse)
def youth_future(request: YouthFutureRequest) -> YouthFutureResponse:
    return calculate_youth_future(request)


@product_router.get("/products", response_model=ProductListResponse)
def products(
    product_type: ProductType | None = None,
    keyword: str | None = None,
    company_name: str | None = None,
    term_months: int | None = Query(None, ge=1, le=120),
    min_rate: Decimal | None = Query(None, ge=0, le=100),
    sort: str = Query("rate_desc", pattern="^(rate_desc|rate_asc|name|term)$"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
) -> ProductListResponse:
    return search_products(
        product_type=product_type,
        keyword=keyword,
        company_name=company_name,
        term_months=term_months,
        min_rate=min_rate,
        sort=sort,
        limit=limit,
        offset=offset,
    )


@product_router.get("/companies", response_model=list[CompanyResponse])
def companies() -> list[CompanyResponse]:
    return list_companies()


@product_router.post("/products/compare", response_model=list[FinancialProductResponse])
def compare(payload: ProductCompareRequest) -> list[FinancialProductResponse]:
    products_to_compare = compare_products(payload.product_ids)
    if len(products_to_compare) < 2:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="비교할 상품을 2개 이상 찾지 못했습니다.",
        )
    return products_to_compare


@product_router.get("/products/{product_id}", response_model=FinancialProductResponse)
def product_detail(product_id: int) -> FinancialProductResponse:
    product = get_product(product_id)
    if product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="상품을 찾을 수 없습니다.",
        )
    return product


@product_router.post(
    "/admin/products",
    response_model=FinancialProductResponse,
    dependencies=[Depends(require_admin_token)],
)
def admin_create_product(payload: ManualProductCreateRequest) -> FinancialProductResponse:
    return create_manual_product(payload)


@product_router.patch(
    "/admin/products/{product_id}",
    response_model=FinancialProductResponse,
    dependencies=[Depends(require_admin_token)],
)
def admin_update_product(
    product_id: int,
    payload: ManualProductUpdateRequest,
) -> FinancialProductResponse:
    try:
        product = update_manual_product(product_id, payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    if product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="상품을 찾을 수 없습니다.",
        )
    return product


@product_router.delete(
    "/admin/products/{product_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_admin_token)],
)
def admin_delete_product(product_id: int) -> Response:
    if not deactivate_product(product_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="상품을 찾을 수 없습니다.",
        )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@product_router.post(
    "/admin/sync/finlife",
    response_model=FinlifeSyncResponse,
    dependencies=[Depends(require_admin_token)],
)
def admin_sync_finlife(payload: FinlifeSyncRequest) -> FinlifeSyncResponse:
    try:
        return sync_finlife_products(payload)
    except FinlifeConfigurationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"FINLIFE 동기화를 완료하지 못했습니다: {exc}",
        ) from exc


@product_router.get(
    "/admin/sync/logs",
    response_model=list[SyncLogResponse],
    dependencies=[Depends(require_admin_token)],
)
def admin_sync_logs(limit: int = Query(20, ge=1, le=100)) -> list[SyncLogResponse]:
    return list_sync_logs(limit=limit)


router.include_router(calculation_router)
router.include_router(product_router)
