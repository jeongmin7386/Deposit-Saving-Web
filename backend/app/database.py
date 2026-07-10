import sqlite3
from pathlib import Path

from app.settings import get_settings


def _database_path() -> Path:
    database_url = get_settings().database_url
    if database_url.startswith("sqlite:///"):
        return Path(database_url.removeprefix("sqlite:///")).resolve()
    if database_url.startswith("sqlite://"):
        return Path(database_url.removeprefix("sqlite://")).resolve()
    return Path(database_url).resolve()


def get_connection() -> sqlite3.Connection:
    path = _database_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def init_db() -> None:
    with get_connection() as connection:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS financial_companies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                company_code TEXT NOT NULL UNIQUE,
                company_name TEXT NOT NULL,
                sector_code TEXT,
                sector_name TEXT,
                homepage_url TEXT,
                is_active INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS financial_products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                company_id INTEGER NOT NULL REFERENCES financial_companies(id),
                external_product_code TEXT,
                product_type TEXT NOT NULL CHECK(product_type IN ('deposit', 'saving')),
                product_name TEXT NOT NULL,
                join_method TEXT,
                join_member TEXT,
                special_conditions TEXT,
                maturity_notes TEXT,
                product_description TEXT,
                official_url TEXT,
                data_source TEXT NOT NULL DEFAULT 'manual',
                disclosure_start_date TEXT,
                disclosure_end_date TEXT,
                is_active INTEGER NOT NULL DEFAULT 1,
                is_manual INTEGER NOT NULL DEFAULT 0,
                last_synced_at TEXT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(company_id, external_product_code, product_type, product_name)
            );

            CREATE INDEX IF NOT EXISTS idx_financial_products_type
                ON financial_products(product_type, is_active);
            CREATE INDEX IF NOT EXISTS idx_financial_products_name
                ON financial_products(product_name);

            CREATE TABLE IF NOT EXISTS product_options (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id INTEGER NOT NULL REFERENCES financial_products(id) ON DELETE CASCADE,
                saving_term_months INTEGER NOT NULL,
                base_rate TEXT,
                maximum_rate TEXT,
                interest_type TEXT,
                reserve_type TEXT,
                minimum_amount TEXT,
                maximum_amount TEXT,
                notes TEXT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(product_id, saving_term_months, interest_type, reserve_type)
            );

            CREATE INDEX IF NOT EXISTS idx_product_options_term
                ON product_options(saving_term_months);

            CREATE TABLE IF NOT EXISTS sync_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source TEXT NOT NULL,
                status TEXT NOT NULL,
                product_type TEXT,
                requested_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                completed_at TEXT,
                products_seen INTEGER NOT NULL DEFAULT 0,
                products_upserted INTEGER NOT NULL DEFAULT 0,
                options_upserted INTEGER NOT NULL DEFAULT 0,
                message TEXT
            );
            """
        )
