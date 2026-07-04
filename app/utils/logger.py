"""Logging setup and a Qt bridge that turns log records into signals."""

from __future__ import annotations

import logging
from datetime import datetime
from logging.handlers import RotatingFileHandler
from pathlib import Path

from PyQt6.QtCore import QObject, pyqtSignal

SUCCESS_LEVEL: int = 25
logging.addLevelName(SUCCESS_LEVEL, "SUCCESS")

LOGGER_NAME: str = "ovenproxy"


class LogBridge(QObject):
    """Thread-safe bridge emitting a Qt signal for each log record."""

    record = pyqtSignal(str, str, str)  # level, message, HH:MM:SS


class QtLogHandler(logging.Handler):
    """A logging handler that forwards records to a :class:`LogBridge`."""

    def __init__(self, bridge: LogBridge) -> None:
        super().__init__()
        self._bridge = bridge

    def emit(self, record: logging.LogRecord) -> None:
        try:
            message = self.format(record)
            timestamp = datetime.fromtimestamp(record.created).strftime("%H:%M:%S")
            self._bridge.record.emit(record.levelname, message, timestamp)
        except Exception:  # noqa: BLE001 - logging must never raise
            self.handleError(record)


def setup_logging(logs_dir: Path) -> tuple[logging.Logger, LogBridge]:
    """Configure the application logger with file + Qt handlers."""
    logger = logging.getLogger(LOGGER_NAME)
    logger.setLevel(logging.DEBUG)
    logger.handlers.clear()
    logger.propagate = False

    file_handler = RotatingFileHandler(
        logs_dir / "ovenproxy.log", maxBytes=1_000_000, backupCount=3, encoding="utf-8"
    )
    file_handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
    file_handler.setLevel(logging.DEBUG)
    logger.addHandler(file_handler)

    bridge = LogBridge()
    qt_handler = QtLogHandler(bridge)
    qt_handler.setFormatter(logging.Formatter("%(message)s"))
    qt_handler.setLevel(logging.INFO)
    logger.addHandler(qt_handler)

    return logger, bridge


def log_success(logger: logging.Logger, message: str, *args: object) -> None:
    """Emit a message at the custom SUCCESS level."""
    logger.log(SUCCESS_LEVEL, message, *args)
