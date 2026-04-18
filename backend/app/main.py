"""ASGI entry: ``app`` is the FastAPI instance (e.g. ``uvicorn app.main:app``); CLI uses ``main()`` below."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.api import api_router
from app.config.settings import get_settings
from app.core.bootstrap import init_app, shutdown_app, verify_database_connection


def _cors_allow_origins(raw: str) -> list[str]:
    s = (raw or "").strip()
    if s == "*":
        return ["*"]
    return [x.strip() for x in s.split(",") if x.strip()]


@asynccontextmanager
async def lifespan(_app: FastAPI):
    settings = get_settings()
    if not settings.database_url:
        msg = "DATABASE_URL is required to run the HTTP API."
        raise RuntimeError(msg)
    init_app()
    verify_database_connection()
    yield
    shutdown_app()


def create_app() -> FastAPI:
    settings = get_settings()
    application = FastAPI(title=settings.app_name, debug=settings.debug, lifespan=lifespan)
    origins = _cors_allow_origins(settings.cors_allow_origins)
    if origins:
        application.add_middleware(
            CORSMiddleware,
            allow_origins=origins,
            allow_credentials=False if origins == ["*"] else True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
    application.include_router(api_router)
    return application


app = create_app()


def main() -> None:
    """CLI: run one career workflow turn (requires LLM and search keys as configured)."""
    from app.pipeline import run_turn

    out = run_turn("I'm a backend dev — should I move into AI?")
    for key in ("plan", "research", "analysis", "critique", "synthesis"):
        print(f"\n=== {key} ===\n{out.get(key)}")


if __name__ == "__main__":
    main()
