"""Endpoints for managing VPN keys (peers)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import Response

from ..config import get_settings
from ..deps import require_secret
from ..files import resolve_key_file, validate_key_name
from ..logging_setup import api_logger
from ..runner import ScriptError, run_manage
from ..schemas import KeyDeleted, KeyGenerated, StatsResponse
from ..stats import parse_stats

router = APIRouter(prefix="/keys", tags=["keys"],
                   dependencies=[Depends(require_secret)])


def _mime_type(extension: str) -> str:
    """Return the media type for a given file extension."""
    if extension == "conf":
        return "text/plain; charset=utf-8"
    if extension == "png":
        return "image/png"
    if extension == "vpnuri":
        return "text/plain; charset=utf-8"
    return "application/octet-stream"


@router.post(
    "",
    response_model=KeyGenerated,
    status_code=status.HTTP_201_CREATED,
    summary="Generate a new key",
    description="Runs the management script 'add' command to create a key.",
)
def generate_key(
    name: str = Query(..., description="Name of the key to generate."),
) -> KeyGenerated:
    """Generate a new VPN key with the given name.

    The pair value ``name`` is passed to the management script as the
    ``add`` argument.
    """
    try:
        safe_name = validate_key_name(name)
    except ValueError as exc:
        api_logger.warning("Rejected generate request, invalid key name: %s", exc)
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    settings = get_settings()
    try:
        run_manage(settings.manage_script, "add", safe_name)
    except ScriptError as exc:
        api_logger.error("Failed to generate key %r: %s", safe_name, exc)
        raise HTTPException(status_code=502, detail=f"add failed: {exc}") from exc

    api_logger.info("Generated key %r", safe_name)
    return KeyGenerated(name=safe_name, message="Key generated successfully.")


@router.get(
    "/{key_name}",
    summary="Download a key file",
    description=(
        "Returns the content of a key file. Supported extensions: "
        ".conf, .png, .vpnuri."
    ),
    responses={200: {"content": {}}},
)
def get_key(
    key_name: str,
    ext: str = Query("conf", alias="ext",
                     description="File extension: conf, png or vpnuri."),
) -> Response:
    """Download the content of a key file from disk.

    Only the configured extensions are served and path traversal is
    explicitly rejected.
    """
    settings = get_settings()
    try:
        safe_name = validate_key_name(key_name)
    except ValueError as exc:
        api_logger.warning("Rejected download request, invalid key name: %s", exc)
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    try:
        path = resolve_key_file(settings.awg_path, safe_name, ext)
    except ValueError as exc:
        api_logger.warning("Rejected download request for %r: %s", safe_name, exc)
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except FileNotFoundError as exc:
        api_logger.info("Key file not found for %r (%s)", safe_name, ext)
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    data = path.read_bytes()
    api_logger.info("Downloaded key file %r (%s, %d bytes)", safe_name, ext, len(data))
    return Response(
        content=data,
        media_type=_mime_type(path.suffix.lstrip(".")),
        headers={"Content-Disposition": f'attachment; filename="{path.name}"'},
    )


@router.delete(
    "/{key_name}",
    response_model=KeyDeleted,
    summary="Delete a key",
    description="Runs the management script 'remove' command.",
)
def delete_key(key_name: str) -> KeyDeleted:
    """Delete the VPN key with the given name."""
    try:
        safe_name = validate_key_name(key_name)
    except ValueError as exc:
        api_logger.warning("Rejected delete request, invalid key name: %s", exc)
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    settings = get_settings()
    try:
        run_manage(settings.manage_script, "remove", safe_name)
    except ScriptError as exc:
        api_logger.error("Failed to delete key %r: %s", safe_name, exc)
        raise HTTPException(status_code=502, detail=f"remove failed: {exc}") from exc

    api_logger.info("Deleted key %r", safe_name)
    return KeyDeleted(name=safe_name, message="Key deleted successfully.")


@router.get(
    "",
    response_model=StatsResponse,
    summary="List keys with statistics",
    description="Runs the management script 'stats' command and returns peer "
    "statistics as a structured model.",
)
def list_keys() -> StatsResponse:
    """Return the list of keys together with their traffic statistics."""
    settings = get_settings()
    try:
        result = run_manage(settings.manage_script, "stats")
    except ScriptError as exc:
        api_logger.error("Failed to list keys: %s", exc)
        raise HTTPException(status_code=502, detail=f"stats failed: {exc}") from exc

    stats = parse_stats(result.stdout)
    api_logger.info("Listed %d key(s)", len(stats.peers))
    return stats
