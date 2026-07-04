"""Self-update support built on the user's ``autoupgrader`` library.

The version comparison is delegated to ``autoupgrader`` (which checks a remote
``version`` file on GitHub), with a pure-Python fallback when the library is not
installed. All network/git work happens on worker threads so the GUI stays live.
"""

from __future__ import annotations

import logging
from types import ModuleType
from typing import Optional

import requests
from PyQt6.QtCore import QObject, QThread, pyqtSignal

from app.config import AppConfig
from app.constants import APP_VERSION
from app.utils.logger import LOGGER_NAME


def _configure(config: AppConfig, current: str) -> ModuleType:
    """Import and configure ``autoupgrader`` for this project."""
    import autoupgrader

    autoupgrader.set_url(config.update_version_url)
    autoupgrader.set_current_version(current)
    autoupgrader.set_download_link(config.update_repo_url)
    return autoupgrader


def _version_tuple(version: str) -> tuple[int, ...]:
    parts: list[int] = []
    for chunk in version.strip().lstrip("vV").split("."):
        try:
            parts.append(int(chunk))
        except ValueError:
            parts.append(0)
    return tuple(parts)


class _CheckWorker(QThread):
    available = pyqtSignal(str, str)  # current, latest
    up_to_date = pyqtSignal(str)      # current
    failed = pyqtSignal(str)

    def __init__(self, config: AppConfig, current: str, parent: Optional[QObject] = None) -> None:
        super().__init__(parent)
        self._config = config
        self._current = current

    def run(self) -> None:
        try:
            response = requests.get(self._config.update_version_url, timeout=10)
            response.raise_for_status()
            body = response.text.strip()
            latest = body.splitlines()[0].strip() if body else self._current
        except requests.RequestException as exc:
            self.failed.emit(f"Could not reach update server: {exc}")
            return

        try:
            upgrader = _configure(self._config, self._current)
            is_current = bool(upgrader.is_up_to_date())
        except ImportError:
            is_current = _version_tuple(latest) <= _version_tuple(self._current)
        except Exception as exc:  # noqa: BLE001
            self.failed.emit(f"Update check failed: {exc}")
            return

        if is_current:
            self.up_to_date.emit(self._current)
        else:
            self.available.emit(self._current, latest)


class _UpdateWorker(QThread):
    done = pyqtSignal(bool, str)  # success, message

    def __init__(self, config: AppConfig, current: str, parent: Optional[QObject] = None) -> None:
        super().__init__(parent)
        self._config = config
        self._current = current

    def run(self) -> None:
        try:
            upgrader = _configure(self._config, self._current)
            upgrader.update()
            self.done.emit(True, "Update downloaded. Please restart OvenProxy to apply it.")
        except ImportError:
            self.done.emit(False, "The 'autoupgrader' package is not installed (pip install autoupgrader).")
        except Exception as exc:  # noqa: BLE001
            self.done.emit(False, f"Update failed: {exc}")


class UpdateService(QObject):
    """Coordinates update checks and upgrades via Qt signals."""

    checking = pyqtSignal()
    update_available = pyqtSignal(str, str)  # current, latest
    up_to_date = pyqtSignal(str)
    error = pyqtSignal(str)
    updating = pyqtSignal()
    update_finished = pyqtSignal(bool, str)

    def __init__(
        self, config: AppConfig, logger: Optional[logging.Logger] = None,
        parent: Optional[QObject] = None,
    ) -> None:
        super().__init__(parent)
        self._config = config
        self._log = logger or logging.getLogger(LOGGER_NAME)
        self._current = APP_VERSION
        self._check_worker: Optional[_CheckWorker] = None
        self._update_worker: Optional[_UpdateWorker] = None

    @property
    def current_version(self) -> str:
        return self._current

    def check(self) -> None:
        if self._check_worker is not None and self._check_worker.isRunning():
            return
        self.checking.emit()
        worker = _CheckWorker(self._config, self._current)
        worker.available.connect(self.update_available.emit)
        worker.up_to_date.connect(self.up_to_date.emit)
        worker.failed.connect(self.error.emit)
        self._check_worker = worker
        worker.start()

    def perform_update(self) -> None:
        if self._update_worker is not None and self._update_worker.isRunning():
            return
        self.updating.emit()
        worker = _UpdateWorker(self._config, self._current)
        worker.done.connect(self.update_finished.emit)
        self._update_worker = worker
        worker.start()
