"""Samples the gateway counters once per second to compute live speeds."""

from __future__ import annotations

from collections import deque
from typing import Optional

from PyQt6.QtCore import QObject, QTimer, pyqtSignal

from app.gateway.gateway_service import GatewayService


class TrafficMonitor(QObject):
    """Emits a per-second :class:`GatewayStats` sample with computed speeds."""

    sample = pyqtSignal(object)  # GatewayStats

    HISTORY = 120  # seconds of rolling history

    def __init__(self, gateway: GatewayService, parent: Optional[QObject] = None) -> None:
        super().__init__(parent)
        self._gateway = gateway
        self._timer = QTimer(self)
        self._timer.setInterval(1000)
        self._timer.timeout.connect(self._tick)
        self._last_up = 0
        self._last_down = 0
        self.history_up: deque[float] = deque([0.0] * self.HISTORY, maxlen=self.HISTORY)
        self.history_down: deque[float] = deque([0.0] * self.HISTORY, maxlen=self.HISTORY)

    def start(self) -> None:
        self._timer.start()

    def stop(self) -> None:
        self._timer.stop()

    def reset(self) -> None:
        self._last_up = 0
        self._last_down = 0
        self.history_up.clear()
        self.history_down.clear()
        self.history_up.extend([0.0] * self.HISTORY)
        self.history_down.extend([0.0] * self.HISTORY)

    def _tick(self) -> None:
        stats = self._gateway.stats()
        up_speed = max(0, stats.upload_bytes - self._last_up)
        down_speed = max(0, stats.download_bytes - self._last_down)
        self._last_up = stats.upload_bytes
        self._last_down = stats.download_bytes
        stats.upload_speed = float(up_speed)
        stats.download_speed = float(down_speed)
        self.history_up.append(float(up_speed))
        self.history_down.append(float(down_speed))
        self.sample.emit(stats)
