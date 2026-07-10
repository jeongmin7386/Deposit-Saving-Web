from collections import defaultdict
from decimal import Decimal, InvalidOperation
from hashlib import sha1
from typing import Any

from app.database import get_connection
from app.schemas.products import (
    CompanyResponse,
    FinancialProductResponse,
    ManualProductCreateRequest,
    ManualProductUpdateRequest,
    ProductListResponse,
    ProductOptionInput,
    ProductOptionResponse,
    ProductType,
    SyncLogResponse,
)


def _decimal_to_text(value: Decimal | None) -> str | None:
    return str(value) if value is not None else None


def _to_decimal(value: object) -> Decimal | None:
    if value in (None, ""):
        return None
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError):
        return None


def _to_int(value: object) -> int | None:
    if value in (None, ""):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _manual_company_code(company_name: str) -> str:
    digest = sha1(company_name.strip().encode("utf-8")).hexdigest()[:10]
    return f"MANUAL-{digest}"


def _sector_name(sector_code: str | None) -> str | None:
    return {
        "020000": "은행",
        "030300": "저축은행",
    }.get(sector_code or "")


def _option_from_row(row: Any) -> ProductOptionResponse:
    return ProductOptionResponse(
        id=row["id"],
        saving_term_months=row["saving_term_months"],
        base_rate=_to_decimal(row["base_rate"]),
        maximum_rate=_to_decimal(row["maximum_rate"]),
        interest_type=row["interest_type"],
        reserve_type=row["reserve_type"],
        minimum_amount=_to_decimal(row["minimum_amount"]),
        maximum_amount=_to_decimal(row["maximum_amount"]),
        notes=row["notes"],
    )


def _fetch_options(connection: Any, product_id: int) -> list[ProductOptionResponse]:
    rows = connection.execute(
        """
        SELECT *
        FROM product_options
        WHERE product_id = ?
        ORDER BY saving_term_months ASC,
                 CAST(COALESCE(maximum_rate, base_rate, '0') AS REAL) DESC
        """,
        (product_id,),
    ).fetchall()
    return [_option_from_row(row) for row in rows]


def _product_from_row(row: Any, options: list[ProductOptionResponse]) -> FinancialProductResponse:
    return FinancialProductResponse(
        id=row["id"],
        product_type=row["product_type"],
        product_name=row["product_name"],
        company_id=row["company_id"],
        company_code=row["company_code"],
        company_name=row["company_name"],
        sector_code=row["sector_code"],
        sector_name=row["sector_name"],
        join_method=row["join_method"],
        join_member=row["join_member"],
        special_conditions=row["special_conditions"],
        maturity_notes=row["maturity_notes"],
        product_description=row["product_description"],
        official_url=row["official_url"],
        data_source=row["data_source"],
        disclosure_start_date=row["disclosure_start_date"],
        disclosure_end_date=row["disclosure_end_date"],
        is_manual=bool(row["is_manual"]),
        last_synced_at=row["last_synced_at"],
        best_rate=_to_decimal(row["best_rate"]),
        best_term_months=_to_int(row["best_term_months"]),
        options=options,
    )


def _product_select_sql() -> str:
    return """
        SELECT
            p.*,
            c.company_code,
            c.company_name,
            c.sector_code,
            c.sector_name,
            (
                SELECT MAX(CAST(COALESCE(o.maximum_rate, o.base_rate, '0') AS REAL))
                FROM product_options o
                WHERE o.product_id = p.id
            ) AS best_rate,
            (
                SELECT o.saving_term_months
                FROM product_options o
                WHERE o.product_id = p.id
                ORDER BY CAST(COALESCE(o.maximum_rate, o.base_rate, '0') AS REAL) DESC,
                         o.saving_term_months ASC
                LIMIT 1
            ) AS best_term_months
        FROM financial_products p
        JOIN financial_companies c ON c.id = p.company_id
    """


