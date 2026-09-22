"""Tests for the generated-client wrapper."""

from __future__ import annotations

from dataclasses import dataclass
from unittest.mock import AsyncMock, patch

import pytest

from app.api import AmneziaClient, ApiError
from client.models import KeyDeleted, KeyGenerated, PeerStats, StatsResponse, Totals


@dataclass
class FakeResponse:
    status_code: int
    content: bytes


def _client_with_httpx(response: FakeResponse) -> AmneziaClient:
    """Build an AmneziaClient whose httpx request returns ``response``."""
    client = AmneziaClient("http://x", "secret")

    class FakeHttpx:
        def request(self, **kwargs):
            return response

    client._client.set_httpx_client(FakeHttpx())
    return client


@pytest.mark.asyncio
async def test_generate_key_success() -> None:
    client = AmneziaClient("http://x", "secret")
    generated = KeyGenerated(name="phone", message="ok")
    with patch(
        "app.api.generate_key_keys_post.asyncio",
        new=AsyncMock(return_value=generated),
    ) as mock:
        await client.generate_key("phone")
        mock.assert_awaited_once()
        _, kwargs = mock.call_args
        assert kwargs["name"] == "phone"
        assert kwargs["x_api_secret"] == "secret"


@pytest.mark.asyncio
async def test_download_key_returns_content() -> None:
    client = _client_with_httpx(FakeResponse(status_code=200, content=b"CONF"))
    data = await client.download_key("phone", "conf")
    assert data == b"CONF"


@pytest.mark.asyncio
async def test_download_key_non_ok_raises() -> None:
    client = _client_with_httpx(FakeResponse(status_code=404, content=b""))
    with pytest.raises(ApiError):
        await client.download_key("phone", "conf")


@pytest.mark.asyncio
async def test_delete_key_success() -> None:
    client = AmneziaClient("http://x", "secret")
    deleted = KeyDeleted(name="phone", message="ok")
    with patch(
        "app.api.delete_key_keys_key_name_delete.asyncio",
        new=AsyncMock(return_value=deleted),
    ) as mock:
        await client.delete_key("phone")
        mock.assert_awaited_once()
        _, kwargs = mock.call_args
        assert kwargs["key_name"] == "phone"
        assert kwargs["x_api_secret"] == "secret"


@pytest.mark.asyncio
async def test_list_keys_returns_stats() -> None:
    client = AmneziaClient("http://x", "secret")
    stats = StatsResponse(
        peers=[PeerStats(name="a", ip="1.1.1.1", received="0 B", sent="0 B",
                         last_handshake="никогда", status="Неактивен")],
        totals=Totals(received="0 B", sent="0 B"),
    )
    with patch(
        "app.api.list_keys_keys_get.asyncio", new=AsyncMock(return_value=stats)
    ) as mock:
        result = await client.list_keys()
        assert result is stats
        mock.assert_awaited_once()
