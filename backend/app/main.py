"""Application entry: FastAPI ASGI `app` and CLI pipeline when run as a script."""

from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.api import api_router
from app.config.settings import get_settings
from app.core.bootstrap import init_app, shutdown_app, verify_database_connection


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
    application.include_router(api_router)
    return application


app = create_app()



if __name__ == "__main__":
    main()
