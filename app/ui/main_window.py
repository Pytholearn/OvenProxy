"""The application shell: sidebar + stacked pages with all wiring."""

from __future__ import annotations

import logging
from datetime import datetime

from PyQt6.QtCore import QEasingCurve, QPropertyAnimation, Qt, QTimer
from PyQt6.QtGui import QCloseEvent
from PyQt6.QtWidgets import (
    QGraphicsOpacityEffect,
    QHBoxLayout,
    QMainWindow,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from app.config import AppConfig
from app.constants import APP_NAME, APP_VERSION
from app.database.db import Database
from app.gateway.gateway_service import GatewayService
from app.models.proxy import Proxy
from app.proxy.exporter import ProxyExporter
from app.services.traffic_monitor import TrafficMonitor
from app.services.update_service import UpdateService
from app.system.system_proxy import SystemProxyService
from app.ui.pages import (
    CheckerPage,
    DashboardPage,
    DocsPage,
    GatewayPage,
    LogsPage,
    ProxiesPage,
    ScraperPage,
    SettingsPage,
    TrafficPage,
    UpdatesPage,
)
from app.ui.sidebar import Sidebar
from app.utils.logger import LogBridge, log_success
from app.utils.paths import AppPaths
from app.widgets.update_banner import UpdateBanner

# Page indices (must match Sidebar.ITEMS order).
_PAGE_CHECKER = 2
_PAGE_GATEWAY = 5
_PAGE_UPDATES = 6


class MainWindow(QMainWindow):
    """Owns every service and page and connects their signals together."""

    def __init__(
        self,
        config: AppConfig,
        paths: AppPaths,
        db: Database,
        gateway: GatewayService,
        monitor: TrafficMonitor,
        log_bridge: LogBridge,
        logger: logging.Logger,
    ) -> None:
        super().__init__()
        self._config = config
        self._paths = paths
        self._db = db
        self._gateway = gateway
        self._monitor = monitor
        self._logger = logger
        self._anim: QPropertyAnimation | None = None

        self._system_proxy = SystemProxyService(logger)
        self._update_service = UpdateService(config, logger)

        self.setWindowTitle(f"{APP_NAME} {APP_VERSION}")
        self.resize(1180, 760)
        self.setMinimumSize(980, 660)

        root = QWidget()
        root.setObjectName("Root")
        outer = QVBoxLayout(root)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        self._banner = UpdateBanner()
        outer.addWidget(self._banner)

        body = QWidget()
        layout = QHBoxLayout(body)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self._sidebar = Sidebar()
        layout.addWidget(self._sidebar)
        self._stack = QStackedWidget()
        layout.addWidget(self._stack, 1)
        outer.addWidget(body, 1)
        self.setCentralWidget(root)

        # ---- pages (order must match Sidebar.ITEMS) ----
        self._dashboard = DashboardPage(monitor)
        self._scraper = ScraperPage(db, config)
        self._checker = CheckerPage(config)
        self._proxies = ProxiesPage(db)
        self._traffic = TrafficPage(monitor)
        self._gateway_page = GatewayPage(gateway, config, self._system_proxy)
        self._updates = UpdatesPage(self._update_service.current_version)
        self._settings = SettingsPage(config)
        self._logs = LogsPage()
        self._docs = DocsPage()
        for page in (
            self._dashboard, self._scraper, self._checker, self._proxies, self._traffic,
            self._gateway_page, self._updates, self._settings, self._logs, self._docs,
        ):
            self._stack.addWidget(page)

        self._connect_signals(log_bridge)
        self._monitor.start()

        self._dashboard.set_total(0)
        self._dashboard.set_working(self._proxies._model.rowCount())
        self._dashboard.set_gateway(False)
        self.statusBar().showMessage("Ready")

        if config.check_updates_on_startup:
            QTimer.singleShot(800, self._update_service.check)

    # --------------------------------------------------------------- wiring
    def _connect_signals(self, log_bridge: LogBridge) -> None:
        self._sidebar.navigate.connect(self._navigate)

        self._scraper.scraped.connect(self._on_scraped)
        self._scraper.message.connect(self._emit_log)

        self._checker.proxy_alive.connect(self._proxies.add_proxy)
        self._checker.checking_finished.connect(self._on_check_finished)
        self._checker.message.connect(self._emit_log)

        self._proxies.use_in_gateway.connect(self._on_use_in_gateway)
        self._proxies.count_changed.connect(self._on_working_count)
        self._proxies.message.connect(self._emit_log)

        self._gateway_page.message.connect(self._emit_log)
        self._gateway.started.connect(self._on_gateway_started)
        self._gateway.stopped.connect(self._on_gateway_stopped)

        self._settings.settings_changed.connect(self._on_settings_changed)

        self._updates.check_requested.connect(self._update_service.check)
        self._updates.update_requested.connect(self._update_service.perform_update)
        self._update_service.checking.connect(self._updates.set_checking)
        self._update_service.update_available.connect(self._on_update_available)
        self._update_service.up_to_date.connect(self._updates.set_up_to_date)
        self._update_service.error.connect(self._on_update_error)
        self._update_service.updating.connect(self._updates.set_updating)
        self._update_service.update_finished.connect(self._on_update_finished)

        self._banner.update_clicked.connect(lambda: self._navigate(_PAGE_UPDATES))

        log_bridge.record.connect(self._logs.append)
        log_bridge.record.connect(self._on_status_message)

    # --------------------------------------------------------------- navigation
    def _navigate(self, index: int) -> None:
        if index == self._stack.currentIndex():
            return
        self._stack.setCurrentIndex(index)
        self._sidebar.set_active(index)
        self._fade_in(self._stack.currentWidget())

    def _fade_in(self, widget: QWidget) -> None:
        effect = QGraphicsOpacityEffect(widget)
        widget.setGraphicsEffect(effect)
        animation = QPropertyAnimation(effect, b"opacity", self)
        animation.setDuration(170)
        animation.setStartValue(0.0)
        animation.setEndValue(1.0)
        animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        animation.finished.connect(lambda: widget.setGraphicsEffect(None))
        animation.start()
        self._anim = animation

    # --------------------------------------------------------------- handlers
    def _on_scraped(self, proxies: list[Proxy]) -> None:
        self._dashboard.set_total(len(proxies))
        self._checker.set_proxies(proxies)
        self._emit_log("INFO", f"{len(proxies)} proxies queued for checking.")
        self._navigate(_PAGE_CHECKER)

    def _on_check_finished(self, alive: int, total: int) -> None:
        self._gateway_page.set_proxies(self._proxies.proxies())
        if self._config.auto_export and alive:
            self._auto_export()

    def _on_working_count(self, count: int) -> None:
        self._dashboard.set_working(count)
        self._gateway_page.set_proxies(self._proxies.proxies())

    def _on_use_in_gateway(self, proxy: Proxy) -> None:
        self._gateway_page.set_proxies(self._proxies.proxies())
        self._gateway_page.set_selected(proxy)
        self._navigate(_PAGE_GATEWAY)

    def _on_gateway_started(self, port: int) -> None:
        self._sidebar.set_gateway_status(True)
        self._dashboard.set_gateway(True, port)

    def _on_gateway_stopped(self) -> None:
        self._sidebar.set_gateway_status(False)
        self._dashboard.set_gateway(False)

    def _on_settings_changed(self) -> None:
        self._config.save(self._paths.config_file)
        self._emit_log("SUCCESS", "Settings saved.")

    def _on_update_available(self, current: str, latest: str) -> None:
        self._updates.set_available(current, latest)
        self._banner.show_update(latest)
        self._emit_log("INFO", f"Update available: v{latest} (you have v{current}).")

    def _on_update_error(self, message: str) -> None:
        self._updates.set_error(message)
        self._emit_log("WARNING", message)

    def _on_update_finished(self, success: bool, message: str) -> None:
        self._updates.set_finished(success, message)
        self._emit_log("SUCCESS" if success else "ERROR", message)

    def _on_status_message(self, level: str, message: str, _timestamp: str) -> None:
        self.statusBar().showMessage(f"[{level}] {message}", 6000)

    def _auto_export(self) -> None:
        proxies = self._proxies.proxies()
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        path = self._paths.exports_dir / f"working-{stamp}.txt"
        ProxyExporter.export(proxies, path, "txt")
        self._emit_log("INFO", f"Auto-exported {len(proxies)} proxies to {path.name}.")

    def _emit_log(self, level: str, text: str) -> None:
        level = level.upper()
        if level == "SUCCESS":
            log_success(self._logger, text)
        elif level == "WARNING":
            self._logger.warning(text)
        elif level == "ERROR":
            self._logger.error(text)
        elif level == "DEBUG":
            self._logger.debug(text)
        else:
            self._logger.info(text)

    # --------------------------------------------------------------- lifecycle
    def closeEvent(self, event: QCloseEvent) -> None:  # noqa: N802
        self._monitor.stop()
        if self._system_proxy.is_active:
            self._system_proxy.disable()
        if self._gateway.is_running:
            self._gateway.stop()
        self._logger.info("Shutting down.")
        super().closeEvent(event)
