"""ProxyForge entry point."""
from __future__ import annotations

import sys

from PyQt6.QtWidgets import QApplication

from app.config import AppConfig
from app.constants import APP_NAME, ORG_NAME
from app.database.db import Database
from app.gateway.gateway_service import GatewayService
from app.scraper.sources import DEFAULT_SOURCES
from app.services.traffic_monitor import TrafficMonitor
from app.ui.main_window import MainWindow
from app.ui.theme import build_stylesheet
from app.utils.logger import setup_logging
from app.utils.paths import AppPaths


def _seed_sources(db: Database) -> None:
    """Populate the default provider list on first run."""
    if not db.get_sources():
        for source in DEFAULT_SOURCES:
            db.save_source(source)


def main() -> int:
    paths = AppPaths.resolve().ensure()
    logger, log_bridge = setup_logging(paths.logs_dir)
    config = AppConfig.load(paths.config_file)

    db = Database(paths.database_file)
    _seed_sources(db)

    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setOrganizationName(ORG_NAME)
    app.setStyleSheet(build_stylesheet())

    gateway = GatewayService(logger)
    monitor = TrafficMonitor(gateway)

    window = MainWindow(config, paths, db, gateway, monitor, log_bridge, logger)
    window.show()
    logger.info("%s started.", APP_NAME)

    exit_code = app.exec()
    db.close()
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
