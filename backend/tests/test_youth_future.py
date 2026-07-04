from decimal import Decimal

import pytest
from pydantic import ValidationError

from app.calculators.youth_future import calculate_youth_future
from app.schemas.requests import YouthFutureRequest


def test_youth_future_general_calculation() -> None:
    request = YouthFutureRequest(
        monthly_amount=Decimal("500000"),
        annual_rate=Decimal("5"),
        benefit_type="general",
    )

    result = calculate_youth_future(request)

    assert result.months == 36
    assert result.principal == Decimal("18000000")
    assert result.bank_interest == Decimal("1387500")
    assert result.government_contribution == Decimal("1080000")
    assert result.maturity_amount == Decimal("20467500")


def test_youth_future_preferred_calculation() -> None:
    request = YouthFutureRequest(
        monthly_amount=Decimal("500000"),
        annual_rate=Decimal("5"),
        benefit_type="preferred",
    )

    result = calculate_youth_future(request)

    assert result.months == 36
    assert result.principal == Decimal("18000000")
    assert result.bank_interest == Decimal("1387500")
    assert result.government_contribution == Decimal("2160000")
    assert result.maturity_amount == Decimal("21547500")


def test_youth_future_rejects_monthly_amount_above_limit() -> None:
    with pytest.raises(ValidationError):
        YouthFutureRequest(
            monthly_amount=Decimal("500001"),
            annual_rate=Decimal("5"),
            benefit_type="general",
        )


def test_youth_future_government_contribution_difference() -> None:
    base_payload = {
        "monthly_amount": Decimal("500000"),
        "annual_rate": Decimal("5"),
    }
    general = calculate_youth_future(
        YouthFutureRequest(**base_payload, benefit_type="general")
    )
    preferred = calculate_youth_future(
        YouthFutureRequest(**base_payload, benefit_type="preferred")
    )

    assert preferred.government_contribution - general.government_contribution == Decimal(
        "1080000"
    )

