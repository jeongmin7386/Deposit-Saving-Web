from app.repositories.products import (
    finish_sync_log,
    start_sync_log,
    upsert_finlife_batch,
)
from app.schemas.products import FinlifeSyncRequest, FinlifeSyncResponse
from app.services.finlife_client import FinlifeClient


def sync_finlife_products(payload: FinlifeSyncRequest) -> FinlifeSyncResponse:
    log_id = start_sync_log("finlife", ",".join(payload.product_types))
    products_seen = 0
    products_upserted = 0
    options_upserted = 0

    try:
        client = FinlifeClient()
        for product_type in payload.product_types:
            for sector_code in payload.sector_codes:
                base_list, option_list = client.fetch_products(product_type, sector_code)
                seen, upserted, options = upsert_finlife_batch(
                    product_type=product_type,
                    sector_code=sector_code,
                    base_list=base_list,
                    option_list=option_list,
                )
                products_seen += seen
                products_upserted += upserted
                options_upserted += options

        finish_sync_log(
            log_id,
            status="success",
            products_seen=products_seen,
            products_upserted=products_upserted,
            options_upserted=options_upserted,
            message="FINLIFE 동기화를 완료했습니다.",
        )
        return FinlifeSyncResponse(
            source="finlife",
            status="success",
            products_seen=products_seen,
            products_upserted=products_upserted,
            options_upserted=options_upserted,
            message="FINLIFE 동기화를 완료했습니다.",
        )
    except Exception as exc:
        finish_sync_log(
            log_id,
            status="failed",
            products_seen=products_seen,
            products_upserted=products_upserted,
            options_upserted=options_upserted,
            message=str(exc),
        )
        raise
