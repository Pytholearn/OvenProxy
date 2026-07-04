"""QThread wrapper around :class:`ProxyScraper`."""

from __future__ import annotations

from typing import Optional

from PyQt6.QtCore import QThread, pyqtSignal

from app.config import AppConfig
from app.models.source import ProxySource
from app.scraper.scraper import ProxyScraper


class ScraperWorker(QThread):
    """Runs a scrape off the GUI thread and reports results via signals."""

    source_done = pyqtSignal(str, int)      # source name, proxies found
    finished_scraping = pyqtSignal(object)  # list[Proxy]
    message = pyqtSignal(str, str)          # level, text

    def __init__(
        self, sources: list[ProxySource], config: AppConfig, parent: Optional[object] = None
    ) -> None:
        super().__init__(parent)
        self._sources = sources
        self._config = config
        self._scraper: Optional[ProxyScraper] = None

    def stop(self) -> None:
        if self._scraper is not None:
            self._scraper.stop()

    def run(self) -> None:
        scraper = ProxyScraper(timeout=self._config.timeout + 5.0)
        self._scraper = scraper
        self.message.emit("INFO", "Scraping sources...")
        proxies = scraper.scrape(
            self._sources, on_source=lambda name, count: self.source_done.emit(name, count)
        )
        if self._config.max_proxies > 0:
            proxies = proxies[: self._config.max_proxies]
        self.message.emit("SUCCESS", f"Scraped {len(proxies)} unique proxies.")
        self.finished_scraping.emit(proxies)
