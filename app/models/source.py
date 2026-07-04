"""The :class:`ProxySource` model describing a proxy list provider."""

from __future__ import annotations

from dataclasses import dataclass

from app.models.proxy import Protocol


@dataclass
class ProxySource:
    """A remote URL that returns a list of proxies."""

    name: str
    url: str
    enabled: bool = True
    protocol: Protocol = Protocol.SOCKS5
    favorite: bool = False
    custom: bool = False

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "url": self.url,
            "enabled": self.enabled,
            "protocol": self.protocol.value,
            "favorite": self.favorite,
            "custom": self.custom,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ProxySource":
        return cls(
            name=str(data["name"]),
            url=str(data["url"]),
            enabled=bool(data.get("enabled", True)),
            protocol=Protocol(data.get("protocol", "socks5")),
            favorite=bool(data.get("favorite", False)),
            custom=bool(data.get("custom", False)),
        )
