"""Endpoints for managing the Amnezia server itself."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import Response

from ..config import get_settings
from ..deps import require_secret
from ..logging_setup import api_logger
from ..runner import ScriptError, run_manage
from ..schemas import ErrorResponse

router = APIRouter(
    prefix="/server", tags=["server"], dependencies=[Depends(require_secret)]
)


def _run_server_command(script: str, command: str) -> Response:
    """Run a server-level management command and map the result to HTTP."""
    try:
        run_manage(script, command)
    except ScriptError as exc:
        api_logger.error("Server command %r failed: %s", command, exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"{command} failed: {exc}",
        ) from exc
    api_logger.info("Server command %r completed successfully", command)
    return Response(status_code=status.HTTP_200_OK, content=b"")


@router.post(
    "/check",
    status_code=status.HTTP_200_OK,
    summary="Run service health check",
    description="Runs the management script 'check' command. Returns an empty "
    "200 on success, otherwise an error DTO.",
    responses={502: {"model": ErrorResponse}},
)
def server_check() -> Response:
    """Check the health of the Amnezia server."""
    settings = get_settings()
    return _run_server_command(settings.manage_script, "check")


@router.post(
    "/restart",
    status_code=status.HTTP_200_OK,
    summary="Restart the service",
    description="Runs the management script 'restart' command. Returns an "
    "empty 200 on success, otherwise an error DTO.",
    responses={502: {"model": ErrorResponse}},
)
def server_restart() -> Response:
    """Restart the Amnezia server."""
    settings = get_settings()
    return _run_server_command(settings.manage_script, "restart")
