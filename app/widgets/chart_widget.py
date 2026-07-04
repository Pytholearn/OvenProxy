"""Real-time upload/download chart built on pyqtgraph."""

from __future__ import annotations

from typing import Optional, Sequence

import pyqtgraph as pg
from PyQt6.QtWidgets import QVBoxLayout, QWidget

from app.ui.theme import COLORS


class TrafficChart(QWidget):
    """Two filled curves (download + upload) over a rolling time window."""

    def __init__(self, points: int = 120, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._points = points

        pg.setConfigOptions(antialias=True)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self._plot = pg.PlotWidget()
        self._plot.setBackground(COLORS["surface"])
        self._plot.showGrid(x=False, y=True, alpha=0.15)
        self._plot.setMenuEnabled(False)
        self._plot.setMouseEnabled(x=False, y=False)
        self._plot.hideButtons()
        self._plot.getAxis("left").setTextPen(COLORS["text_muted"])
        self._plot.getAxis("bottom").setTextPen(COLORS["text_muted"])
        self._plot.setLabel("left", "KB/s")
        layout.addWidget(self._plot)

        self._x = list(range(points))
        self._down = [0.0] * points
        self._up = [0.0] * points

        down_pen = pg.mkPen(COLORS["accent"], width=2)
        up_pen = pg.mkPen(COLORS["success"], width=2)
        self._down_curve = self._plot.plot(
            self._x, self._down, pen=down_pen,
            fillLevel=0, brush=pg.mkBrush(76, 194, 255, 50), name="Download",
        )
        self._up_curve = self._plot.plot(
            self._x, self._up, pen=up_pen,
            fillLevel=0, brush=pg.mkBrush(58, 210, 159, 45), name="Upload",
        )

    def update_series(self, down: Sequence[float], up: Sequence[float]) -> None:
        """Replace the plotted data; values are bytes/s and shown as KB/s."""
        self._down = [v / 1024.0 for v in list(down)[-self._points:]]
        self._up = [v / 1024.0 for v in list(up)[-self._points:]]
        x = list(range(len(self._down)))
        self._down_curve.setData(x, self._down)
        self._up_curve.setData(x[: len(self._up)], self._up)

    def reset(self) -> None:
        zeros = [0.0] * self._points
        self.update_series(zeros, zeros)
