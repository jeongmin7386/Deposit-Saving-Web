from decimal import Decimal

import pytest

from app.database import init_db
from app.repositories.products import (
    compare_products,
    create_manual_product,
    search_products,
    upsert_finlife_batch,
)
from app.schemas.products import ManualProductCreateRequest, ProductOptionInput
from app.settings import get_settings


@pytest.fixture
def product_db(tmp_path, monkeypatch):
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path / 'products.db'}")
    get_settings.cache_clear()
    init_db()
    yield
    get_settings.cache_clear()


def test_manual_product_can_be_searched_and_compared(product_db) -> None:
    created = create_manual_product(
        ManualProductCreateRequest(
            company_name="테스트은행",
            product_type="deposit",
            product_name="테스트 정기예금",
            join_method="인터넷",
            option=ProductOptionInput(
                saving_term_months=12,
                base_rate=Decimal("3.8"),
                maximum_rate=Decimal("4.2"),
            ),
        )
    )

    result = search_products(
        product_type="deposit",
        keyword="테스트",
        term_months=12,
        min_rate=Decimal("4.0"),
    )
    compared = compare_products([created.id, created.id])

    assert result.total == 1
    assert result.items[0].company_name == "테스트은행"
    assert result.items[0].best_rate == Decimal("4.2")
    assert compared[0].product_name == "테스트 정기예금"


def test_finlife_batch_upsert_stores_product_options(product_db) -> None:
    seen, products, options = upsert_finlife_batch(
        product_type="saving",
        sector_code="020000",
        base_list=[
            {
                "fin_co_no": "0010001",
                "kor_co_nm": "샘플은행",
                "fin_prdt_cd": "SAVING-001",
                "fin_prdt_nm": "샘플 자유적금",
                "join_way": "스마트폰",
                "spcl_cnd": "급여이체 우대",
            }
        ],
        option_list=[
            {
                "fin_co_no": "0010001",
                "fin_prdt_cd": "SAVING-001",
                "save_trm": "12",
                "intr_rate": "3.5",
                "intr_rate2": "4.1",
                "intr_rate_type_nm": "단리",
                "rsrv_type_nm": "자유적립식",
            }
        ],
    )

    result = search_products(product_type="saving", keyword="샘플")

    assert seen == 1
    assert products == 1
    assert options == 1
    assert result.total == 1
    assert result.items[0].data_source == "finlife"
    assert result.items[0].options[0].reserve_type == "자유적립식"
