"""Safe handling of key names and file downloads."""

from __future__ import annotations

import re
from pathlib import Path

ALLOWED_EXTENSIONS = frozenset({"conf", "png", "vpnuri"})

# Key names are used as file basenames, so they must not contain path
# separators or characters that could escape the AWG directory.
_SAFE_NAME_RE = re.compile(r"^[A-Za-z0-9_.\-\u0400-\u04FF\u0301]+$")


def validate_key_name(name: str | None) -> str:
    """Normalise and validate a user-supplied key name.

    Args:
        name: Raw key name from the request.

    Returns:
        The validated key name.

    Raises:
        ValueError: If the name is missing or contains disallowed characters.
    """
    if not name or not name.strip():
        raise ValueError("Key name must not be empty.")
    candidate = name.strip()
    if not _SAFE_NAME_RE.fullmatch(candidate):
        raise ValueError("Key name contains disallowed characters.")
    if candidate in {".", ".."} or candidate.startswith("."):
        raise ValueError("Key name is not allowed.")
    return candidate


def resolve_key_file(awg_dir: Path, key_name: str, extension: str) -> Path:
    """Resolve the on-disk path for a key file, guarding against traversal.

    Args:
        awg_dir: Base AWG directory.
        key_name: Validated key name.
        extension: One of the allowed file extensions.

    Returns:
        The absolute :class:`pathlib.Path` to the requested file.

    Raises:
        ValueError: If the extension is not allowed, or the resolved path
            escapes the base directory.
    """
    ext = extension.lower().lstrip(".")
    if ext not in ALLOWED_EXTENSIONS:
        raise ValueError(
            f"Unsupported file extension '{extension}'. "
            f"Allowed: {sorted(ALLOWED_EXTENSIONS)}."
        )

    path = (awg_dir / f"{key_name}.{ext}").resolve()
    base = awg_dir.resolve()
    if not path.is_relative_to(base):
        raise ValueError("Requested file is outside the allowed directory.")
    if not path.is_file():
        raise FileNotFoundError(f"File not found: {path.name}")
    return path
