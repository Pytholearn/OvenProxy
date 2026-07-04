"""Landing page with KPI tiles and a live throughput chart."""

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


class DashboardPage(BasePage):
    """Aggregated overview of scraping, checking and gateway activity."""

    def __init__(self, monitor: TrafficMonitor, parent: Optional[QWidget] = None) -> None:
        super().__init__("Dashboard", "Overview of your proxy operations", parent)
        self._monitor = monitor

        cards = QHBoxLayout()
        cards.setSpacing(14)
        self._total = StatCard("Total Scraped", "0", "scraper")
        self._working = StatCard("Working Proxies", "0", "checker", COLORS["success"])
        self._gateway = StatCard("Gateway", "Offline", "gateway", COLORS["warning"])
        self._traffic = StatCard("Total Traffic", "0.0 B", "traffic")
        for card in (self._total, self._working, self._gateway, self._traffic):
            cards.addWidget(card)
        self.content().addLayout(cards)

        chart_card = Card()
        title = QLabel("Live Throughput")
        title.setObjectName("SectionTitle")
        chart_card.body().addWidget(title)
        self._chart = TrafficChart()
        chart_card.body().addWidget(self._chart)
        self.content().addWidget(chart_card, 1)

        monitor.sample.connect(self._on_sample)

    def set_total(self, value: int) -> None:
        self._total.set_value(str(value))

    def set_working(self, value: int) -> None:
        self._working.set_value(str(value))

    def set_gateway(self, running: bool, port: int = 0) -> None:
        self._gateway.set_value("Online" if running else "Offline")
        self._gateway.set_value_color(COLORS["success"] if running else COLORS["text"])
        self._gateway.set_caption(f"127.0.0.1:{port}" if running else "Not running")

    def _on_sample(self, stats: GatewayStats) -> None:
        self._traffic.set_value(format_bytes(stats.total_bytes))
        self._traffic.set_caption(
            f"↓ {format_speed(stats.download_speed)}   ↑ {format_speed(stats.upload_speed)}"
        )
        self._chart.update_series(self._monitor.history_down, self._monitor.history_up)
