"""Tests for the generated-client wrapper."""

from __future__ import annotations

from dataclasses import dataclass
from http import HTTPStatus
from unittest.mock import AsyncMock, patch

import pytest

from app.api import AmneziaClient, ApiError
from client.models import KeyGenerated, PeerStats, StatsResponse, Totals


@dataclass
class FakeDetailResponse:
    status_code: HTTPStatus
    content: bytes


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
    client = AmneziaClient("http://x", "secret")
    detail = FakeDetailResponse(status_code=HTTPStatus.OK, content=b"CONF")
    with patch(
        "app.api.get_key_keys_key_name_get.asyncio_detailed",
        new=AsyncMock(return_value=detail),
    ) as mock:
        data = await client.download_key("phone", "conf")
        assert data == b"CONF"
        mock.assert_awaited_once()
        _, kwargs = mock.call_args
        assert kwargs["key_name"] == "phone"
        assert kwargs["ext"] == "conf"


@pytest.mark.asyncio
async def test_download_key_non_ok_raises() -> None:
    client = AmneziaClient("http://x", "secret")
    detail = FakeDetailResponse(status_code=HTTPStatus.NOT_FOUND, content=b"")
    with patch(
        "app.api.get_key_keys_key_name_get.asyncio_detailed",
        new=AsyncMock(return_value=detail),
    ):
        with pytest.raises(ApiError):
            await client.download_key("phone", "conf")


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
