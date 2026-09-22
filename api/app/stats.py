"""Parsing utilities for the management script output."""

from __future__ import annotations

import re

from .schemas import PeerStats, StatsResponse, Totals

# Header: Имя | IP | Получено | Отправлено | Последний handshake | Статус
_ROW_RE = re.compile(
    r"^\s*(?P<name>.+?)\s*\|\s*(?P<ip>[\d.:a-fA-F/]+)\s*\|\s*"
    r"(?P<received>.+?)\s*\|\s*(?P<sent>.+?)\s*\|\s*"
    r"(?P<handshake>.+?)\s*\|\s*(?P<status>.+?)\s*$"
)

_TOTAL_RE = re.compile(
    r"Итого:\s*Получено\s*(?P<received>.+?)\s*,\s*"
    r"Отправлено\s*(?P<sent>.+?)\s*$"
)

def parse_stats(output: str) -> StatsResponse:
    """Parse the ``stats`` command output into a :class:`StatsResponse`.

    The output contains a human-readable table followed by an aggregate
    "Итого" (total) line. Rows without a parseable IP are treated as headers
    or noise and skipped.

    Args:
        output: Raw output produced by the management script.

    Returns:
        A structured :class:`StatsResponse`.
    """
    peers: list[PeerStats] = []
    totals: Totals | None = None

    for line in output.splitlines():
        total_match = _TOTAL_RE.search(line)
        if total_match:
            totals = Totals(
                received=total_match.group("received").strip(),
                sent=total_match.group("sent").strip(),
            )
            continue

        row_match = _ROW_RE.match(line)
        if not row_match:
            continue

        try:
            peer = PeerStats(
                name=row_match.group("name").strip(),
                ip=row_match.group("ip").strip(),
                received=row_match.group("received").strip(),
                sent=row_match.group("sent").strip(),
                last_handshake=row_match.group("handshake").strip(),
                status=row_match.group("status").strip(),
            )
        except (ValueError, KeyError):
            continue
        peers.append(peer)

    if totals is None:
        totals = Totals(received="", sent="")

    return StatsResponse(peers=peers, totals=totals)
