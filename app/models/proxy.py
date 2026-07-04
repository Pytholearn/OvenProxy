"""The :class:`Proxy` domain model and its enums."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional


class Protocol(str, Enum):
    """Supported proxy protocols."""

    SOCKS5 = "socks5"
    SOCKS4 = "socks4"
    HTTP = "http"


class ProxyStatus(str, Enum):
    """Lifecycle status of a proxy."""

    UNKNOWN = "Unknown"
    CHECKING = "Checking"
    ALIVE = "Alive"
    DEAD = "Dead"


class AnonymityLevel(str, Enum):
    """How much the proxy reveals about the original client."""

    UNKNOWN = "Unknown"
    TRANSPARENT = "Transparent"
    ANONYMOUS = "Anonymous"
    ELITE = "Elite"


@dataclass
class Proxy:
    """A single proxy and everything we know about it."""

    ip: str
    port: int
    protocol: Protocol = Protocol.SOCKS5
    country: str = ""
    country_code: str = ""
    exit_ip: str = ""
    latency_ms: Optional[float] = None
    status: ProxyStatus = ProxyStatus.UNKNOWN
    anonymity: AnonymityLevel = AnonymityLevel.UNKNOWN
    last_checked: Optional[datetime] = None

    @property
    def address(self) -> str:
        """``ip:port`` form, also the database primary key."""
        return f"{self.ip}:{self.port}"

    @property
    def uri(self) -> str:
        """``protocol://ip:port`` form."""
        return f"{self.protocol.value}://{self.ip}:{self.port}"

    def __hash__(self) -> int:
        return hash((self.ip, self.port, self.protocol))

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Proxy):
            return NotImplemented
        return (self.ip, self.port, self.protocol) == (
            other.ip,
            other.port,
            other.protocol,
        )

    def to_dict(self) -> dict:
        return {
            "ip": self.ip,
            "port": self.port,
            "protocol": self.protocol.value,
            "country": self.country,
            "country_code": self.country_code,
            "exit_ip": self.exit_ip,
            "latency_ms": self.latency_ms,
            "status": self.status.value,
            "anonymity": self.anonymity.value,
            "last_checked": self.last_checked.isoformat() if self.last_checked else None,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Proxy":
        last_checked = data.get("last_checked")
        return cls(
            ip=str(data["ip"]),
            port=int(data["port"]),
            protocol=Protocol(data.get("protocol", "socks5")),
            country=data.get("country", ""),
            country_code=data.get("country_code", ""),
            exit_ip=data.get("exit_ip", ""),
            latency_ms=data.get("latency_ms"),
            status=ProxyStatus(data.get("status", "Unknown")),
            anonymity=AnonymityLevel(data.get("anonymity", "Unknown")),
            last_checked=datetime.fromisoformat(last_checked) if last_checked else None,
        )
