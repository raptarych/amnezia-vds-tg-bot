"""Application configuration.

Settings are loaded from environment variables with sensible defaults for a
standard Ubuntu 24 host deployment. All paths can be overridden, which is
useful both for local development and for automated tests.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration for the Amnezia management API."""

    #: Header name that must carry the shared secret.
    secret_header: str = "X-API-Secret"

    #: Path to the file containing the expected API secret (one line).
    secret_file: str = "/etc/amnezia-vds/api_secret"

    #: Path to the AmneziaWireGuard management script.
    manage_script: str = "/root/awg/manage_amneziawg.sh"

    #: Directory where per-key configuration files are stored.
    awg_dir: str = "/root/awg"

    #: Root logging level (DEBUG, INFO, WARNING, ERROR).
    log_level: str = "INFO"

    #: Optional path to a rotating log file. Empty string disables file logging.
    log_file: str = "/var/log/amnezia_api"

    model_config = SettingsConfigDict(
        env_prefix="AMNEZIA_API_", env_file=".env", extra="ignore"
    )

    @property
    def secret(self) -> str:
        """Return the expected API secret read from the secret file."""
        content = _read_secret(Path(self.secret_file))
        return content.strip()

    @property
    def awg_path(self) -> Path:
        """Return the AWG directory as a :class:`pathlib.Path`."""
        return Path(self.awg_dir)


def _read_secret(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return ""


@lru_cache
def get_settings() -> Settings:
    """Return a cached :class:`Settings` instance."""
    return Settings()
