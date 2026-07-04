"""Concurrent proxy checker (SOCKS5 / SOCKS4 / HTTP) on a ThreadPoolExecutor."""

from __future__ import annotations

import logging
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from typing import Callable, Optional

import requests

from app.models.proxy import AnonymityLevel, Protocol, Proxy, ProxyStatus
from app.utils.logger import LOGGER_NAME

OnResult = Callable[[Proxy], None]

_HEADERS = {"User-Agent": "OvenProxy/1.0"}

# requests/PySocks scheme per protocol. ``socks5h`` resolves DNS on the proxy.
_SCHEME: dict[Protocol, str] = {
    Protocol.SOCKS5: "socks5h",
    Protocol.SOCKS4: "socks4",
    Protocol.HTTP: "http",
}


class ProxyChecker:
    """Validates proxies by routing a geolocation request through each one.

    The proxy's own protocol decides the request scheme, so SOCKS5, SOCKS4 and
    HTTP proxies are all checked correctly.
    """

    def __init__(
        self,
        check_url: str,
        timeout: float = 10.0,
        retries: int = 1,
        real_ip: str = "",
        logger: Optional[logging.Logger] = None,
    ) -> None:
        self._check_url = check_url
        self._timeout = timeout
        self._retries = max(1, retries)
        self._real_ip = real_ip
        self._log = logger or logging.getLogger(LOGGER_NAME)
        self._stop_event = threading.Event()

    def stop(self) -> None:
        self._stop_event.set()

    def reset(self) -> None:
        self._stop_event.clear()

    @property
    def stopped(self) -> bool:
        return self._stop_event.is_set()

    def check_one(self, proxy: Proxy) -> Proxy:
        """Probe a single proxy and mutate it in place with the outcome."""
        if self._stop_event.is_set():
            return proxy
        scheme = _SCHEME.get(proxy.protocol, "socks5h")
        proxy_url = f"{scheme}://{proxy.ip}:{proxy.port}"
        proxies = {"http": proxy_url, "https": proxy_url}
        last_error: Optional[Exception] = None

        for _ in range(self._retries):
            if self._stop_event.is_set():
                return proxy
            start = time.perf_counter()
            try:
                response = requests.get(
                    self._check_url, proxies=proxies, timeout=self._timeout, headers=_HEADERS
                )
                latency_ms = (time.perf_counter() - start) * 1000.0
                response.raise_for_status()
                data = response.json()
                if data.get("status") and data["status"] != "success":
                    raise ValueError("geolocation lookup failed")
                proxy.latency_ms = round(latency_ms, 1)
                proxy.exit_ip = data.get("query", "")
                proxy.country = data.get("country", "")
                proxy.country_code = data.get("countryCode", "")
                proxy.status = ProxyStatus.ALIVE
                proxy.anonymity = self._classify_anonymity(proxy.exit_ip)
                proxy.last_checked = datetime.now()
                return proxy
            except (requests.RequestException, ValueError) as exc:
                last_error = exc
                continue

        proxy.status = ProxyStatus.DEAD
        proxy.latency_ms = None
        proxy.last_checked = datetime.now()
        if last_error is not None:
            self._log.debug("Proxy %s dead: %s", proxy.address, last_error)
        return proxy

    def _classify_anonymity(self, exit_ip: str) -> AnonymityLevel:
        if not exit_ip:
            return AnonymityLevel.UNKNOWN
        if self._real_ip and exit_ip == self._real_ip:
            return AnonymityLevel.TRANSPARENT
        return AnonymityLevel.ANONYMOUS

    def check_many(self, proxies: list[Proxy], threads: int, on_result: OnResult) -> None:
        """Check *proxies* concurrently, invoking *on_result* as each completes."""
        self.reset()
        with ThreadPoolExecutor(max_workers=max(1, threads)) as pool:
            future_map = {pool.submit(self.check_one, p): p for p in proxies}
            for future in as_completed(future_map):
                if self._stop_event.is_set():
                    pool.shutdown(wait=False, cancel_futures=True)
                    break
                try:
                    on_result(future.result())
                except Exception as exc:  # noqa: BLE001 - keep the run alive
                    self._log.error("Checker error: %s", exc)