def search_products(
    product_type: ProductType | None = None,
    keyword: str | None = None,
    company_name: str | None = None,
    term_months: int | None = None,
    min_rate: Decimal | None = None,
    sort: str = "rate_desc",
    limit: int = 20,
    offset: int = 0,
) -> ProductListResponse:
    conditions = ["p.is_active = 1", "c.is_active = 1"]
    params: list[Any] = []

    if product_type:
        conditions.append("p.product_type = ?")
        params.append(product_type)
    if keyword:
        conditions.append("(p.product_name LIKE ? OR c.company_name LIKE ?)")
        like = f"%{keyword.strip()}%"
        params.extend([like, like])
    if company_name:
        conditions.append("c.company_name LIKE ?")
        params.append(f"%{company_name.strip()}%")
    if term_months:
        conditions.append(
            """
            EXISTS (
                SELECT 1 FROM product_options term_o
                WHERE term_o.product_id = p.id
                  AND term_o.saving_term_months = ?
            )
            """
        )
        params.append(term_months)
    if min_rate is not None:
        conditions.append(
            """
            EXISTS (
                SELECT 1 FROM product_options rate_o
                WHERE rate_o.product_id = p.id
                  AND CAST(COALESCE(rate_o.maximum_rate, rate_o.base_rate, '0') AS REAL) >= ?
            )
            """
        )
        params.append(float(min_rate))

    where_sql = " WHERE " + " AND ".join(conditions)
    order_sql = {
        "rate_asc": " ORDER BY best_rate ASC, c.company_name ASC, p.product_name ASC",
        "name": " ORDER BY c.company_name ASC, p.product_name ASC",
        "term": " ORDER BY best_term_months ASC, best_rate DESC",
    }.get(sort, " ORDER BY best_rate DESC, c.company_name ASC, p.product_name ASC")

    with get_connection() as connection:
        total = connection.execute(
            f"""
            SELECT COUNT(DISTINCT p.id)
            FROM financial_products p
            JOIN financial_companies c ON c.id = p.company_id
            {where_sql}
            """,
            params,
        ).fetchone()[0]

        rows = connection.execute(
            f"{_product_select_sql()} {where_sql} {order_sql} LIMIT ? OFFSET ?",
            [*params, limit, offset],
        ).fetchall()

        items = [
            _product_from_row(row, _fetch_options(connection, row["id"]))
            for row in rows
        ]

    return ProductListResponse(items=items, total=total, limit=limit, offset=offset)


def get_product(product_id: int) -> FinancialProductResponse | None:
    with get_connection() as connection:
        row = connection.execute(
            f"{_product_select_sql()} WHERE p.id = ? AND p.is_active = 1",
            (product_id,),
        ).fetchone()
        if row is None:
            return None
        return _product_from_row(row, _fetch_options(connection, product_id))


def compare_products(product_ids: list[int]) -> list[FinancialProductResponse]:
    products = [get_product(product_id) for product_id in product_ids]
    return [product for product in products if product is not None]


