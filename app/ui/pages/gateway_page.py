"""Local gateway page: upstream selection, LAN/mobile mode and system proxy."""

from __future__ import annotations

from typing import Optional

from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSpinBox,
    QWidget,
)

from app.config import AppConfig
from app.gateway.gateway_service import GatewayService
from app.models.proxy import Proxy
from app.resources.icons import make_icon
from app.system.system_proxy import SystemProxyService
from app.ui.pages.base_page import BasePage
from app.ui.theme import COLORS
from app.utils.helpers import format_bytes, format_duration, format_speed
from app.utils.network import get_lan_ip
from app.widgets.cards import Card


class GatewayPage(BasePage):
    """Starts/stops a local SOCKS5 gateway chained to a chosen upstream."""

    message = pyqtSignal(str, str)

    def __init__(
        self,
        gateway: GatewayService,
        config: AppConfig,
        system_proxy: SystemProxyService,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__("Local Gateway", "Forward local, system or phone traffic through one proxy", parent)
        self._gateway = gateway
        self._config = config
        self._system_proxy = system_proxy

        config_card = Card()
        row = QHBoxLayout()
        row.setSpacing(12)
        row.addWidget(QLabel("Upstream:"))
        self._upstream = QComboBox()
        self._upstream.setMinimumWidth(280)
        row.addWidget(self._upstream, 1)
        row.addWidget(QLabel("Local port:"))
        self._port = QSpinBox()
        self._port.setRange(1, 65535)
        self._port.setValue(config.gateway_port)
        self._port.setFixedWidth(100)
        row.addWidget(self._port)

        self._start_btn = QPushButton("  Start")
        self._start_btn.setObjectName("Primary")
        self._start_btn.setIcon(make_icon("play", "#06222f"))
        self._start_btn.clicked.connect(self._start)
        self._stop_btn = QPushButton("  Stop")
        self._stop_btn.setObjectName("Danger")
        self._stop_btn.setIcon(make_icon("stop", COLORS["error"]))
        self._stop_btn.clicked.connect(self._gateway.stop)
        self._stop_btn.setEnabled(False)
        row.addWidget(self._start_btn)
        row.addWidget(self._stop_btn)
        config_card.body().addLayout(row)

        options = QHBoxLayout()
        options.setSpacing(20)
        self._lan_check = QCheckBox("Allow LAN / mobile connections")
        self._lan_check.setIcon(make_icon("phone", COLORS["text_muted"]))
        self._lan_check.setToolTip("Bind to all interfaces so a phone on the same Wi-Fi can connect")
        options.addWidget(self._lan_check)

        self._sysproxy_check = QCheckBox("Set as Windows system proxy")
        self._sysproxy_check.setIcon(make_icon("globe", COLORS["text_muted"]))
        if not system_proxy.is_supported:
            self._sysproxy_check.setEnabled(False)
            self._sysproxy_check.setToolTip("Only available on Windows")
        else:
            self._sysproxy_check.setToolTip("Route ALL system traffic through this gateway")
        options.addWidget(self._sysproxy_check)
        options.addStretch(1)
        config_card.body().addLayout(options)

        self._status = QLabel("●  Offline")
        self._status.setStyleSheet(f"color: {COLORS['text_muted']};")
        config_card.body().addWidget(self._status)

        self._mobile_info = QLabel("")
        self._mobile_info.setWordWrap(True)
        self._mobile_info.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self._mobile_info.setStyleSheet(f"color: {COLORS['text_muted']};")
        self._mobile_info.hide()
        config_card.body().addWidget(self._mobile_info)
        self.content().addWidget(config_card)

        stats_card = Card()
        grid = QGridLayout()
        grid.setHorizontalSpacing(28)
        grid.setVerticalSpacing(10)
        self._labels: dict[str, QLabel] = {}
        metrics = [
            ("Connected Clients", "clients"),
            ("Upload", "upload"),
            ("Download", "download"),
            ("Total Traffic", "total"),
            ("Latency", "latency"),
            ("Session", "session"),
        ]
        for index, (caption, key) in enumerate(metrics):
            column = index % 3
            base_row = (index // 3) * 2
            title = QLabel(caption)
            title.setObjectName("CardTitle")
            value = QLabel("—")
            value.setObjectName("StatValue")
            self._labels[key] = value
            grid.addWidget(title, base_row, column)
            grid.addWidget(value, base_row + 1, column)
        stats_card.body().addLayout(grid)
        self.content().addWidget(stats_card, 1)

        self._timer = QTimer(self)
        self._timer.setInterval(1000)
        self._timer.timeout.connect(self._refresh_stats)

        gateway.started.connect(self._on_started)
        gateway.stopped.connect(self._on_stopped)
        gateway.error.connect(self._on_error)

    # ------------------------------------------------------------------- public
    def set_proxies(self, proxies: list[Proxy]) -> None:
        current = self._upstream.currentData()
        self._upstream.clear()
        for proxy in proxies:
            self._upstream.addItem(self._label_for(proxy), proxy)
        if current is not None:
            self.set_selected(current)

    def set_selected(self, proxy: Proxy) -> None:
        for index in range(self._upstream.count()):
            data: Proxy = self._upstream.itemData(index)
            if data is not None and data.address == proxy.address:
                self._upstream.setCurrentIndex(index)
                return
        self._upstream.addItem(self._label_for(proxy), proxy)
        self._upstream.setCurrentIndex(self._upstream.count() - 1)

    # ------------------------------------------------------------------ private
    @staticmethod
    def _label_for(proxy: Proxy) -> str:
        ping = f"{proxy.latency_ms:.0f} ms" if proxy.latency_ms is not None else "—"
        return f"{proxy.address}  ·  {proxy.country_code or '??'}  ·  {ping}"

    def _start(self) -> None:
        proxy: Optional[Proxy] = self._upstream.currentData()
        if proxy is None:
            self.message.emit("WARNING", "No upstream proxy selected.")
            return
        host = "0.0.0.0" if self._lan_check.isChecked() else "127.0.0.1"
        self._gateway.start(proxy, self._port.value(), local_host=host, timeout=self._config.timeout + 5.0)

    def _on_started(self, port: int) -> None:
        self._set_running(True)
        if self._lan_check.isChecked():
            lan_ip = get_lan_ip()
            self._status.setText(f"●  Online — LAN {lan_ip}:{port}")
            self._mobile_info.setText(
                f"📱 On your phone (same Wi-Fi), set a manual SOCKS proxy to "
                f"socks5://{lan_ip}:{port}   ·   Allow OvenProxy through the firewall if it doesn't connect."
            )
            self._mobile_info.show()
        else:
            self._status.setText(f"●  Online — listening on 127.0.0.1:{port}")
            self._mobile_info.hide()
        self._status.setStyleSheet(f"color: {COLORS['success']};")

        if self._sysproxy_check.isChecked() and self._system_proxy.is_supported:
            if self._system_proxy.enable("127.0.0.1", port):
                self.message.emit("SUCCESS", "System proxy enabled — all traffic now routes through the gateway.")
            else:
                self.message.emit("ERROR", "Could not set the system proxy.")

        self._timer.start()
        self.message.emit("SUCCESS", f"Gateway online on port {port}.")

    def _on_stopped(self) -> None:
        if self._system_proxy.is_active:
            self._system_proxy.disable()
            self.message.emit("INFO", "System proxy restored.")
        self._set_running(False)
        self._status.setText("●  Offline")
        self._status.setStyleSheet(f"color: {COLORS['text_muted']};")
        self._mobile_info.hide()
        self._timer.stop()

    def _on_error(self, text: str) -> None:
        self.message.emit("ERROR", text)
        self._on_stopped()

    def _set_running(self, running: bool) -> None:
        self._start_btn.setEnabled(not running)
        self._stop_btn.setEnabled(running)
        self._port.setEnabled(not running)
        self._upstream.setEnabled(not running)
        self._lan_check.setEnabled(not running)
        self._sysproxy_check.setEnabled(not running and self._system_proxy.is_supported)

    def _refresh_stats(self) -> None:
        stats = self._gateway.stats()
        self._labels["clients"].setText(str(stats.active_clients))
        self._labels["upload"].setText(format_speed(stats.upload_speed))
        self._labels["download"].setText(format_speed(stats.download_speed))
        self._labels["total"].setText(format_bytes(stats.total_bytes))
        self._labels["latency"].setText(f"{stats.latency_ms:.0f} ms" if stats.latency_ms else "—")
        self._labels["session"].setText(format_duration(stats.session_seconds))
