"""FastAPI application entrypoint for the Amnezia VPN management API."""

from __future__ import annotations

import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import JSONResponse, Response

from .config import get_settings
from .routers import keys, server

BOOTSTRAP_SECRET_ENV = "AMNEZIA_API_BOOTSTRAP_SECRET"


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Create the secret file at startup when it is missing."""
    settings = get_settings()
    secret_path = Path(settings.secret_file)
    if not secret_path.exists():
        bootstrap = os.environ.get(BOOTSTRAP_SECRET_ENV, "").strip()
        if not bootstrap:
            bootstrap = os.urandom(24).hex()
            print(
                f"WARNING: Generated a new API secret. Stored at {secret_path}. "
                "Share it with clients."
            )
        secret_path.parent.mkdir(parents=True, exist_ok=True)
        secret_path.write_text(bootstrap + "\n", encoding="utf-8")
        os.chmod(secret_path, 0o600)
    yield


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
