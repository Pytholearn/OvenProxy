"""QThread wrapper around :class:`ProxyChecker`."""

from __future__ import annotations

import time
from typing import Optional

from PyQt6.QtCore import QThread, pyqtSignal

from app.checker.checker import ProxyChecker
from app.config import AppConfig
from app.models.proxy import Proxy, ProxyStatus
from app.models.statistics import CheckProgress
from app.utils.network import get_public_ip


class CheckerWorker(QThread):
    """Validates a list of proxies off the GUI thread."""

    progress = pyqtSignal(object)          # CheckProgress
    proxy_checked = pyqtSignal(object)     # Proxy (alive or dead)
    finished_checking = pyqtSignal(int, int)  # alive count, total
    message = pyqtSignal(str, str)         # level, text

    def __init__(
        self, proxies: list[Proxy], config: AppConfig, parent: Optional[object] = None
    ) -> None:
        super().__init__(parent)
        self._proxies = proxies
        self._config = config
        self._checker: Optional[ProxyChecker] = None

    def stop(self) -> None:
        if self._checker is not None:
            self._checker.stop()

    def run(self) -> None:
        total = len(self._proxies)
        if total == 0:
            self.finished_checking.emit(0, 0)
            return

        self.message.emit("INFO", "Resolving public IP for anonymity detection...")
        real_ip = get_public_ip() or ""

        checker = ProxyChecker(
            check_url=self._config.check_url,
            timeout=self._config.timeout,
            retries=self._config.retries,
            real_ip=real_ip,
        )
        self._checker = checker

        progress = CheckProgress(total=total)
        start = time.perf_counter()

        def on_result(proxy: Proxy) -> None:
            progress.checked += 1
            if proxy.status == ProxyStatus.ALIVE:
                progress.alive += 1
            else:
                progress.dead += 1
            progress.elapsed = time.perf_counter() - start
            progress.speed = progress.checked / progress.elapsed if progress.elapsed > 0 else 0.0
            self.proxy_checked.emit(proxy)
            self.progress.emit(progress)

        self.message.emit(
            "INFO", f"Checking {total} proxies with {self._config.threads} threads..."
        )
        checker.check_many(self._proxies, self._config.threads, on_result)
        self.message.emit("SUCCESS", f"Done. {progress.alive}/{total} proxies alive.")
        self.finished_checking.emit(progress.alive, total)
