"""Small pure formatting helpers."""

from __future__ import annotations


def format_bytes(num: float) -> str:
    """Render a byte count as a human-readable string."""
    value = float(num)
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if abs(value) < 1024.0:
            return f"{value:.1f} {unit}"
        value /= 1024.0
    return f"{value:.1f} PB"


def format_speed(bytes_per_sec: float) -> str:
    """Render a transfer rate (bytes/second)."""
    return f"{format_bytes(bytes_per_sec)}/s"


def format_duration(seconds: float) -> str:
    """Render a duration as HH:MM:SS (or MM:SS when under an hour)."""
    total = int(seconds)
    hours, remainder = divmod(total, 3600)
    minutes, secs = divmod(remainder, 60)
    if hours:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    return f"{minutes:02d}:{secs:02d}"
