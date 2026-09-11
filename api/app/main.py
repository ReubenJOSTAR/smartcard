"""FastAPI app factory — CORS, global exception handlers, router registration."""

import logging

from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.config import settings
from app.routers import account, auth, config, history, products, receipts, sessions, stores

# Uvicorn configures its own "uvicorn"/"uvicorn.access" loggers but leaves the root
# logger unconfigured, so app-level `logging.getLogger(__name__).info(...)` calls
# (e.g. the dev-mock OTP log) would otherwise be silently dropped instead of reaching
# the console.
logging.basicConfig(level=logging.INFO if settings.ENVIRONMENT == "development" else logging.WARNING)


def create_app() -> FastAPI:
    app = FastAPI(title="SmartCart API")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Registered on Starlette's HTTPException (not fastapi.HTTPException) so this also
    # catches framework-raised errors (404, 405) that Starlette's router raises directly —
    # a handler registered on the fastapi subclass would miss those.
    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        detail = exc.detail
        if isinstance(detail, dict) and "code" in detail:
            body = detail
        else:
            body = {"code": "HTTP_ERROR", "message": str(detail), "details": {}}
        return JSONResponse(status_code=exc.status_code, content={"error": body})

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
        return JSONResponse(
            status_code=422,
            content={
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Invalid request",
                    "details": {"errors": jsonable_encoder(exc.errors())},
                }
            },
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        return JSONResponse(
            status_code=500,
            content={"error": {"code": "INTERNAL_ERROR", "message": "Something went wrong", "details": {}}},
        )

    app.include_router(auth.router)
    app.include_router(config.router)
    app.include_router(products.router)
    app.include_router(sessions.router)
    app.include_router(history.router)
    app.include_router(receipts.router)
    app.include_router(account.router)
    app.include_router(stores.router)

    return app


app = create_app()
