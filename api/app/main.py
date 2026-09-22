"""FastAPI application entrypoint for the Amnezia VPN management API."""

from __future__ import annotations

import logging
import os
import time
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, Response

from .config import get_settings
from .logging_setup import api_logger, configure_logging, normalize_level
from .routers import keys, server

BOOTSTRAP_SECRET_ENV = "AMNEZIA_API_BOOTSTRAP_SECRET"


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Configure logging and create the secret file at startup."""
    settings = get_settings()
    configure_logging(
        level=normalize_level(settings.log_level),
        log_file=settings.log_file or None,
    )
    api_logger.info("Amnezia VPN management API starting")

    secret_path = Path(settings.secret_file)
    if not secret_path.exists():
        bootstrap = os.environ.get(BOOTSTRAP_SECRET_ENV, "").strip()
        if not bootstrap:
            bootstrap = os.urandom(24).hex()
            api_logger.warning(
                "No API secret file found; generated a new one at %s. "
                "Share it with clients.",
                secret_path,
            )
        secret_path.parent.mkdir(parents=True, exist_ok=True)
        secret_path.write_text(bootstrap + "\n", encoding="utf-8")
        os.chmod(secret_path, 0o600)
    else:
        api_logger.info("API secret file found at %s", secret_path)

    yield
    api_logger.info("Amnezia VPN management API shutting down")


app = FastAPI(
    title="Amnezia VPN Management API",
    version="1.0.0",
    description=(
        "HTTP API to manage Amnezia VPN on a host: generate/download/delete "
        "keys and check/restart the server. All requests require an "
        "X-API-Secret header."
    ),
    lifespan=lifespan,
)


@app.middleware("http")
async def request_logging_middleware(request: Request, call_next):
    """Log every request with its method, path, outcome and duration.

    The value of the ``X-API-Secret`` header is intentionally **not** logged;
    only whether a secret was provided is recorded.
    """
    secret_header = request.headers.get("X-API-Secret")
    auth_present = bool(secret_header)
    start = time.perf_counter()

    response = await call_next(request)

    duration_ms = (time.perf_counter() - start) * 1000
    access_logger = logging.getLogger("amnezia.access")
    access_logger.info(
        "method=%s path=%s status=%s duration_ms=%.1f auth=%s client=%s",
        request.method,
        request.url.path,
        response.status_code,
        duration_ms,
        auth_present,
        request.client.host if request.client else "-",
    )
    return response


@app.get("/health", tags=["system"], include_in_schema=False)
def health() -> Response:
    """Liveness probe used by the deploy script."""
    return Response(status_code=200, content=b"ok")


@app.exception_handler(404)
def not_found_handler(_request, _exc):
    """Return a JSON body for missing endpoints."""
    return JSONResponse(status_code=404, content={"detail": "Not found."})


app.include_router(keys.router)
app.include_router(server.router)