def list_companies() -> list[CompanyResponse]:
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT id, company_code, company_name, sector_code, sector_name
            FROM financial_companies
            WHERE is_active = 1
            ORDER BY company_name ASC
            """
        ).fetchall()
    return [CompanyResponse(**dict(row)) for row in rows]


def _upsert_company(
    connection: Any,
    company_code: str,
    company_name: str,
    sector_code: str | None = None,
    sector_name: str | None = None,
) -> int:
    connection.execute(
        """
        INSERT INTO financial_companies (
            company_code, company_name, sector_code, sector_name, is_active
        )
        VALUES (?, ?, ?, ?, 1)
        ON CONFLICT(company_code) DO UPDATE SET
            company_name = excluded.company_name,
            sector_code = COALESCE(excluded.sector_code, financial_companies.sector_code),
            sector_name = COALESCE(excluded.sector_name, financial_companies.sector_name),
            is_active = 1,
            updated_at = CURRENT_TIMESTAMP
        """,
        (company_code, company_name, sector_code, sector_name),
    )
    return connection.execute(
        "SELECT id FROM financial_companies WHERE company_code = ?",
        (company_code,),
    ).fetchone()["id"]


def _upsert_product(
    connection: Any,
    *,
    company_id: int,
    external_product_code: str,
    product_type: ProductType,
    product_name: str,
    join_method: str | None = None,
    join_member: str | None = None,
    special_conditions: str | None = None,
    maturity_notes: str | None = None,
    product_description: str | None = None,
    official_url: str | None = None,
    data_source: str,
    disclosure_start_date: str | None = None,
    disclosure_end_date: str | None = None,
    is_manual: bool = False,
) -> int:
    connection.execute(
        """
        INSERT INTO financial_products (
            company_id, external_product_code, product_type, product_name,
            join_method, join_member, special_conditions, maturity_notes,
            product_description, official_url, data_source, disclosure_start_date,
            disclosure_end_date, is_active, is_manual, last_synced_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(company_id, external_product_code, product_type, product_name)
        DO UPDATE SET
            join_method = excluded.join_method,
            join_member = excluded.join_member,
            special_conditions = excluded.special_conditions,
            maturity_notes = excluded.maturity_notes,
            product_description = excluded.product_description,
            official_url = excluded.official_url,
            data_source = excluded.data_source,
            disclosure_start_date = excluded.disclosure_start_date,
            disclosure_end_date = excluded.disclosure_end_date,
            is_active = 1,
            is_manual = excluded.is_manual,
            last_synced_at = CURRENT_TIMESTAMP,
            updated_at = CURRENT_TIMESTAMP
        """,
        (
            company_id,
            external_product_code,
            product_type,
            product_name,
            join_method,
            join_member,
            special_conditions,
            maturity_notes,
            product_description,
            official_url,
            data_source,
            disclosure_start_date,
            disclosure_end_date,
            int(is_manual),
        ),
    )
    return connection.execute(
        """
        SELECT id
        FROM financial_products
        WHERE company_id = ?
          AND external_product_code = ?
          AND product_type = ?
          AND product_name = ?
        """,
        (company_id, external_product_code, product_type, product_name),
    ).fetchone()["id"]


def _replace_options(
    connection: Any,
    product_id: int,
    options: list[ProductOptionInput],
) -> int:
    connection.execute("DELETE FROM product_options WHERE product_id = ?", (product_id,))
    for option in options:
        connection.execute(
            """
            INSERT INTO product_options (
                product_id, saving_term_months, base_rate, maximum_rate,
                interest_type, reserve_type, minimum_amount, maximum_amount, notes
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                product_id,
                option.saving_term_months,
                _decimal_to_text(option.base_rate),
                _decimal_to_text(option.maximum_rate),
                option.interest_type,
                option.reserve_type,
                _decimal_to_text(option.minimum_amount),
                _decimal_to_text(option.maximum_amount),
                option.notes,
            ),
        )
    return len(options)


def create_manual_product(payload: ManualProductCreateRequest) -> FinancialProductResponse:
    company_code = payload.company_code or _manual_company_code(payload.company_name)
    external_product_code = f"manual-{sha1((company_code + payload.product_name).encode('utf-8')).hexdigest()[:16]}"
    with get_connection() as connection:
        company_id = _upsert_company(
            connection,
            company_code=company_code,
            company_name=payload.company_name,
            sector_code=payload.sector_code,
            sector_name=payload.sector_name,
        )
        product_id = _upsert_product(
            connection,
            company_id=company_id,
            external_product_code=external_product_code,
            product_type=payload.product_type,
            product_name=payload.product_name,
            join_method=payload.join_method,
            join_member=payload.join_member,
            special_conditions=payload.special_conditions,
            maturity_notes=payload.maturity_notes,
            product_description=payload.product_description,
            official_url=payload.official_url,
            data_source="manual",
            is_manual=True,
        )
        _replace_options(connection, product_id, [payload.option])

    product = get_product(product_id)
    if product is None:
        raise ValueError("등록한 상품을 다시 조회하지 못했습니다.")
    return product


def update_manual_product(
    product_id: int,
    payload: ManualProductUpdateRequest,
) -> FinancialProductResponse | None:
    with get_connection() as connection:
        existing = connection.execute(
            "SELECT id, is_manual FROM financial_products WHERE id = ?",
            (product_id,),
        ).fetchone()
        if existing is None:
            return None
        if not bool(existing["is_manual"]):
            raise ValueError("FINLIFE 동기화 상품은 관리자 화면에서 직접 수정할 수 없습니다.")

        fields = payload.model_dump(exclude_unset=True, exclude={"options"})
        if fields:
            assignments = []
            values = []
            for key, value in fields.items():
                assignments.append(f"{key} = ?")
                values.append(int(value) if key == "is_active" else value)
            assignments.append("updated_at = CURRENT_TIMESTAMP")
            connection.execute(
                f"UPDATE financial_products SET {', '.join(assignments)} WHERE id = ?",
                [*values, product_id],
            )
        if payload.options is not None:
            _replace_options(connection, product_id, payload.options)

    return get_product(product_id)


