"""Traffic monitor page with a live chart and throughput KPIs."""

from __future__ import annotations

from typing import Optional

from PyQt6.QtWidgets import QHBoxLayout, QLabel, QWidget

from app.models.statistics import GatewayStats
from app.services.traffic_monitor import TrafficMonitor
from app.ui.pages.base_page import BasePage
from app.ui.theme import COLORS
from app.utils.helpers import format_bytes, format_speed
from app.widgets.cards import Card, StatCard
from app.widgets.chart_widget import TrafficChart


class TrafficPage(BasePage):
    """Visualises gateway traffic sampled once per second."""

    def __init__(self, monitor: TrafficMonitor, parent: Optional[QWidget] = None) -> None:
        super().__init__("Traffic Monitor", "Real-time gateway throughput", parent)
        self._monitor = monitor

        cards = QHBoxLayout()
        cards.setSpacing(14)
        self._download = StatCard("Download", "0.0 B/s", "scraper", COLORS["accent"])
        self._upload = StatCard("Upload", "0.0 B/s", "export", COLORS["success"])
        self._total = StatCard("Transferred", "0.0 B", "traffic")
        self._clients = StatCard("Active Connections", "0", "gateway", COLORS["warning"])
        for card in (self._download, self._upload, self._total, self._clients):
            cards.addWidget(card)
        self.content().addLayout(cards)

        chart_card = Card()
        title = QLabel("Throughput (KB/s)")
        title.setObjectName("SectionTitle")
        chart_card.body().addWidget(title)
        self._chart = TrafficChart()
        chart_card.body().addWidget(self._chart)
        self.content().addWidget(chart_card, 1)

        monitor.sample.connect(self._on_sample)

    def _on_sample(self, stats: GatewayStats) -> None:
        self._download.set_value(format_speed(stats.download_speed))
        self._upload.set_value(format_speed(stats.upload_speed))
        self._total.set_value(format_bytes(stats.total_bytes))
        self._clients.set_value(str(stats.active_clients))
        self._chart.update_series(self._monitor.history_down, self._monitor.history_up)
