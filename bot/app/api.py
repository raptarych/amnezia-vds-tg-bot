"""Thin wrapper around the generated OpenAPI client.

Provides convenient async methods for the operations the bot needs, maps API
errors to a custom exception, and passes the shared secret on every call.
"""

from __future__ import annotations

import httpx

from app import config as config_module
from client import Client
from client.api.keys import (
    generate_key_keys_post,
    get_key_keys_key_name_get,
    list_keys_keys_get,
)
from client.api.server import server_restart_server_restart_post
from client.models import StatsResponse


class ApiError(RuntimeError):
    """Raised when the backing HTTP API reports an error."""


class AmneziaClient:
    """Wrapper exposing the operations used by the bot."""

    def __init__(self, base_url: str, secret: str, *, timeout: float = 120.0) -> None:
        self._client = Client(base_url=base_url, timeout=httpx.Timeout(timeout))
        self._secret = secret

    @classmethod
    def from_config(cls, cfg: config_module.BotConfig) -> AmneziaClient:
        """Build a client from a :class:`BotConfig`."""
        return cls(cfg.api_url, cfg.api_secret)

    async def generate_key(self, name: str) -> None:
        """Generate a new key via the API."""
        result = await generate_key_keys_post.asyncio(
            client=self._client, name=name, x_api_secret=self._secret
        )
        self._raise_for_result(result, action="generate key")

    async def download_key(self, name: str, ext: str) -> bytes:
        """Download a key file's raw content."""
        detail = await get_key_keys_key_name_get.asyncio_detailed(
            client=self._client, key_name=name, ext=ext, x_api_secret=self._secret
        )
        if detail.status_code != 200:
            raise ApiError(f"Failed to download {name}.{ext}: {detail.status_code}")
        if not detail.content:
            raise ApiError(f"Empty content returned for {name}.{ext}")
        return detail.content

    async def list_keys(self) -> StatsResponse:
        """Fetch and return the key statistics."""
        result = await list_keys_keys_get.asyncio(
            client=self._client, x_api_secret=self._secret
        )
        self._raise_for_result(result, action="list keys")
        stats = result
        if not isinstance(stats, StatsResponse):
            raise ApiError("Unexpected response shape from the keys list endpoint.")
        return stats

    async def restart_server(self) -> None:
        """Restart the Amnezia server via the API."""
        detail = await server_restart_server_restart_post.asyncio_detailed(
            client=self._client, x_api_secret=self._secret
        )
        if detail.status_code != 200:
            raise ApiError(f"Failed to restart server: {detail.status_code}")

    @staticmethod
    def _raise_for_result(result, action: str) -> None:
        """Raise an :class:`ApiError` when an unhelpful payload is returned."""
        if result is None:
            raise ApiError(f"API returned an error while trying to {action}.")
        status = getattr(result, "status", None)
        if status is not None and status == 422:
            raise ApiError(f"Invalid request parameters while trying to {action}.")
