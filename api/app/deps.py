"""Authentication helpers.

Every API request must carry a shared secret in a dedicated header. The
header value is compared against the reference secret stored in a file on the
host. An optional bootstrap secret (from environment) allows provisioning the
reference file before it exists on first boot.
"""

from __future__ import annotations

from fastapi import Header, HTTPException, Request, status

from .config import get_settings


def _constant_time_equal(left: str, right: str) -> bool:
    """Compare two strings in constant time to avoid timing attacks."""
    if len(left) != len(right):
        return False
    result = 0
    for a, b in zip(left.encode(), right.encode()):
        result |= a ^ b
    return result == 0


def require_secret(
    request: Request,
    x_api_secret: str = Header(default="", alias="X-API-Secret"),
) -> None:
    """Validate the incoming secret against the reference stored on the host.

    Args:
        request: The incoming FastAPI request.
        x_api_secret: Value of the ``X-API-Secret`` header.

    Raises:
        HTTPException: If the secret is missing or does not match.
    """
    settings = get_settings()
    reference = settings.secret
    if not reference:
        reference = request.app.state.bootstrap_secret

    if not x_api_secret or not reference or not _constant_time_equal(
        x_api_secret, reference
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API secret.",
            headers={"WWW-Authenticate": "Bearer"},
        )
