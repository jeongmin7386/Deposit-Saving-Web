import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router
from app.database import init_db
from app.schemas.products import FinlifeSyncRequest
from app.services.product_sync import sync_finlife_products
from app.settings import get_settings


def _allowed_origins() -> list[str]:
    configured_origins = [
        origin.strip()
        for origin in os.getenv("ALLOWED_ORIGINS", "").split(",")
        if origin.strip()
    ]
    return [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        *configured_origins,
    ]


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    if get_settings().sync_on_startup:
        try:
            sync_finlife_products(FinlifeSyncRequest())
        except Exception:
            pass
    yield


app = FastAPI(
    title="Deposit Savings Calculator API",
    version="1.0.0",
    description="Deposit, saving, youth leap, youth future, and financial product comparison API",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins(),
    allow_origin_regex=os.getenv(
        "ALLOWED_ORIGIN_REGEX",
        r"https://.*\.onrender\.com",
    ),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


@app.get("/")
def root() -> dict[str, str]:
    return {
        "service": "Deposit Savings Calculator API",
        "status": "ok",
        "docs": "/docs",
        "health": "/health",
    }


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
