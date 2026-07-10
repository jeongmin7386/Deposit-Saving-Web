from typing import Any

import httpx

from app.schemas.products import ProductType
from app.settings import get_settings


class FinlifeConfigurationError(RuntimeError):
    pass


class FinlifeClient:
    base_url = "https://finlife.fss.or.kr/finlifeapi"
    endpoints: dict[ProductType, str] = {
        "deposit": "depositProductsSearch.json",
        "saving": "savingProductsSearch.json",
    }

    def __init__(self) -> None:
        api_key = get_settings().finlife_api_key
        if not api_key:
            raise FinlifeConfigurationError("FINLIFE_API_KEY 환경변수가 설정되어 있지 않습니다.")
        self.api_key = api_key

    def fetch_products(
        self,
        product_type: ProductType,
        sector_code: str,
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        endpoint = self.endpoints[product_type]
        base_list: list[dict[str, Any]] = []
        option_list: list[dict[str, Any]] = []
        page_no = 1
        max_page = 1

        with httpx.Client(timeout=20) as client:
            while page_no <= max_page:
                response = client.get(
                    f"{self.base_url}/{endpoint}",
                    params={
                        "auth": self.api_key,
                        "topFinGrpNo": sector_code,
                        "pageNo": page_no,
                    },
                )
                response.raise_for_status()
                payload = response.json()
                result = payload.get("result", payload)
                error_code = str(result.get("err_cd", "000"))
                if error_code not in {"000", "0", ""}:
                    raise RuntimeError(result.get("err_msg") or "FINLIFE API 오류가 발생했습니다.")

                base_list.extend(result.get("baseList") or [])
                option_list.extend(result.get("optionList") or [])
                max_page = int(result.get("max_page_no") or result.get("maxPageNo") or 1)
                page_no += 1

        return base_list, option_list
