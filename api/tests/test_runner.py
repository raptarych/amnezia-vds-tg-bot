"""Tests for the management-script runner and its failure logging."""

from __future__ import annotations

import logging
from pathlib import Path

import pytest

from app.runner import ScriptError, run_manage

# A long marker string that would be truncated by a naive `[-500:]` slice.
LONG_MARKER = "X" * 5000 + "-TAIL-SENTINEL"


def _write_mock(path: Path, code: str) -> Path:
    path.write_text(code, encoding="utf-8")
    return path


def _failing_script() -> str:
    return (
        "import sys\n"
        f"sys.stdout.write('stdout-line {LONG_MARKER}\\n')\n"
        "sys.stderr.write('stderr-line boom\\n')\n"
        "sys.exit(3)\n"
    )


def test_run_manage_raises_script_error_with_full_output(tmp_path: Path) -> None:
    script = _write_mock(tmp_path / "fail.py", _failing_script())

    with pytest.raises(ScriptError) as excinfo:
        run_manage(str(script), "boom")

    exc = excinfo.value
    assert exc.exit_code == 3
    assert LONG_MARKER in exc.stdout
    assert "stderr-line boom" in exc.stderr


def test_failure_logs_full_untruncated_output(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    script = _write_mock(tmp_path / "fail.py", _failing_script())

    with (
        caplog.at_level(logging.ERROR, logger="amnezia.runner"),
        pytest.raises(ScriptError),
    ):
        run_manage(str(script), "boom")

    full_log = "\n".join(rec.getMessage() for rec in caplog.records)
    # The sentinel lives past a 500-char window, proving nothing was truncated.
    assert LONG_MARKER in full_log
    assert "stdout-line" in full_log
    assert "stderr-line boom" in full_log


def test_run_manage_missing_script(tmp_path: Path) -> None:
    missing = tmp_path / "does_not_exist.py"
    with pytest.raises(ScriptError):
        run_manage(str(missing), "stats")
