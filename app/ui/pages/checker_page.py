"""Checker page: validate scraped proxies and surface live statistics."""

from __future__ import annotations

from typing import Optional

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import (
    QFileDialog,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QPushButton,
    QWidget,
)

from app.config import AppConfig
from app.models.proxy import Proxy, ProxyStatus
from app.models.statistics import CheckProgress
from app.proxy.exporter import ProxyImporter
from app.resources.icons import make_icon
from app.services.checker_worker import CheckerWorker
from app.ui.pages.base_page import BasePage
from app.ui.theme import COLORS
from app.widgets.cards import Card


class CheckerPage(BasePage):
    """Runs the checker and emits every alive proxy to the working list."""

    proxy_alive = pyqtSignal(object)        # Proxy
    checking_finished = pyqtSignal(int, int)  # alive, total
    message = pyqtSignal(str, str)

    def __init__(self, config: AppConfig, parent: Optional[QWidget] = None) -> None:
        super().__init__("Checker", "Validate proxies and measure latency", parent)
        self._config = config
        self._queue: list[Proxy] = []
        self._worker: Optional[CheckerWorker] = None

        controls_card = Card()
        controls = QHBoxLayout()
        self._start_btn = QPushButton("  Start Check")
        self._start_btn.setObjectName("Primary")
        self._start_btn.setIcon(make_icon("play", "#06222f"))
        self._start_btn.clicked.connect(self._start)
        self._start_btn.setEnabled(False)
        self._stop_btn = QPushButton("  Stop")
        self._stop_btn.setObjectName("Danger")
        self._stop_btn.setIcon(make_icon("stop", COLORS["error"]))
        self._stop_btn.clicked.connect(self._stop)
        self._stop_btn.setEnabled(False)
        load_btn = QPushButton("  Load from file")
        load_btn.setIcon(make_icon("import", COLORS["text_muted"]))
        load_btn.clicked.connect(self._load_file)
        controls.addWidget(self._start_btn)
        controls.addWidget(self._stop_btn)
        controls.addWidget(load_btn)
        controls.addStretch(1)
        self._queue_label = QLabel("Queue: 0")
        self._queue_label.setObjectName("SectionTitle")
        controls.addWidget(self._queue_label)
        controls_card.body().addLayout(controls)

        self._progress = QProgressBar()
        self._progress.setValue(0)
        controls_card.body().addWidget(self._progress)
        self.content().addWidget(controls_card)

        stats_card = Card()
        grid = QGridLayout()
        grid.setHorizontalSpacing(28)
        grid.setVerticalSpacing(10)
        self._stat_labels: dict[str, QLabel] = {}
        metrics = [
            ("Checked", "checked"),
            ("Alive", "alive"),
            ("Dead", "dead"),
            ("Remaining", "remaining"),
            ("Speed", "speed"),
            ("Elapsed", "elapsed"),
        ]
        for index, (caption, key) in enumerate(metrics):
            column = index % 3
            row = (index // 3) * 2
            title = QLabel(caption)
            title.setObjectName("CardTitle")
            value = QLabel("0")
            value.setObjectName("StatValue")
            self._stat_labels[key] = value
            grid.addWidget(title, row, column)
            grid.addWidget(value, row + 1, column)
        stats_card.body().addLayout(grid)
        self.content().addWidget(stats_card, 1)

    # ------------------------------------------------------------------- public
    def set_proxies(self, proxies: list[Proxy]) -> None:
        self._queue = list(proxies)
        self._queue_label.setText(f"Queue: {len(self._queue)}")
        self._start_btn.setEnabled(bool(self._queue))
        self._reset_stats()

    # ------------------------------------------------------------------ private
    def _load_file(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "Load proxies", "", "Proxy files (*.txt *.json *.csv);;All files (*)"
        )
        if not path:
            return
        proxies = ProxyImporter.import_file(path)
        self.set_proxies(proxies)
        self.message.emit("INFO", f"Loaded {len(proxies)} proxies from file.")

    def _start(self) -> None:
        if not self._queue:
            return
        self._reset_stats()
        self._start_btn.setEnabled(False)
        self._stop_btn.setEnabled(True)
        self._worker = CheckerWorker(self._queue, self._config)
        self._worker.progress.connect(self._on_progress)
        self._worker.proxy_checked.connect(self._on_proxy_checked)
        self._worker.message.connect(self.message.emit)
        self._worker.finished_checking.connect(self._on_finished)
        self._worker.start()

    def _stop(self) -> None:
        if self._worker is not None:
            self._worker.stop()
            self.message.emit("WARNING", "Stopping checker...")

    def _on_progress(self, progress: CheckProgress) -> None:
        self._progress.setValue(progress.percent)
        self._stat_labels["checked"].setText(str(progress.checked))
        self._stat_labels["alive"].setText(str(progress.alive))
        self._stat_labels["dead"].setText(str(progress.dead))
        self._stat_labels["remaining"].setText(str(progress.remaining))
        self._stat_labels["speed"].setText(f"{progress.speed:.0f}/s")
        self._stat_labels["elapsed"].setText(f"{progress.elapsed:.0f}s")
        self._stat_labels["alive"].setStyleSheet(f"color: {COLORS['success']};")
        self._stat_labels["dead"].setStyleSheet(f"color: {COLORS['error']};")

    def _on_proxy_checked(self, proxy: Proxy) -> None:
        if proxy.status == ProxyStatus.ALIVE:
            self.proxy_alive.emit(proxy)

    def _on_finished(self, alive: int, total: int) -> None:
        self._start_btn.setEnabled(bool(self._queue))
        self._stop_btn.setEnabled(False)
        self.checking_finished.emit(alive, total)

    def _reset_stats(self) -> None:
        self._progress.setValue(0)
        for key, label in self._stat_labels.items():
            label.setText("0")
        self._queue_label.setText(f"Queue: {len(self._queue)}")
