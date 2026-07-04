"""Networking helpers: proxy line parsing and public-IP discovery."""

from __future__ import annotations

import re
from typing import Optional

import requests

from app.constants import PUBLIC_IP_URL

_PROXY_RE = re.compile(
    r"(?:socks5h?://|socks4://|https?://)?"
    r"(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}):(\d{2,5})"
)


def parse_proxy_line(line: str) -> Optional[tuple[str, int]]:
    """Extract ``(ip, port)`` from an arbitrary text line, or ``None``."""
    line = line.strip()
    if not line or line.startswith("#"):
        return None
    match = _PROXY_RE.search(line)
    if not match:
        return None
    ip, port_str = match.group(1), match.group(2)
    if any(int(octet) > 255 for octet in ip.split(".")):
        return None
    port = int(port_str)
    if not 1 <= port <= 65535:
        return None
    return ip, port


def get_public_ip(timeout: float = 8.0) -> Optional[str]:
    """Return this machine's public IP (direct connection) or ``None``."""
    try:
        response = requests.get(PUBLIC_IP_URL, timeout=timeout)
        response.raise_for_status()
        return response.json().get("ip")
    except (requests.RequestException, ValueError):
        return None


def get_lan_ip() -> str:
    """Return this machine's LAN IP (the address a phone would connect to)."""
    import socket

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        sock.connect(("8.8.8.8", 80))
        return sock.getsockname()[0]
    except OSError:
        return "127.0.0.1"
    finally:
        sock.close()
