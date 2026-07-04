"""Application-wide constants."""

from __future__ import annotations

from pathlib import Path


def _read_version() -> str:
    """Read the application version from the project-root ``VERSION`` file."""
    try:
        version_file = Path(__file__).resolve().parent.parent / "VERSION"
        if version_file.exists():
            text = version_file.read_text(encoding="utf-8-sig").strip()
            if text:
                return text.splitlines()[0].strip()
    except OSError:
        pass
    return "1.0.0"


APP_NAME: str = "OvenProxy"
APP_VERSION: str = _read_version()
ORG_NAME: str = "OvenProxy"

# Endpoint used by the checker. Returns the *exit* IP and geolocation as seen
# through the proxy, which lets us derive country + anonymity in a single request.
DEFAULT_CHECK_URL: str = "http://ip-api.com/json/?fields=status,countryCode,country,query"

# Endpoint used once (direct) to learn our real IP for anonymity comparison.
PUBLIC_IP_URL: str = "https://api.ipify.org?format=json"

DEFAULT_GATEWAY_HOST: str = "127.0.0.1"
DEFAULT_GATEWAY_PORT: int = 1080
