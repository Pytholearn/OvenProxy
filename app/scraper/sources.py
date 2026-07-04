"""Built-in list of public proxy providers (SOCKS5 / SOCKS4 / HTTP)."""

from __future__ import annotations

from app.models.proxy import Protocol
from app.models.source import ProxySource

DEFAULT_SOURCES: list[ProxySource] = [
    # ---------------------------------------------------------------- SOCKS5
    ProxySource(
        "ProxyScrape · SOCKS5",
        "https://api.proxyscrape.com/v2/?request=getproxies&protocol=socks5&timeout=10000&country=all",
        protocol=Protocol.SOCKS5,
    ),
    ProxySource(
        "TheSpeedX · SOCKS5",
        "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/socks5.txt",
        protocol=Protocol.SOCKS5,
    ),
    ProxySource(
        "Monosans · SOCKS5",
        "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/socks5.txt",
        protocol=Protocol.SOCKS5,
    ),
    ProxySource(
        "Proxifly · SOCKS5",
        "https://raw.githubusercontent.com/proxifly/free-proxy-list/main/proxies/protocols/socks5/data.txt",
        protocol=Protocol.SOCKS5,
    ),
    ProxySource(
        "Proxy-List.Download · SOCKS5",
        "https://www.proxy-list.download/api/v1/get?type=socks5",
        protocol=Protocol.SOCKS5,
    ),
    # ---------------------------------------------------------------- SOCKS4
    ProxySource(
        "ProxyScrape · SOCKS4",
        "https://api.proxyscrape.com/v2/?request=getproxies&protocol=socks4&timeout=10000&country=all",
        protocol=Protocol.SOCKS4,
    ),
    ProxySource(
        "TheSpeedX · SOCKS4",
        "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/socks4.txt",
        protocol=Protocol.SOCKS4,
    ),
    ProxySource(
        "Monosans · SOCKS4",
        "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/socks4.txt",
        protocol=Protocol.SOCKS4,
    ),
    ProxySource(
        "Proxy-List.Download · SOCKS4",
        "https://www.proxy-list.download/api/v1/get?type=socks4",
        protocol=Protocol.SOCKS4,
    ),
    # ------------------------------------------------------------------ HTTP
    ProxySource(
        "ProxyScrape · HTTP",
        "https://api.proxyscrape.com/v2/?request=getproxies&protocol=http&timeout=10000&country=all",
        protocol=Protocol.HTTP,
    ),
    ProxySource(
        "TheSpeedX · HTTP",
        "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt",
        protocol=Protocol.HTTP,
    ),
    ProxySource(
        "Monosans · HTTP",
        "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/http.txt",
        protocol=Protocol.HTTP,
    ),
    ProxySource(
        "Proxy-List.Download · HTTP",
        "https://www.proxy-list.download/api/v1/get?type=http",
        protocol=Protocol.HTTP,
    ),
]
