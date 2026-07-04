"""Resolves and creates the application's data directories."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from app.constants import APP_NAME


@dataclass
class AppPaths:
    """Holds every filesystem path the application uses."""

    data_dir: Path
    logs_dir: Path
    exports_dir: Path
    config_file: Path
    database_file: Path

    @classmethod
    def resolve(cls) -> "AppPaths":
        base = os.environ.get("APPDATA") or os.environ.get("XDG_DATA_HOME")
        root = Path(base) if base else Path.home() / ".local" / "share"
        data_dir = root / APP_NAME
        return cls(
            data_dir=data_dir,
            logs_dir=data_dir / "logs",
            exports_dir=data_dir / "exports",
            config_file=data_dir / "config.json",
            database_file=data_dir / "ovenproxy.db",
        )

    def ensure(self) -> "AppPaths":
        """Create all directories if they do not exist."""
        for directory in (self.data_dir, self.logs_dir, self.exports_dir):
            directory.mkdir(parents=True, exist_ok=True)
        return self
