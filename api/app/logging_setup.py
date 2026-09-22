"""Logging configuration for the API.

Provides a single ``configure_logging`` helper that installs a consistent
formatter on the root logger and, optionally, a rotating file handler. The log
level and destination can be tuned with environment variables so the behaviour
is the same under uvicorn, plain ``python`` and pytest.
"""

from __future__ import annotations

import logging
import sys
from logging.handlers import RotatingFileHandler
from typing import Literal

CONSOLE_FORMAT = "%(asctime)s %(levelname)-8s %(name)s | %(message)s"
FILE_FORMAT = (
    "%(asctime)s %(levelname)-8s %(name)s | "
    "%(pathname)s:%(lineno)d | %(message)s"
)

#: Applications loggers, kept as module-level references for convenience.
api_logger = logging.getLogger("amnezia.api")
runner_logger = logging.getLogger("amnezia.runner")


def configure_logging(
    level: str = "INFO",
    log_file: str | None = None,
    max_bytes: int = 10 * 1024 * 1024,
    backup_count: int = 5,
) -> None:
    """Configure the root logger and optional rotating file handler.

    Args:
        level: Root log level (e.g. ``DEBUG``, ``INFO``).
        log_file: Optional path to a log file. When ``None`` only stderr/stdout
            is used.
        max_bytes: Maximum size of a single log file before rotation.
        backup_count: Number of rotated files to keep.
    """
    root = logging.getLogger()
    root.setLevel(level.upper())

    if not any(
        isinstance(h, logging.StreamHandler) and not isinstance(h, RotatingFileHandler)
        for h in root.handlers
    ):
        console = logging.StreamHandler(sys.stderr)
        console.setFormatter(logging.Formatter(CONSOLE_FORMAT))
        root.addHandler(console)

    if log_file:
        file_handler = RotatingFileHandler(
            log_file, maxBytes=max_bytes, backupCount=backup_count
        )
        file_handler.setFormatter(logging.Formatter(FILE_FORMAT))
        root.addHandler(file_handler)

    # uvicorn uses its own loggers; keep them at a sensible level.
    logging.getLogger("uvicorn.access").setLevel("WARNING")


def normalize_level(value: str | None) -> Literal["DEBUG", "INFO", "WARNING", "ERROR"]:
    """Map an arbitrary config string to a supported log level name."""
    normalized = (value or "INFO").upper()
    if normalized not in {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}:
        return "INFO"
    return normalized  # type: ignore[return-value]
