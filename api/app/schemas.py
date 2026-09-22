"""Pydantic request/response models for the API."""

from __future__ import annotations

from pydantic import BaseModel, Field


class PeerStats(BaseModel):
    """Statistics for a single AmneziaWireGuard peer (key)."""

    name: str = Field(description="Key/peer name.")
    ip: str = Field(description="Peer IP address inside the tunnel.")
    received: str = Field(description="Amount of data received, human-readable.")
    sent: str = Field(description="Amount of data sent, human-readable.")
    last_handshake: str = Field(
        description="Date/time of the last handshake or 'never'."
    )
    status: str = Field(description="Peer activity status, e.g. Active/Inactive.")


class Totals(BaseModel):
    """Aggregated traffic totals across all peers."""

    received: str = Field(description="Total data received by all peers.")
    sent: str = Field(description="Total data sent by all peers.")


class StatsResponse(BaseModel):
    """Response of the key list (stats) endpoint."""

    peers: list[PeerStats] = Field(description="Per-peer statistics.")
    totals: Totals = Field(description="Aggregated totals.")


class KeyGenerated(BaseModel):
    """Response returned after successfully generating a new key."""

    name: str = Field(description="Name of the generated key.")
    message: str = Field(description="Human-readable confirmation message.")


class KeyDeleted(BaseModel):
    """Response returned after successfully deleting a key."""

    name: str = Field(description="Name of the deleted key.")
    message: str = Field(description="Human-readable confirmation message.")


class ErrorResponse(BaseModel):
    """Uniform error body returned for failed operations."""

    detail: str = Field(description="Human-readable error description.")
