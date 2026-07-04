"""Qt-facing service that runs the SOCKS5 forwarder in its own loop thread."""

from __future__ import annotations

import asyncio
import logging
import threading
import time
from typing import Optional

from PyQt6.QtCore import QObject, pyqtSignal

from app.gateway.socks5 import Socks5Forwarder
from app.models.proxy import Proxy
from app.models.statistics import GatewayStats
from app.utils.logger import LOGGER_NAME


class GatewayService(QObject):
    """Starts/stops the gateway and exposes a thread-safe stats snapshot."""

    started = pyqtSignal(int)         # local port
    stopped = pyqtSignal()
    error = pyqtSignal(str)
    status_changed = pyqtSignal(bool)

    def __init__(
        self, logger: Optional[logging.Logger] = None, parent: Optional[QObject] = None
    ) -> None:
        super().__init__(parent)
        self._log = logger or logging.getLogger(LOGGER_NAME)
        self._thread: Optional[threading.Thread] = None
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._forwarder: Optional[Socks5Forwarder] = None
        self._running = False
        self._start_time = 0.0
        self._upstream: Optional[Proxy] = None

    @property
    def is_running(self) -> bool:
        return self._running

    @property
    def upstream(self) -> Optional[Proxy]:
        return self._upstream

    def start(
        self,
        upstream: Proxy,
        local_port: int,
        local_host: str = "127.0.0.1",
        timeout: float = 15.0,
    ) -> None:
        if self._running:
            self.error.emit("Gateway is already running.")
            return
        self._upstream = upstream
        self._thread = threading.Thread(
            target=self._run_loop,
            args=(upstream, local_host, local_port, timeout),
            name="GatewayLoop",
            daemon=True,
        )
        self._thread.start()

    def _run_loop(self, upstream: Proxy, host: str, port: int, timeout: float) -> None:
        loop = asyncio.new_event_loop()
        self._loop = loop
        asyncio.set_event_loop(loop)
        forwarder = Socks5Forwarder(
            host, port, upstream.ip, upstream.port, timeout, self._log, upstream.protocol
        )
        self._forwarder = forwarder
        try:
            loop.run_until_complete(forwarder.start())
        except OSError as exc:
            self._log.error("Gateway bind failed on port %d: %s", port, exc)
            self.error.emit(f"Could not bind 127.0.0.1:{port} — {exc}")
            loop.close()
            self._loop = None
            self._forwarder = None
            return

        self._running = True
        self._start_time = time.time()
        self.started.emit(port)
        self.status_changed.emit(True)
        try:
            loop.run_until_complete(forwarder.serve_forever())
        except asyncio.CancelledError:
            pass
        except Exception as exc:  # noqa: BLE001
            self._log.error("Gateway loop crashed: %s", exc)
        finally:
            forwarder.close()
            try:
                loop.run_until_complete(asyncio.sleep(0))
            except RuntimeError:
                pass
            loop.close()
            self._running = False
            self._loop = None
            self._forwarder = None
            self.status_changed.emit(False)
            self.stopped.emit()
            self._log.info("Gateway stopped.")

    def stop(self) -> None:
        if not self._running or self._loop is None or self._forwarder is None:
            return
        loop = self._loop

        def _shutdown() -> None:
            if self._forwarder is not None:
                self._forwarder.close()
            for task in asyncio.all_tasks(loop):
                task.cancel()

        loop.call_soon_threadsafe(_shutdown)

    def stats(self) -> GatewayStats:
        counters = self._forwarder.counters if self._forwarder else None
        if not self._running or counters is None:
            return GatewayStats(running=False)
        latency = self._upstream.latency_ms if self._upstream and self._upstream.latency_ms else 0.0
        return GatewayStats(
            running=True,
            active_clients=counters.active,
            upload_bytes=counters.upload,
            download_bytes=counters.download,
            latency_ms=float(latency),
            session_seconds=time.time() - self._start_time,
        )