def deactivate_product(product_id: int) -> bool:
    with get_connection() as connection:
        cursor = connection.execute(
            """
            UPDATE financial_products
            SET is_active = 0, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (product_id,),
        )
    return cursor.rowcount > 0


def upsert_finlife_batch(
    product_type: ProductType,
    sector_code: str,
    base_list: list[dict[str, Any]],
    option_list: list[dict[str, Any]],
) -> tuple[int, int, int]:
    options_by_product: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for option in option_list:
        key = (str(option.get("fin_co_no", "")), str(option.get("fin_prdt_cd", "")))
        options_by_product[key].append(option)

    products_seen = 0
    products_upserted = 0
    options_upserted = 0

    with get_connection() as connection:
        for base in base_list:
            company_code = str(base.get("fin_co_no") or "").strip()
            product_code = str(base.get("fin_prdt_cd") or "").strip()
            company_name = str(base.get("kor_co_nm") or "").strip()
            product_name = str(base.get("fin_prdt_nm") or "").strip()
            if not company_code or not product_code or not company_name or not product_name:
                continue

            products_seen += 1
            company_id = _upsert_company(
                connection,
                company_code=company_code,
                company_name=company_name,
                sector_code=sector_code,
                sector_name=_sector_name(sector_code),
            )
            product_id = _upsert_product(
                connection,
                company_id=company_id,
                external_product_code=product_code,
                product_type=product_type,
                product_name=product_name,
                join_method=base.get("join_way"),
                join_member=base.get("join_member"),
                special_conditions=base.get("spcl_cnd"),
                maturity_notes=base.get("etc_note"),
                product_description=base.get("mtrt_int"),
                data_source="finlife",
                disclosure_start_date=base.get("dcls_strt_day"),
                disclosure_end_date=base.get("dcls_end_day"),
                is_manual=False,
            )

            parsed_options: list[ProductOptionInput] = []
            for raw_option in options_by_product[(company_code, product_code)]:
                term = _to_int(raw_option.get("save_trm"))
                if term is None:
                    continue
                parsed_options.append(
                    ProductOptionInput(
                        saving_term_months=term,
                        base_rate=_to_decimal(raw_option.get("intr_rate")),
                        maximum_rate=_to_decimal(raw_option.get("intr_rate2")),
                        interest_type=raw_option.get("intr_rate_type_nm")
                        or raw_option.get("intr_rate_type"),
                        reserve_type=raw_option.get("rsrv_type_nm")
                        or raw_option.get("rsrv_type"),
                        notes=raw_option.get("etc_note"),
                    )
                )
            options_upserted += _replace_options(connection, product_id, parsed_options)
            products_upserted += 1

    return products_seen, products_upserted, options_upserted


def start_sync_log(source: str, product_type: str | None = None) -> int:
    with get_connection() as connection:
        cursor = connection.execute(
            """
            INSERT INTO sync_logs (source, status, product_type)
            VALUES (?, 'running', ?)
            """,
            (source, product_type),
        )
        return int(cursor.lastrowid)


def finish_sync_log(
    log_id: int,
    *,
    status: str,
    products_seen: int = 0,
    products_upserted: int = 0,
    options_upserted: int = 0,
    message: str | None = None,
) -> None:
    with get_connection() as connection:
        connection.execute(
            """
            UPDATE sync_logs
            SET status = ?,
                completed_at = CURRENT_TIMESTAMP,
                products_seen = ?,
                products_upserted = ?,
                options_upserted = ?,
                message = ?
            WHERE id = ?
            """,
            (
                status,
                products_seen,
                products_upserted,
                options_upserted,
                message,
                log_id,
            ),
        )


def list_sync_logs(limit: int = 20) -> list[SyncLogResponse]:
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT *
            FROM sync_logs
            ORDER BY requested_at DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
    return [SyncLogResponse(**dict(row)) for row in rows]
