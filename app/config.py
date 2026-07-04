"""Typed application configuration with JSON persistence."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, fields
from pathlib import Path

from app.constants import DEFAULT_CHECK_URL, DEFAULT_GATEWAY_PORT


@dataclass
class AppConfig:
    """User-configurable settings, persisted to ``config.json``."""

    threads: int = 200
    timeout: float = 10.0
    retries: int = 1
    max_proxies: int = 0  # 0 == unlimited
    auto_remove_dead: bool = True
    auto_export: bool = False
    theme: str = "dark"
    language: str = "en"
    gateway_port: int = DEFAULT_GATEWAY_PORT
    check_url: str = DEFAULT_CHECK_URL
    update_version_url: str = (
        "https://raw.githubusercontent.com/Pytholearn/OvenProxy/refs/heads/main/VERSION"
    )
    update_repo_url: str = "https://github.com/Pytholearn/OvenProxy.git"
    check_updates_on_startup: bool = True

    @classmethod
    def load(cls, path: Path) -> "AppConfig":
        """Load config from *path*, creating defaults if missing or corrupt."""
        if not path.exists():
            config = cls()
            config.save(path)
            return config
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return cls()
        valid = {f.name for f in fields(cls)}
        clean = {k: v for k, v in raw.items() if k in valid}
        return cls(**clean)

    def save(self, path: Path) -> None:
        """Persist the current configuration as pretty JSON."""
        path.write_text(json.dumps(asdict(self), indent=2), encoding="utf-8")

    def update(self, **kwargs: object) -> None:
        """Update fields in place (keeps references held by workers valid)."""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
