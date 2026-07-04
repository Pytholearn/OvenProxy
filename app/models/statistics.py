"""Lightweight statistics dataclasses passed across Qt signals."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class CheckProgress:
    """Live progress of a proxy-checking run."""

    total: int = 0
    checked: int = 0
    alive: int = 0
    dead: int = 0
    speed: float = 0.0  # checks per second
    elapsed: float = 0.0  # seconds

    @property
    def remaining(self) -> int:
        return max(0, self.total - self.checked)

    @property
    def percent(self) -> int:
        if self.total <= 0:
            return 0
        return int(self.checked / self.total * 100)


@dataclass
class GatewayStats:
    """A snapshot of the local gateway's traffic and connection state."""

    running: bool = False
    active_clients: int = 0
    upload_bytes: int = 0
    download_bytes: int = 0
    upload_speed: float = 0.0  # bytes/second (filled by TrafficMonitor)
    download_speed: float = 0.0
    latency_ms: float = 0.0
    session_seconds: float = 0.0

    @property
    def total_bytes(self) -> int:
        return self.upload_bytes + self.download_bytes
