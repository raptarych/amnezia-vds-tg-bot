"""Safe execution of the AmneziaWireGuard management script.

The management script is invoked on the host via ``subprocess``. Commands are
never shell-interpolated; arguments are passed as a list to avoid injection and
to keep the behaviour predictable on Ubuntu 24.
"""

from __future__ import annotations

import os
import subprocess
import sys
from dataclasses import dataclass

from .logging_setup import runner_logger


class ScriptError(RuntimeError):
    """Raised when the management script cannot be run or exits unsuccessfully.

    Carries the raw stdout and stderr so callers and loggers can inspect the
    full, untruncated output of the failed command.
    """

    def __init__(self, exit_code: int, stderr: str, stdout: str = "") -> None:
        self.exit_code = exit_code
        self.stderr = stderr
        self.stdout = stdout
        super().__init__(
            f"management script failed with exit code {exit_code}: {stderr.strip()}"
        )


@dataclass(slots=True)
class CommandResult:
    """Outcome of a single management script invocation."""

    exit_code: int
    stdout: str
    stderr: str

    @property
    def ok(self) -> bool:
        """Return ``True`` when the script exited successfully."""
        return self.exit_code == 0


def _decode(data: bytes | None) -> str:
    """Decode captured output bytes as UTF-8, tolerating invalid bytes."""
    return data.decode("utf-8", errors="replace") if data else ""


def _build_command(script: str, args: tuple[str, ...]) -> list[str]:
    """Build the process command line, handling Windows test support."""
    command: list[str] = [script, *args]
    if os.name == "nt":
        # Testing support on Windows: Python mocks run via the interpreter,
        # anything else is treated as a bash script (e.g. Git Bash).
        if script.endswith(".py"):
            command = [sys.executable, *command]
        else:
            command = ["bash", *command]
    return command


def run_manage(script: str, *args: str, timeout: int = 120) -> CommandResult:
    """Invoke the management script with the given positional arguments.

    Args:
        script: Absolute path to the management script.
        *args: Arguments passed to the script.
        timeout: Timeout in seconds before the process is killed.

    Returns:
        A :class:`CommandResult` holding stdout/stderr and exit code.

    Raises:
        ScriptError: If the script exited with a non-zero code, timed out, or
            could not be launched. The exception carries the full output of the
            failed invocation.
    """
    runner_logger.info("Executing management command: %s %s", script, " ".join(args))
    command = _build_command(script, args)

    try:
        proc = subprocess.run(
            command,
            capture_output=True,
            text=False,
            timeout=timeout,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        stdout = _decode(exc.stdout)
        stderr = _decode(exc.stderr)
        _log_failure(
            status=f"timeout after {timeout}s",
            args=args,
            stdout=stdout,
            stderr=stderr,
        )
        raise ScriptError(-1, stderr, stdout) from exc
    except OSError as exc:
        # e.g. the script file is missing or not executable.
        runner_logger.error(
            "Management command could not be launched (%s): %s -> %s",
            exc,
            script,
            " ".join(args),
        )
        raise ScriptError(-1, str(exc)) from exc
    except subprocess.SubprocessError as exc:
        runner_logger.error(
            "Management command failed to run (%r): %s", exc, " ".join(args)
        )
        raise ScriptError(-1, str(exc)) from exc

    stdout = _decode(proc.stdout)
    stderr = _decode(proc.stderr)

    if proc.returncode != 0:
        _log_failure(
            status=f"exit={proc.returncode}",
            args=args,
            stdout=stdout,
            stderr=stderr,
        )
        raise ScriptError(proc.returncode, stderr, stdout)

    runner_logger.info("Management command succeeded: %s", " ".join(args))
    return CommandResult(proc.returncode, stdout, stderr)


def _log_failure(status: str, args: tuple[str, ...], stdout: str, stderr: str) -> None:
    """Log the full, untruncated output of a failed management command."""
    runner_logger.error(
        "Management command failed (%s), args=%s\n--- stdout ---\n%s\n"
        "--- stderr ---\n%s\n--- end ---",
        status,
        " ".join(args),
        stdout or "<empty>",
        stderr or "<empty>",
    )
