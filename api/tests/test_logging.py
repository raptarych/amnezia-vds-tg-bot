"""Tests for the API logging configuration."""

from __future__ import annotations

import logging
from pathlib import Path

from app.logging_setup import configure_logging, normalize_level


def test_configure_logging_writes_to_file(tmp_path: Path) -> None:
    log_file = tmp_path / "api.log"
    configure_logging(level="INFO", log_file=str(log_file))

    logger = logging.getLogger("amnezia.api.test")
    logger.info("hello from logging test")

    for handler in logging.getLogger().handlers:
        handler.flush()

    content = log_file.read_text(encoding="utf-8")
    assert "hello from logging test" in content


def test_normalize_level() -> None:
    assert normalize_level(None) == "INFO"
    assert normalize_level("debug") == "DEBUG"
    assert normalize_level("WARNING") == "WARNING"
    assert normalize_level("bogus") == "INFO"
