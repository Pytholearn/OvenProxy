"""Domain models: proxies, sources and statistics dataclasses."""

from app.models.proxy import AnonymityLevel, Protocol, Proxy, ProxyStatus
from app.models.source import ProxySource
from app.models.statistics import CheckProgress, GatewayStats

__all__ = [
    "AnonymityLevel",
    "Protocol",
    "Proxy",
    "ProxyStatus",
    "ProxySource",
    "CheckProgress",
    "GatewayStats",
]
