"""Tests for the statistics table rendering."""

from __future__ import annotations

from app.handlers.commands import _render_stats_table
from client.models import PeerStats, StatsResponse, Totals


def _stats() -> StatsResponse:
    return StatsResponse(
        peers=[
            PeerStats(
                name="my_phone",
                ip="172.16.17.2",
                received="0 B",
                sent="0 B",
                last_handshake="никогда",
                status="Неактивен",
            ),
            PeerStats(
                name="laptop",
                ip="172.16.17.3",
                received="21.28 MiB",
                sent="220.70 MiB",
                last_handshake="2026-09-22 18:15:47",
                status="Активен",
            ),
        ],
        totals=Totals(received="21.28 MiB", sent="220.70 MiB"),
    )


def test_render_stats_table_contains_values() -> None:
    rendered = _render_stats_table(_stats())
    assert "my_phone" in rendered
    assert "172.16.17.3" in rendered
    assert "21.28 MiB" in rendered
    assert "Неактивен" in rendered


def test_render_stats_table_has_borders() -> None:
    rendered = _render_stats_table(_stats())
    # PrettyTable draws a framed block with +---+ borders.
    assert rendered.startswith("+")
    assert "+----" in rendered
