from fastapi import APIRouter

from app.calculators.deposit import calculate_deposit
from app.calculators.saving import calculate_saving
from app.calculators.youth_future import calculate_youth_future
from app.calculators.youth_leap import calculate_youth_leap
from app.schemas.requests import (
    DepositRequest,
    SavingRequest,
    YouthFutureRequest,
    YouthLeapRequest,
)
from app.schemas.responses import CalculationResult, YouthFutureResponse

router = APIRouter(prefix="/api/calculate", tags=["calculations"])


@router.post("/deposit", response_model=CalculationResult)
def deposit(request: DepositRequest) -> CalculationResult:
    return calculate_deposit(request)


@router.post("/saving", response_model=CalculationResult)
def saving(request: SavingRequest) -> CalculationResult:
    return calculate_saving(request)


@router.post("/youth-leap", response_model=CalculationResult)
def youth_leap(request: YouthLeapRequest) -> CalculationResult:
    return calculate_youth_leap(request)


@router.post("/youth-future", response_model=YouthFutureResponse)
def youth_future(request: YouthFutureRequest) -> YouthFutureResponse:
    return calculate_youth_future(request)

