import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router


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


app = FastAPI(
    title="Deposit Savings Calculator API",
    version="1.0.0",
    description="Deposit, saving, youth leap, and youth future calculator API",
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


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}

