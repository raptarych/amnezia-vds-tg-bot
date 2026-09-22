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
    """Raised when the management script finishes with a non-zero exit code."""

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


def run_manage(script: str, *args: str, timeout: int = 120) -> CommandResult:
    """Invoke the management script with the given positional arguments.

    Args:
        script: Absolute path to the management script.
        *args: Arguments passed to the script.
        timeout: Timeout in seconds before the process is killed.

    Returns:
        A :class:`CommandResult` holding stdout/stderr and exit code.

    Raises:
        ScriptError: If the script exited with a non-zero code.
    """
    runner_logger.info("Executing management command: %s %s", script, " ".join(args))
    try:
        command: list[str] = [script, *args]
        if os.name == "nt":
            # Testing support on Windows: Python mocks run via the interpreter,
            # anything else is treated as a bash script (e.g. Git Bash).
            if script.endswith(".py"):
                command = [sys.executable, *command]
            else:
                command = ["bash", *command]
        proc = subprocess.run(
            command,
            capture_output=True,
            text=False,
            timeout=timeout,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout.decode("utf-8", errors="replace") if exc.stdout else ""
        stderr = exc.stderr.decode("utf-8", errors="replace") if exc.stderr else ""
        runner_logger.error(
            "Management command timed out after %ss: %s",
            timeout,
            " ".join(args),
        )
        raise ScriptError(-1, stderr, stdout) from exc

    stdout = proc.stdout.decode("utf-8", errors="replace")
    stderr = proc.stderr.decode("utf-8", errors="replace")

    if proc.returncode != 0:
        runner_logger.error(
            "Management command failed (exit=%s): %s stderr=%r",
            proc.returncode,
            " ".join(args),
            stderr[-500:],
        )
        raise ScriptError(proc.returncode, stderr, stdout)

    runner_logger.info("Management command succeeded: %s", " ".join(args))
    return CommandResult(proc.returncode, stdout, stderr)
